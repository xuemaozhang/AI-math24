from __future__ import annotations

import ast
import math
import operator
import os
import re
from collections import Counter
from typing import Iterable, List, Literal, Optional

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set; add it to your environment or .env file.")

genai.configure(api_key=GEMINI_API_KEY)
GEN_MODEL = genai.GenerativeModel(GEMINI_MODEL)

app = FastAPI(title="Math24 Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic models -----------------------------------------------------------------


class NumbersPayload(BaseModel):
    numbers: List[int] = Field(..., min_length=1, max_length=8, description="Numbers available to use")
    target: int = Field(default=24, description="Target value to reach")
    mode: Optional[Literal["easy", "hard"]] = Field(default=None, description="Game mode context")

    @field_validator("numbers")
    def ensure_positive(cls, v: List[int]) -> List[int]:
        if any(n <= 0 for n in v):
            raise ValueError("Numbers must be positive")
        return v


class CheckRequest(NumbersPayload):
    expression: str = Field(..., min_length=1, description="User provided arithmetic expression")


class CheckResponse(BaseModel):
    valid: bool
    value: Optional[float]
    errors: List[str]
    hints: List[str]
    normalized_expression: Optional[str]


class HintRequest(NumbersPayload):
    expression: str = Field("", description="Partial or full expression typed so far")
    solution: Optional[str] = Field(None, description="Known valid solution expression (will be partially hinted, not revealed)")


class HintResponse(BaseModel):
    hint: str
    model: str


# --- Expression utilities -------------------------------------------------------------


ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError("Only numeric constants are allowed")
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _safe_eval(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BIN_OPS:
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        if isinstance(node.op, ast.Div) and math.isclose(right, 0.0, abs_tol=1e-9):
            raise ZeroDivisionError("Division by zero")
        return ALLOWED_BIN_OPS[type(node.op)](left, right)
    raise ValueError("Unsupported expression")


def evaluate_expression(expr: str) -> float:
    parsed = ast.parse(expr, mode="eval")
    return _safe_eval(parsed.body)


def extract_numbers(expr: str) -> List[int]:
    return [int(m.group()) for m in re.finditer(r"\d+", expr)]


def extract_operators(expr: str) -> List[str]:
    return re.findall(r"[+\-*/]", expr)


def solution_first_step(expr: str) -> Optional[str]:
    """Parse a solution expression and return a small hint about its first binary op.

    We keep this light: find the left-most binary operation and surface just that op and its operands.
    If parsing fails, return None.
    """

    try:
        tree = ast.parse(expr, mode="eval")
    except Exception:
        return None

    def walk(node: ast.AST) -> Optional[ast.BinOp]:
        if isinstance(node, ast.BinOp):
            return node
        if isinstance(node, ast.UnaryOp):
            return walk(node.operand)
        if isinstance(node, ast.Expr):
            return walk(node.value)
        if isinstance(node, ast.Call):
            return None
        return None

    first = walk(tree.body) if isinstance(tree, ast.Expression) else None
    if not first:
        return None

    def operand_label(n: ast.AST) -> Optional[str]:
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return str(int(n.value))
        if isinstance(n, ast.BinOp):
            return "(sub-expression)"
        return None

    left = operand_label(first.left)
    right = operand_label(first.right)
    op_map = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}
    op_symbol = op_map.get(type(first.op))

    if not op_symbol or not left or not right:
        return None

    return f"A valid solve starts by combining {left} and {right} using {op_symbol}."


def numbers_match(available: Iterable[int], used: Iterable[int]) -> bool:
    return Counter(available) == Counter(used)


def build_hints(request: CheckRequest, value: Optional[float], errors: List[str]) -> List[str]:
    hints: List[str] = []
    if errors:
        for err in errors:
            if "numbers" in err.lower():
                hints.append("Use every provided number exactly once.")
            if "Division by zero" in err:
                hints.append("Avoid dividing by zero.")
            if "Unsupported" in err:
                hints.append("Stick to +, -, *, / and parentheses.")
        return hints or ["Adjust the expression and try again."]

    if value is None:
        return ["Provide an expression to check."]

    delta = value - request.target
    if math.isclose(delta, 0, abs_tol=1e-6):
        hints.append("Great job—this hits the target!")
    elif abs(delta) <= 3:
        hints.append("You're very close; tweak the last operator or order.")
    else:
        hints.append("Consider re-grouping with parentheses to change order of operations.")
        hints.append("Try pairing numbers to make factors of the target (e.g., 6, 8, 12).")
    return hints


def build_hint_prompt(
    request: HintRequest,
    used_numbers: List[int],
    remaining_numbers: List[int],
    parse_note: str,
    solution_step: Optional[str],
    solution_ops: List[str],
) -> str:
    numbers_str = ", ".join(str(n) for n in request.numbers)
    used_str = ", ".join(str(n) for n in used_numbers) or "none"
    remaining_str = ", ".join(str(n) for n in remaining_numbers) or "none"
    partial = request.expression.strip() or "(no expression yet)"
    mode_text = request.mode or "unspecified"

    ops_str = ", ".join(solution_ops) if solution_ops else "unknown"

    prompt = f"""
        You are an assistant for the Math 24 game.

        Rules:
        - Use every provided number exactly once
        - Allowed operations: +, -, *, /, parentheses
        - Target: {request.target}
        - Return ONE concise hint (8-20 words), a single sentence
        - Never give a complete solution or full expression using all numbers
        - Allowed: suggest one operation, a partial grouping, or a strategic idea
        - Disallowed: full expression that reaches the target; step-by-step full solution; listing all operations
        - Avoid generic phrasing like "group X and Y first"; vary tactics and be specific.
        - If a solution hint is provided, align with it but DO NOT reveal the full solution.

        Game state:
        - Numbers given: {numbers_str}
        - Numbers already used: {used_str}
        - Numbers remaining: {remaining_str}
        - Current expression (may be partial): {partial}
        - Mode: {mode_text}
        - Expression status: {parse_note}
        - Solution operators (bag): {ops_str}
        - Solution opening move: {solution_step or "not provided"}

        Respond with just the hint text. Do not reveal a complete solution.

        Good examples (format/length):
        - "Make an 8 with 2 and 4, then multiply it by the largest remaining number."
        - "Use one division to reduce a big pair, then add the smallest number to reach 24."
        - "Aim for factors of 24 (3×8, 4×6); set up one of these with your remaining numbers."
        """

    return prompt.strip()


# --- Routes ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/check", response_model=CheckResponse)
def check_expression(payload: CheckRequest) -> CheckResponse:
    errors: List[str] = []
    value: Optional[float] = None
    normalized_expr: Optional[str] = None

    try:
        parsed = ast.parse(payload.expression, mode="eval")
        normalized_expr = payload.expression.replace(" ", "")
        value = evaluate_expression(payload.expression)
    except (SyntaxError, ValueError, ZeroDivisionError) as exc:  # ValueError includes unsupported nodes
        errors.append(str(exc))
    except Exception as exc:  # pragma: no cover - unexpected parser errors
        raise HTTPException(status_code=400, detail=f"Unexpected error: {exc}") from exc

    # Validate number usage only if parsing succeeded
    if not errors:
        used_numbers = extract_numbers(payload.expression)
        if not numbers_match(payload.numbers, used_numbers):
            errors.append("Numbers used do not match the provided set (all numbers, exact counts).")

    valid = not errors and value is not None and math.isfinite(value) and math.isclose(
        value, payload.target, abs_tol=1e-6
    )
    hints = build_hints(payload, value, errors)

    return CheckResponse(
        valid=bool(valid),
        value=value,
        errors=errors,
        hints=hints,
        normalized_expression=normalized_expr,
    )


@app.post("/hint", response_model=HintResponse)
def ai_hint(payload: HintRequest) -> HintResponse:
    used_numbers = extract_numbers(payload.expression)
    remaining_counter = Counter(payload.numbers) - Counter(used_numbers)
    remaining_numbers = list(remaining_counter.elements())

    try:
        ast.parse(payload.expression or "0", mode="eval")
        parse_note = "expression parses" if payload.expression.strip() else "no expression yet"
    except Exception as exc:  # pragma: no cover - parsing diagnostic only
        parse_note = f"expression not valid yet: {exc}"  # keep short

    eval_value: Optional[float] = None
    try:
        if payload.expression.strip():
            eval_value = evaluate_expression(payload.expression)
    except Exception:
        eval_value = None

    solution_ops: List[str] = extract_operators(payload.solution) if payload.solution else []
    solution_step = solution_first_step(payload.solution) if payload.solution else None

    prompt = build_hint_prompt(payload, used_numbers, remaining_numbers, parse_note, solution_step, solution_ops)
    try:
        completion = GEN_MODEL.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 80,
                "temperature": 0.85,
                "top_p": 0.9,
            },
        )
        text = (completion.text or "Try pairing numbers into factors of the target.").strip()
    except Exception as exc:  # pragma: no cover - upstream errors
        raise HTTPException(status_code=502, detail=f"Hint generation failed: {exc}") from exc
    print(f"the AI hint: {text}")
    # Keep hints concise and avoid over-long responses even if the model drifts.
    truncated = text.split("\n")[0][:240]
    word_count = len(truncated.split())

    if word_count < 6:
        rem = remaining_numbers or payload.numbers
        if eval_value is not None:
            delta = eval_value - payload.target
            if delta < -3:
                fallback = "Raise the total: multiply a mid pair, then add a small remaining number." 
            elif delta > 3:
                fallback = "Reduce the total: use one division or subtraction on the biggest pair before combining the rest." 
            else:
                fallback = "Nudge closer: reorder with parentheses and try forming a 6 or 8 first." 
        elif len(rem) >= 2:
            a, b = rem[0], rem[1]
            fallback = f"Try {a} {"*" if a*b <= payload.target else "+"} {b} to make a factor, then finish with the others." 
        elif rem:
            fallback = f"Blend {rem[0]} with the largest number using division or subtraction to fine-tune." 
        else:
            fallback = "Reorder with parentheses and try a single division before adding." 
        truncated = fallback
    print(f"the AI final hint: {truncated}")
    return HintResponse(hint=truncated, model=GEMINI_MODEL)


# For local dev: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
