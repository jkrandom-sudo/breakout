#!/usr/bin/env python3
"""Breakout — Console-based Breakout game using Python curses.

Main entry point.  Run::

    python game.py

All game logic lives in :mod:`breakout_game` (no curses imports).
Curses display code lives in :mod:`renderer`.
High-score persistence lives in :mod:`scores`.
"""

from __future__ import annotations

import curses
import sys
import time
from typing import Any

from breakout_game import BreakoutGame
from i18n import t
from renderer import CursesRenderer
from scores import ScoreManager


def main(stdscr: Any) -> None:
    """Main game loop — called by ``curses.wrapper``."""
    # ── Terminal setup ────────────────────────────────────────────────
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    # ── Initialise components ─────────────────────────────────────────
    game = BreakoutGame()
    renderer = CursesRenderer(stdscr)
    score_mgr = ScoreManager()

    # State flags for the main loop
    showing_high_scores = False
    showing_controls = False
    entering_name = False
    name_input = ""
    high_score_checked = False

    # ── Main loop ─────────────────────────────────────────────────────
    while True:
        # Handle terminal resize
        try:
            h, w = stdscr.getmaxyx()
            if h < 24 or w < 80:
                stdscr.erase()
                msg = t("terminal_too_small", game.language)
                try:
                    stdscr.addstr(0, 0, msg)
                except curses.error:
                    pass
                stdscr.refresh()
                time.sleep(0.5)
                continue
        except curses.error:
            pass

        # ── Input handling ────────────────────────────────────────────
        key = None
        try:
            key = stdscr.getch()
        except curses.error:
            pass

        if key == ord("q"):
            break

        # Handle name entry overlay
        if entering_name:
            if key == 10 or key == ord("\n") or key == curses.KEY_ENTER:
                name = name_input.strip() or "Player"
                score_mgr.add_score(game.score, name)
                entering_name = False
                name_input = ""
                showing_high_scores = True
            elif key == 27 or key == ord("\x1b"):  # ESC
                score_mgr.add_score(game.score, "Player")
                entering_name = False
                name_input = ""
                showing_high_scores = True
            elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
                name_input = name_input[:-1]
            elif 32 <= key <= 126:
                if len(name_input) < 16:
                    name_input += chr(key)
            continue

        # Handle high-score screen
        if showing_high_scores:
            if key != -1:
                showing_high_scores = False
                if game.game_over or game.victory:
                    pass  # wait for R
                else:
                    game.paused = False
            else:
                renderer.draw_high_scores(
                    game,
                    score_mgr.top_scores(),
                    game.get_text("high_scores"),
                )
                curses.doupdate()
                time.sleep(0.05)
            continue

        # Handle controls overlay
        if showing_controls:
            if key != -1:
                showing_controls = False
            else:
                renderer.draw_controls(game)
                curses.doupdate()
                time.sleep(0.05)
            continue

        # ── Normal game input ─────────────────────────────────────────
        if key != -1:
            if key == ord("h") or key == ord("H"):
                showing_controls = True
            elif key == ord("p") or key == ord("P"):
                game.toggle_pause()
            elif key == ord("l") or key == ord("L"):
                game.toggle_language()
            elif key == ord("s") or key == ord("S"):
                game.toggle_sound()
            elif key == ord("=") or key == ord("+"):
                game.increase_speed()
            elif key == ord("-") or key == ord("_"):
                game.decrease_speed()
            elif key == ord("r") or key == ord("R"):
                if game.game_over or game.victory:
                    game.reset()
                    high_score_checked = False
            elif key == curses.KEY_LEFT:
                game.move_paddle(-1)
            elif key == curses.KEY_RIGHT:
                game.move_paddle(1)
            elif key == ord(" "):
                game.launch_ball()

        # ── Update game state ─────────────────────────────────────────
        events = game.update()

        # ── Sound effects ─────────────────────────────────────────────
        for ev in events:
            renderer.play_sound(game, ev)

        # ── Check high score on game over ─────────────────────────────
        if (game.game_over or game.victory) and not high_score_checked:
            high_score_checked = True
            if score_mgr.is_high_score(game.score):
                entering_name = True
                name_input = ""

        # ── Render ────────────────────────────────────────────────────
        renderer.draw(game)
        curses.doupdate()

        # ── Tick delay ────────────────────────────────────────────────
        time.sleep(game.tick_delay)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        sys.exit(0)
