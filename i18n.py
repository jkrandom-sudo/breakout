"""Bilingual strings for Breakout game.

Provides the `t()` function for translating UI strings.
Both zh_CN (Chinese) and en_US (English) are supported.
"""

from __future__ import annotations

from typing import Any

STRINGS: dict[str, dict[str, Any]] = {
    "zh_CN": {
        # Terminal size check
        "terminal_too_small": "Terminal too small! Need at least 80x24.",
        # High scores
        "no_scores": "暂无记录",
        "high_scores_title": "最高分",
        "col_rank": "排名",
        "col_name": "姓名",
        "col_score": "分数",
        "col_date": "日期",
        # Controls
        "controls_title": "操作说明",
        "close_hint": "按任意键关闭",
        # Name prompt
        "new_high_score": "新纪录！",
        "enter_name": "请输入你的名字",
    },
    "en_US": {
        # Terminal size check
        "terminal_too_small": "Terminal too small! Need at least 80x24.",
        # High scores
        "no_scores": "No scores yet",
        "high_scores_title": "High Scores",
        "col_rank": "Rank",
        "col_name": "Name",
        "col_score": "Score",
        "col_date": "Date",
        # Controls
        "controls_title": "Controls",
        "close_hint": "Press any key to close",
        # Name prompt
        "new_high_score": "New High Score!",
        "enter_name": "Enter your name",
    },
}
# Aliases for short language codes used by breakout_game.py
STRINGS["zh"] = STRINGS["zh_CN"]
STRINGS["en"] = STRINGS["en_US"]

DEFAULT_LANG = "zh_CN"


def t(key: str, lang: str | None = None, **kwargs: Any) -> str:
    """Translate a string key into the given language.

    Args:
        key: Translation key.
        lang: Language code (zh_CN or en_US). Defaults to DEFAULT_LANG.
        **kwargs: Format arguments for the translation string.

    Returns:
        Translated string, or the key itself if not found.
    """
    if lang is None:
        lang = DEFAULT_LANG

    table = STRINGS.get(lang) or STRINGS[DEFAULT_LANG]
    s = table.get(key)
    if s is None:
        # Fallback to English
        s = STRINGS["en_US"].get(key, key)
    if kwargs:
        try:
            return s.format(**kwargs)
        except Exception:
            return s
    return s
