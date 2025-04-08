from typing import List
import subprocess
import json

def extract_keywords_with_mistral(text: str, num_keywords: int = 5) -> List[str]:
    prompt = f"Extract {num_keywords} relevant keywords or phrases from the following text:\n\"{text}\"\nReturn them as a list."

    # Run the Mistral model locally via Ollama CLI
    result = subprocess.run(
        ["ollama", "run", "mistral"],
        input=prompt.encode(),
        capture_output=True
    )

    output = result.stdout.decode().strip()

    # Try to parse list-like output
    try:
        keywords = json.loads(output)
    except:
        keywords = [kw.strip("-• ") for kw in output.split("\n") if kw.strip()]

    return keywords