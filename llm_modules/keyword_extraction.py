from typing import List
import os
from openai import OpenAI

# Set up Groq-compatible client
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def extract_keywords_with_groq(text: str, num_keywords: int = 5) -> List[str]:
    prompt = f"""
You are an expert assistant for a location recommendation system.

From the following user input:
\"{text}\"

Extract {num_keywords} high-quality **searchable concepts or keywords** that best capture the user's intent and context.

The keywords must be relevant to at least one of the following:
- 🗺️ Places: physical locations, cafe/restaurant types, districts, streets, landmarks, cultural spots
- 🧠 Moods & Emotions: feelings, atmosphere (e.g. quiet, energetic, nostalgic, romantic)
- 🎯 Intent & Use Cases: what the user wants to do (e.g. work remotely, meet someone, relax, explore)
- 🌱 Personal Preferences: dietary (e.g. vegan), service-related (e.g. fast wifi, pet friendly, cheap), music, ambiance

Instructions:
- Extract **meaningful** keywords (not generic filler like "looking for" or "I want")
- Focus on **real-world identifiable tags** or concepts
- Do NOT include full sentences or explanations — just the keywords
- Return the keywords as a simple Python list

Example:
Input: "I’m feeling a bit lonely, just want a quiet, hidden cafe with old books and some acoustic music around District 1"
Output: ["quiet", "hidden cafe", "old books", "acoustic music", "District 1"]

Now extract for this input:
"{text}"
"""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    return [line.strip("-• ").strip() for line in content.strip().split("\n") if line.strip()]