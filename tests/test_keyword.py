"""Keyword extraction tests. They use a fake client, so they need no API key and no network.

    pytest -q
"""
import os
import sys
from types import SimpleNamespace

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm_modules.keyword_extraction import PROMPT, extract_keywords_with_groq, parse_keywords


class FakeClient:
    """Stands in for OpenAI(...): records the request and returns a canned reply."""

    def __init__(self, reply):
        self.reply, self.calls = reply, []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.reply))])


def test_json_array_on_one_line():
    # the old parser split on newlines, so this came back as a single keyword
    assert parse_keywords('["quiet", "hidden cafe", "old books", "acoustic music", "District 1"]') == [
        "quiet", "hidden cafe", "old books", "acoustic music", "District 1"]


def test_python_list_and_code_fence():
    assert parse_keywords("```python\n['vegan', 'fast wifi']\n```") == ["vegan", "fast wifi"]


def test_text_around_the_list():
    assert parse_keywords('Here are the keywords: ["work remotely", "quiet"] Hope this helps!') == ["work remotely", "quiet"]


def test_bullets_and_numbers():
    assert parse_keywords("- quiet\n2. vegan\n* District 1") == ["quiet", "vegan", "District 1"]


def test_duplicates_and_limit():
    assert parse_keywords('["Quiet", "quiet", "a", "b", "c", "d", "e"]', limit=3) == ["Quiet", "a", "b"]


def test_request_uses_prompt_and_low_temperature():
    fake = FakeClient('["quiet", "vegan", "District 1", "fast wifi", "work remotely"]')
    text = "I'm looking for a quiet vegan cafe in District 1 with strong wifi to work remotely."
    assert extract_keywords_with_groq(text, client=fake) == ["quiet", "vegan", "District 1", "fast wifi", "work remotely"]
    call = fake.calls[0]
    assert call["temperature"] == 0.3
    assert call["messages"][0]["content"] == PROMPT.format(text=text, num_keywords=5)
