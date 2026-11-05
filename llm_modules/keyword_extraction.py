"""Step 1 of the Cafe Finder engine: turn what someone types into a few searchable keywords.

    python -m llm_modules.keyword_extraction "a quiet cafe with old books near District 1"

Uses Groq's OpenAI-compatible API. Set GROQ_API_KEY (see utils/.env.example);
GROQ_MODEL overrides the model.
"""
import ast
import json
import os
import re
import sys
from typing import List, Optional

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")  # llama3-8b-8192 and then llama-3.1-8b-instant were retired by Groq
BASE_URL = "https://api.groq.com/openai/v1"

PROMPT = """You are an expert assistant for a location recommendation system.

From the following user input:
"{text}"

Extract {num_keywords} high-quality searchable concepts or keywords that best capture the user's intent and context.

The keywords must be relevant to at least one of the following:
- Places: physical locations, cafe/restaurant types, districts, streets, landmarks, cultural spots
- Moods & Emotions: feelings, atmosphere (e.g. quiet, energetic, nostalgic, romantic)
- Intent & Use Cases: what the user wants to do (e.g. work remotely, meet someone, relax, explore)
- Personal Preferences: dietary (e.g. vegan), service-related (e.g. fast wifi, pet friendly, cheap), music, ambiance

Instructions:
- Extract meaningful keywords (not generic filler like "looking for" or "I want")
- Focus on real-world identifiable tags or concepts
- Do NOT include full sentences or explanations, just the keywords
- Return ONLY a JSON array of strings, on one line

Example:
Input: "I'm feeling a bit lonely, just want a quiet, hidden cafe with old books and some acoustic music around District 1"
Output: ["quiet", "hidden cafe", "old books", "acoustic music", "District 1"]

Now extract for this input:
"{text}"
"""


def parse_keywords(content: str, limit: int = 5) -> List[str]:
    """Read the model's reply as a list of keywords.

    Models do not always follow the format, so this accepts, in order:
    a JSON array, a Python list literal, then one keyword per line (with or
    without bullets or numbering). Code fences and text around the list are ignored.
    """
    text = (content or "").strip()
    text = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", text).strip()
    candidates = []
    match = re.search(r"\[.*\]", text, flags=re.S)
    if match:
        chunk = match.group(0)
        for loader in (json.loads, ast.literal_eval):
            try:
                value = loader(chunk)
            except (ValueError, SyntaxError):
                continue
            if isinstance(value, (list, tuple)):
                candidates = [str(v) for v in value]
                break
    if not candidates:
        candidates = [re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line) for line in text.splitlines()]
    seen, out = set(), []
    for kw in candidates:
        kw = kw.strip().strip("\"'").strip()
        if not kw or len(kw) > 60 or kw.lower() in seen:
            continue
        seen.add(kw.lower())
        out.append(kw)
    return out[:limit]


def extract_keywords_with_groq(text: str, num_keywords: int = 5, client: Optional[object] = None) -> List[str]:
    """Ask the LLM for keywords. Pass `client` to use another OpenAI-compatible client (or a fake one in tests)."""
    if client is None:
        from openai import OpenAI  # imported here so tests and parse_keywords need no API key

        client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url=BASE_URL)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT.format(text=text, num_keywords=num_keywords)}],
        temperature=0.3,  # the same sentence should give nearly the same keywords every time
    )
    return parse_keywords(response.choices[0].message.content, num_keywords)


if __name__ == "__main__":
    sentence = " ".join(sys.argv[1:]) or "I'm looking for a quiet vegan cafe in District 1 with strong wifi to work remotely."
    print(extract_keywords_with_groq(sentence))
