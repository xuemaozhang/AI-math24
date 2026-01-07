import os
from dotenv import load_dotenv
# import google.generativeai as genai
import openai

# Load environment variables
load_dotenv()

# API_KEY = os.getenv("GEMINI_API_KEY")

# if not API_KEY:
#     raise ValueError("GEMINI_API_KEY not found in .env")


# genai.configure(api_key=API_KEY)

# GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
# GEN_MODEL = genai.GenerativeModel(GEMINI_MODEL)

# model = genai.GenerativeModel("gemini-2.5-flash")
# response = model.generate_content("Explain how AI works in a few words")
# print("fetched response:")
# print(response.text)

def build_hint_prompt(
    numbers,
    used_numbers,
    remaining_numbers,
    expression,
) -> str:
    numbers_str = ", ".join(str(n) for n in numbers)
    used_str = ", ".join(str(n) for n in used_numbers) or "none"
    remaining_str = ", ".join(str(n) for n in remaining_numbers) or "none"
    partial = expression.strip() or "(no expression yet)"


    prompt = f"""
        You are an assistant for the Math 24 game.

        Rules:
        - Use every provided number exactly once
        - Allowed operations: +, -, *, /, parentheses
        - Target: 24
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
        - Mode: easy

        Respond with just the hint text. Do not reveal a complete solution.

        Good examples (format/length):
        - "Make an 8 with 2 and 4, then multiply it by the largest remaining number."
        - "Use one division to reduce a big pair, then add the smallest number to reach 24."
        - "Aim for factors of 24 (3×8, 4×6); set up one of these with your remaining numbers."
        """

    return prompt.strip()

def extract_numbers(expr: str) -> list[int]:
    import re
    return [int(m.group()) for m in re.finditer(r"\d+", expr)]

numbers=[6, 4, 2, 2] 
expression='(2+4)' 
solution='((2+4)*(6-2))'

from collections import Counter  
used_numbers = extract_numbers(expression)
remaining_counter = Counter(numbers) - Counter(used_numbers)
remaining_numbers = list(remaining_counter.elements())


prompt = build_hint_prompt(
     numbers,
    used_numbers,
    remaining_numbers,
    expression,
)

client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
completion = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[
        {"role": "system", "content": prompt},
    ],
    temperature=0.1,
    top_p=0.9,
)
# completion = GEN_MODEL.generate_content(
#     prompt,
#     generation_config={
#         "max_output_tokens": 80,
#         "temperature": 0.85,
#         "top_p": 0.9,
#     },
# )
res = completion.choices[0].message.content.strip()
# text = (completion.text or "Try pairing numbers into factors of the target.").strip()
print("Generated hint:")
print(res)
