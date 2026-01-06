"""Unit tests for the Math24 Backend API"""

import ast
import os
from collections import Counter
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import (
    ALLOWED_BIN_OPS,
    CheckRequest,
    HintRequest,
    NumbersPayload,
    _safe_eval,
    app,
    build_hint_prompt,
    build_hints,
    evaluate_expression,
    extract_numbers,
    extract_operators,
    numbers_match,
    solution_first_step,
)


client = TestClient(app)


# --- Test Expression Utilities ---


class TestSafeEval:
    """Tests for the _safe_eval function"""

    def test_constant_integer(self):
        node = ast.parse("42", mode="eval")
        assert _safe_eval(node.body) == 42.0

    def test_constant_float(self):
        node = ast.parse("3.14", mode="eval")
        assert _safe_eval(node.body) == 3.14

    def test_addition(self):
        node = ast.parse("2 + 3", mode="eval")
        assert _safe_eval(node.body) == 5.0

    def test_subtraction(self):
        node = ast.parse("10 - 4", mode="eval")
        assert _safe_eval(node.body) == 6.0

    def test_multiplication(self):
        node = ast.parse("3 * 4", mode="eval")
        assert _safe_eval(node.body) == 12.0

    def test_division(self):
        node = ast.parse("8 / 2", mode="eval")
        assert _safe_eval(node.body) == 4.0

    def test_division_by_zero(self):
        node = ast.parse("5 / 0", mode="eval")
        with pytest.raises(ZeroDivisionError):
            _safe_eval(node.body)

    def test_unary_plus(self):
        node = ast.parse("+5", mode="eval")
        assert _safe_eval(node.body) == 5.0

    def test_unary_minus(self):
        node = ast.parse("-7", mode="eval")
        assert _safe_eval(node.body) == -7.0

    def test_complex_expression(self):
        node = ast.parse("(3 + 5) * 2 - 4", mode="eval")
        assert _safe_eval(node.body) == 12.0

    def test_unsupported_operation(self):
        node = ast.parse("2 ** 3", mode="eval")
        with pytest.raises(ValueError, match="Unsupported expression"):
            _safe_eval(node.body)

    def test_non_numeric_constant(self):
        node = ast.parse("'hello'", mode="eval")
        with pytest.raises(ValueError, match="Only numeric constants are allowed"):
            _safe_eval(node.body)


class TestEvaluateExpression:
    """Tests for the evaluate_expression function"""

    def test_simple_addition(self):
        assert evaluate_expression("2 + 3") == 5.0

    def test_order_of_operations(self):
        assert evaluate_expression("2 + 3 * 4") == 14.0

    def test_parentheses(self):
        assert evaluate_expression("(2 + 3) * 4") == 20.0

    def test_division(self):
        assert evaluate_expression("24 / 6") == 4.0

    def test_complex_expression(self):
        assert evaluate_expression("(8 - 2) * 4 + 1") == 25.0


class TestExtractNumbers:
    """Tests for the extract_numbers function"""

    def test_single_digit(self):
        assert extract_numbers("3 + 5") == [3, 5]

    def test_multi_digit(self):
        assert extract_numbers("12 + 34") == [12, 34]

    def test_complex_expression(self):
        assert extract_numbers("(8 - 2) * 4 + 1") == [8, 2, 4, 1]

    def test_no_numbers(self):
        assert extract_numbers("+ - * /") == []

    def test_decimal_ignored(self):
        # Only extracts integer parts
        assert extract_numbers("3.14 + 2.5") == [3, 14, 2, 5]


class TestExtractOperators:
    """Tests for the extract_operators function"""

    def test_basic_operators(self):
        assert extract_operators("3 + 5 - 2") == ["+", "-"]

    def test_all_operators(self):
        assert extract_operators("3 + 5 - 2 * 4 / 8") == ["+", "-", "*", "/"]

    def test_no_operators(self):
        assert extract_operators("12345") == []

    def test_operators_in_parentheses(self):
        assert extract_operators("(3 + 5) * (8 - 2)") == ["+", "*", "-"]


class TestNumbersMatch:
    """Tests for the numbers_match function"""

    def test_exact_match(self):
        assert numbers_match([1, 2, 3, 4], [1, 2, 3, 4])

    def test_different_order(self):
        assert numbers_match([1, 2, 3, 4], [4, 3, 2, 1])

    def test_duplicate_numbers_match(self):
        assert numbers_match([1, 1, 2, 3], [1, 2, 1, 3])

    def test_different_numbers(self):
        assert not numbers_match([1, 2, 3, 4], [1, 2, 3, 5])

    def test_different_counts(self):
        assert not numbers_match([1, 1, 2, 3], [1, 2, 2, 3])

    def test_different_lengths(self):
        assert not numbers_match([1, 2, 3], [1, 2, 3, 4])


class TestSolutionFirstStep:
    """Tests for the solution_first_step function"""

    def test_simple_addition(self):
        result = solution_first_step("3 + 5")
        assert result == "A valid solve starts by combining 3 and 5 using +."

    def test_multiplication(self):
        result = solution_first_step("4 * 6")
        assert result == "A valid solve starts by combining 4 and 6 using *."

    def test_complex_expression(self):
        result = solution_first_step("(3 + 5) * 2")
        # The outermost operation is multiplication, so it returns the multiply step
        assert "2" in result and "*" in result

    def test_invalid_expression(self):
        result = solution_first_step("invalid")
        assert result is None

    def test_nested_expression(self):
        result = solution_first_step("((2 + 3) * 4) - 1")
        # Should extract the outermost binop
        assert result is not None


class TestBuildHints:
    """Tests for the build_hints function"""

    def test_correct_answer(self):
        request = CheckRequest(numbers=[3, 8, 3, 8], expression="8/(3-8/3)", target=24)
        hints = build_hints(request, 24.0, [])
        assert any("Great job" in h for h in hints)

    def test_close_answer(self):
        request = CheckRequest(numbers=[1, 2, 3, 4], expression="1+2+3+4", target=24)
        hints = build_hints(request, 10.0, [])
        # Check that we get some hints for an incorrect answer
        assert len(hints) > 0
        assert not any("Great job" in h for h in hints)

    def test_with_errors(self):
        request = CheckRequest(numbers=[1, 2, 3, 4], expression="1+2+3", target=24)
        errors = ["Numbers used do not match the provided set"]
        hints = build_hints(request, 6.0, errors)
        assert any("number" in h.lower() for h in hints)

    def test_division_by_zero_error(self):
        request = CheckRequest(numbers=[1, 2, 3, 4], expression="1/0", target=24)
        errors = ["Division by zero"]
        hints = build_hints(request, None, errors)
        assert any("zero" in h.lower() for h in hints)

    def test_unsupported_operation_error(self):
        request = CheckRequest(numbers=[1, 2, 3, 4], expression="2**3", target=24)
        errors = ["Unsupported expression"]
        hints = build_hints(request, None, errors)
        assert any("Stick to" in h for h in hints)


class TestBuildHintPrompt:
    """Tests for the build_hint_prompt function"""

    def test_basic_prompt(self):
        request = HintRequest(numbers=[1, 2, 3, 4], expression="1+2", target=24)
        prompt = build_hint_prompt(
            request,
            used_numbers=[1, 2],
            remaining_numbers=[3, 4],
            parse_note="expression parses",
            solution_step="A valid solve starts by combining 3 and 4 using *.",
            solution_ops=["+", "*"],
        )
        assert "1, 2, 3, 4" in prompt
        assert "1, 2" in prompt
        assert "3, 4" in prompt
        assert "1+2" in prompt
        assert "Target: 24" in prompt

    def test_no_expression(self):
        request = HintRequest(numbers=[1, 2, 3, 4], expression="", target=24)
        prompt = build_hint_prompt(
            request,
            used_numbers=[],
            remaining_numbers=[1, 2, 3, 4],
            parse_note="no expression yet",
            solution_step=None,
            solution_ops=[],
        )
        assert "no expression yet" in prompt
        assert "none" in prompt.lower()


# --- Test Pydantic Models ---


class TestNumbersPayload:
    """Tests for the NumbersPayload model"""

    def test_valid_payload(self):
        payload = NumbersPayload(numbers=[1, 2, 3, 4], target=24)
        assert payload.numbers == [1, 2, 3, 4]
        assert payload.target == 24

    def test_default_target(self):
        payload = NumbersPayload(numbers=[1, 2, 3, 4])
        assert payload.target == 24

    def test_negative_number(self):
        with pytest.raises(ValueError, match="Numbers must be positive"):
            NumbersPayload(numbers=[1, -2, 3, 4])

    def test_zero_number(self):
        with pytest.raises(ValueError, match="Numbers must be positive"):
            NumbersPayload(numbers=[0, 1, 2, 3])

    def test_mode_easy(self):
        payload = NumbersPayload(numbers=[1, 2, 3, 4], mode="easy")
        assert payload.mode == "easy"

    def test_mode_hard(self):
        payload = NumbersPayload(numbers=[1, 2, 3, 4], mode="hard")
        assert payload.mode == "hard"


# --- Test API Endpoints ---


class TestHealthEndpoint:
    """Tests for the /health endpoint"""

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestCheckEndpoint:
    """Tests for the /check endpoint"""

    def test_valid_solution(self):
        response = client.post(
            "/check",
            json={
                "numbers": [3, 8, 3, 8],
                "expression": "8/(3-8/3)",
                "target": 24,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["value"] == pytest.approx(24.0)
        assert data["errors"] == []

    def test_invalid_numbers(self):
        response = client.post(
            "/check",
            json={
                "numbers": [1, 2, 3, 4],
                "expression": "5 + 6",
                "target": 24,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0
        assert any("Numbers used do not match" in e for e in data["errors"])

    def test_syntax_error(self):
        response = client.post(
            "/check",
            json={
                "numbers": [1, 2, 3, 4],
                "expression": "1 + + 2",
                "target": 24,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    def test_division_by_zero(self):
        response = client.post(
            "/check",
            json={
                "numbers": [1, 2, 3, 4],
                "expression": "1 / (2 - 2)",
                "target": 24,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert any("Division by zero" in e for e in data["errors"])

    def test_incorrect_value(self):
        response = client.post(
            "/check",
            json={
                "numbers": [1, 2, 3, 4],
                "expression": "1 + 2 + 3 + 4",
                "target": 24,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["value"] == 10.0

    def test_normalized_expression(self):
        response = client.post(
            "/check",
            json={
                "numbers": [3, 8, 3, 8],
                "expression": "8 / ( 3 - 8 / 3 )",
                "target": 24,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["normalized_expression"] == "8/(3-8/3)"


class TestHintEndpoint:
    """Tests for the /hint endpoint"""

    @patch("main.GEN_MODEL")
    def test_hint_success(self, mock_model):
        # Mock the Gemini API response
        mock_response = MagicMock()
        mock_response.text = "Try multiplying 3 and 8 first."
        mock_model.generate_content.return_value = mock_response

        response = client.post(
            "/hint",
            json={
                "numbers": [3, 8, 3, 8],
                "expression": "",
                "target": 24,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "hint" in data
        assert "model" in data
        assert len(data["hint"]) > 0

    @patch("main.GEN_MODEL")
    def test_hint_with_partial_expression(self, mock_model):
        mock_response = MagicMock()
        mock_response.text = "Now try dividing by 3."
        mock_model.generate_content.return_value = mock_response

        response = client.post(
            "/hint",
            json={
                "numbers": [3, 8, 3, 8],
                "expression": "3 * 8",
                "target": 24,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "hint" in data

    @patch("main.GEN_MODEL")
    def test_hint_with_solution(self, mock_model):
        mock_response = MagicMock()
        mock_response.text = "Consider using division."
        mock_model.generate_content.return_value = mock_response

        response = client.post(
            "/hint",
            json={
                "numbers": [3, 8, 3, 8],
                "expression": "",
                "solution": "8/(3-8/3)",
                "target": 24,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "hint" in data

    @patch("main.GEN_MODEL")
    def test_hint_api_failure(self, mock_model):
        # Mock API failure
        mock_model.generate_content.side_effect = Exception("API Error")

        response = client.post(
            "/hint",
            json={
                "numbers": [3, 8, 3, 8],
                "expression": "",
                "target": 24,
            },
        )
        assert response.status_code == 502

    @patch("main.GEN_MODEL")
    def test_hint_short_response_fallback(self, mock_model):
        # Mock a very short response to trigger fallback logic
        mock_response = MagicMock()
        mock_response.text = "Try"  # Too short
        mock_model.generate_content.return_value = mock_response

        response = client.post(
            "/hint",
            json={
                "numbers": [3, 8, 3, 8],
                "expression": "3 * 8",
                "target": 24,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Should use fallback hint
        assert len(data["hint"].split()) >= 6


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_single_number(self):
        response = client.post(
            "/check",
            json={
                "numbers": [24],
                "expression": "24",
                "target": 24,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_large_numbers(self):
        response = client.post(
            "/check",
            json={
                "numbers": [100, 200, 300, 400],
                "expression": "(400 - 100) / (200 / 300)",
                "target": 450,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_float_result_close_to_target(self):
        response = client.post(
            "/check",
            json={
                "numbers": [1, 3, 4, 6],
                "expression": "6 / (1 - 3/4)",
                "target": 24,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_duplicate_numbers(self):
        response = client.post(
            "/check",
            json={
                "numbers": [2, 2, 2, 2],
                "expression": "(2 + 2) * (2 + 2)",
                "target": 16,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["value"] == 16.0
