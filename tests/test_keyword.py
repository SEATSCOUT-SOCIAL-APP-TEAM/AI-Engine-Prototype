import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from llm_modules.keyword_extraction import extract_keywords_with_mistral

if __name__ == "__main__":
    sample_text = "I'm looking for a quiet vegan cafe in District 1 with strong wifi to work remotely."
    keywords = extract_keywords_with_mistral(sample_text)
    print("Extracted Keywords:", keywords)