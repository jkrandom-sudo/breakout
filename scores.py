"""High-score manager — persists top 10 scores to a JSON file.

Usage::

    mgr = ScoreManager()
    mgr.add_score(450, "Player")
    top = mgr.top_scores()
"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Any


SCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores.json")
MAX_SCORES = 10


class ScoreEntry:
    """A single high-score entry.

    Attributes:
        score: The player's score.
        name: Player name (default "Player").
        date: ISO-format date string.
    """

    def __init__(self, score: int, name: str = "Player", date_str: str | None = None) -> None:
        self.score = score
        self.name = name
        self.date = date_str or date.today().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {"score": self.score, "name": self.name, "date": self.date}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScoreEntry:
        """Deserialise from a dict."""
        return cls(
            score=int(data["score"]),
            name=str(data.get("name", "Player")),
            date_str=str(data.get("date", date.today().isoformat())),
        )

    def __repr__(self) -> str:
        return f"ScoreEntry({self.score}, {self.name!r}, {self.date!r})"


class ScoreManager:
    """Load, save, and query high scores from a JSON file.

    Scores are kept in descending order (highest first).  Only the top
    *MAX_SCORES* (10) entries are persisted.
    """

    def __init__(self, filepath: str | None = None) -> None:
        self.filepath = filepath or SCORES_FILE
        self._scores: list[ScoreEntry] = []
        self.load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load scores from the JSON file (silent if missing/corrupt)."""
        self._scores = []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for entry in data:
                self._scores.append(ScoreEntry.from_dict(entry))
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            self._scores = []
        self._scores.sort(key=lambda e: e.score, reverse=True)

    def save(self) -> None:
        """Write the current top scores to the JSON file."""
        data = [e.to_dict() for e in self._scores[:MAX_SCORES]]
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_score(self, score: int, name: str = "Player") -> int | None:
        """Add a new score entry.

        Returns the rank (1-indexed) if the score qualifies for the top 10,
        or ``None`` if it doesn't.
        """
        entry = ScoreEntry(score, name)
        self._scores.append(entry)
        self._scores.sort(key=lambda e: e.score, reverse=True)
        self._scores = self._scores[:MAX_SCORES]
        self.save()

        # Determine rank
        for i, e in enumerate(self._scores):
            if e is entry:
                return i + 1
        return None

    def is_high_score(self, score: int) -> bool:
        """Return True if *score* would make the top 10."""
        if len(self._scores) < MAX_SCORES:
            return True
        return score > self._scores[-1].score

    def top_scores(self) -> list[ScoreEntry]:
        """Return the current top scores (highest first)."""
        return list(self._scores)

    def clear(self) -> None:
        """Remove all scores."""
        self._scores = []
        self.save()
