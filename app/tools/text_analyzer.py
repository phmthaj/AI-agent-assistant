import re
from collections import Counter
from typing import Any

from app.tools.base import BaseTool


class TextAnalyzerTool(BaseTool):
    name = "text_analyzer"
    description = "Analyze text statistics such as word count, sentences, and top terms."
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to analyze.",
            },
            "top_n": {
                "type": "integer",
                "description": "Number of frequent terms to return.",
                "minimum": 1,
                "maximum": 20,
            },
        },
        "required": ["text"],
        "additionalProperties": False,
    }

    _word_pattern = re.compile(r"[\w']+", re.UNICODE)
    _sentence_pattern = re.compile(r"[^.!?]+[.!?]?")

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        text = arguments.get("text")
        if not isinstance(text, str) or not text.strip():
            return {"ok": False, "error": "Argument 'text' must be non-empty."}

        top_n = arguments.get("top_n", 10)
        if not isinstance(top_n, int):
            top_n = 10
        top_n = max(1, min(top_n, 20))

        words = self._word_pattern.findall(text.lower())
        sentences = [
            sentence.strip()
            for sentence in self._sentence_pattern.findall(text)
            if sentence.strip()
        ]
        top_terms = Counter(words).most_common(top_n)
        average_word_length = (
            sum(len(word) for word in words) / len(words)
            if words
            else 0
        )

        return {
            "ok": True,
            "characters": len(text),
            "words": len(words),
            "unique_words": len(set(words)),
            "sentences": len(sentences),
            "average_word_length": round(average_word_length, 2),
            "top_terms": [
                {"term": term, "count": count}
                for term, count in top_terms
            ],
        }
