"""CursesRenderer — all curses-dependent display code.

This module is the **only** file that imports ``curses``.  It takes a
``BreakoutGame`` instance and draws its state to the terminal.
"""

from __future__ import annotations

import curses
import math
from typing import TYPE_CHECKING, Any

from i18n import t

if TYPE_CHECKING:
    from breakout_game import BreakoutGame

# ── Colour-pair constants (indexed by brick row colour 1-5) ──────────────
COLOR_RED = 1
COLOR_ORANGE = 2
COLOR_YELLOW = 3
COLOR_GREEN = 4
COLOR_BLUE = 5
COLOR_WHITE = 6
COLOR_CYAN = 7
COLOR_MAGENTA = 8

# Colour-pair numbers (curses colour-pair indices)
CP_BORDER = 10
CP_SCORE = 11
CP_PADDLE = 12
CP_BALL = 13
CP_BRICK_BASE = 20  # bricks use CP_BRICK_BASE + colour_index
CP_HEART = 14
CP_TITLE = 15
CP_OVERLAY = 16


def init_colours() -> None:
    """Initialise curses colour pairs for the entire game."""
    curses.start_color()
    curses.use_default_colors()

    # Define custom colours if terminal supports 256 colours
    if curses.COLORS >= 256:
        curses.init_color(COLOR_RED, 1000, 200, 200)       # red
        curses.init_color(COLOR_ORANGE, 1000, 600, 0)      # orange
        curses.init_color(COLOR_YELLOW, 1000, 1000, 0)     # yellow
        curses.init_color(COLOR_GREEN, 200, 800, 200)      # green
        curses.init_color(COLOR_BLUE, 200, 400, 1000)      # blue
        curses.init_color(COLOR_WHITE, 800, 800, 800)      # white
        curses.init_color(COLOR_CYAN, 0, 1000, 1000)       # cyan
        curses.init_color(COLOR_MAGENTA, 1000, 0, 1000)    # magenta

    # Border
    curses.init_pair(CP_BORDER, curses.COLOR_WHITE, -1)
    # Score / status text
    curses.init_pair(CP_SCORE, curses.COLOR_YELLOW, -1)
    # Paddle
    curses.init_pair(CP_PADDLE, curses.COLOR_CYAN, curses.COLOR_CYAN)
    # Ball
    curses.init_pair(CP_BALL, curses.COLOR_WHITE, -1)
    # Hearts
    curses.init_pair(CP_HEART, curses.COLOR_RED, -1)
    # Title / overlay
    curses.init_pair(CP_TITLE, curses.COLOR_YELLOW, -1)
    # Overlay background
    curses.init_pair(CP_OVERLAY, curses.COLOR_WHITE, curses.COLOR_BLUE)

    # Brick colours (pair = CP_BRICK_BASE + colour_index)
    brick_colors = {
        1: curses.COLOR_RED,
        2: curses.COLOR_YELLOW,   # orange → use yellow
        3: curses.COLOR_YELLOW,
        4: curses.COLOR_GREEN,
        5: curses.COLOR_BLUE,
    }
    for idx, c in brick_colors.items():
        curses.init_pair(CP_BRICK_BASE + idx, c, c)


class CursesRenderer:
    """Draws the game state to a curses window.

    Args:
        stdscr: The main curses window (from ``curses.wrapper``).
    """

    def __init__(self, stdscr: Any) -> None:
        self.stdscr = stdscr
        init_colours()
        curses.curs_set(0)  # hide cursor

    # ======================================================================
    # Public draw methods
    # ======================================================================

    def draw(self, game: BreakoutGame) -> None:
        """Full redraw of the entire game screen."""
        self.stdscr.erase()
        self._draw_border(game)
        self._draw_top_bar(game)
        self._draw_bricks(game)
        self._draw_paddle(game)
        self._draw_ball(game)

        if game.paused:
            self._draw_pause_overlay(game)
        if game.game_over:
            self._draw_game_over(game)
        if game.victory:
            self._draw_victory(game)

        self.stdscr.noutrefresh()

    def draw_high_scores(
        self, game: BreakoutGame, scores: list[Any], title: str
    ) -> None:
        """Draw the high-score screen overlay."""
        self.stdscr.erase()
        self._draw_border(game)

        h, w = self.stdscr.getmaxyx()
        title_text = f" {title} "
        y = 3
        x = (w - len(title_text)) // 2
        self._addstr(y, x, title_text, curses.color_pair(CP_TITLE) | curses.A_BOLD)

        if not scores:
            msg = t("no_scores", game.language)
            self._addstr(y + 2, (w - len(msg)) // 2, msg)
        else:
            header = f"{'#':>3}  {t('col_name', game.language):<16}  {t('col_score', game.language):>6}  {t('col_date', game.language):<12}"
            self._addstr(y + 2, (w - len(header)) // 2, header, curses.A_UNDERLINE)
            for i, entry in enumerate(scores):
                line = f"{i + 1:>3}  {entry.name:<16}  {entry.score:>6}  {entry.date:<12}"
                self._addstr(y + 4 + i, (w - len(line)) // 2, line)

        hint = game.get_text("close_hint")
        self._addstr(h - 2, (w - len(hint)) // 2, hint, curses.A_DIM)

        self.stdscr.noutrefresh()

    def draw_name_prompt(self, game: BreakoutGame, current_input: str) -> None:
        """Draw the 'enter your name' prompt overlay."""
        self.draw(game)
        h, w = self.stdscr.getmaxyx()

        prompt = game.get_text("enter_name")
        lines = [
            f"  {game.get_text('new_high_score')}  ",
            "",
            f"  {prompt}: {current_input}_  ",
        ]
        box_h = len(lines) + 2
        box_w = max(len(l) for l in lines) + 4
        box_y = h // 2 - box_h // 2
        box_x = w // 2 - box_w // 2

        for i, line in enumerate(lines):
            self._addstr(box_y + 1 + i, box_x + 2, line, curses.A_BOLD)

        self.stdscr.noutrefresh()

    def draw_controls(self, game: BreakoutGame) -> None:
        """Draw the controls help overlay."""
        self.stdscr.erase()
        self._draw_border(game)
        h, w = self.stdscr.getmaxyx()

        title = game.get_text("controls_title")
        controls = game.get_texts("controls")

        y = 3
        x = (w - len(title)) // 2
        self._addstr(y, x, title, curses.color_pair(CP_TITLE) | curses.A_BOLD)

        for i, line in enumerate(controls):
            self._addstr(y + 2 + i, (w - len(line)) // 2, line)

        hint = game.get_text("close_hint")
        self._addstr(h - 2, (w - len(hint)) // 2, hint, curses.A_DIM)
        self.stdscr.noutrefresh()

    # ======================================================================
    # Sound effects (terminal bell)
    # ======================================================================

    def play_sound(self, game: BreakoutGame, event: str) -> None:
        """Ring the terminal bell for a game event (if sound is enabled)."""
        if not game.sound_enabled:
            return
        curses.beep()

    # ======================================================================
    # Internal drawing helpers
    # ======================================================================

    def _draw_border(self, game: BreakoutGame) -> None:
        """Draw the outer border frame."""
        h, w = self.stdscr.getmaxyx()
        cp = curses.color_pair(CP_BORDER)

        # Top & bottom
        try:
            self.stdscr.addch(0, 0, curses.ACS_ULCORNER, cp)
            self.stdscr.addch(0, w - 1, curses.ACS_URCORNER, cp)
            self.stdscr.addch(h - 1, 0, curses.ACS_LLCORNER, cp)
            self.stdscr.addch(h - 1, w - 1, curses.ACS_LRCORNER, cp)
            self.stdscr.hline(0, 1, curses.ACS_HLINE, w - 2, cp)
            self.stdscr.hline(h - 1, 1, curses.ACS_HLINE, w - 2, cp)
            self.stdscr.vline(1, 0, curses.ACS_VLINE, h - 2, cp)
            self.stdscr.vline(1, w - 1, curses.ACS_VLINE, h - 2, cp)
        except curses.error:
            pass  # terminal too small — ignore

    def _draw_top_bar(self, game: BreakoutGame) -> None:
        """Draw score, lives, level, speed, and sound indicator at the top."""
        cp = curses.color_pair(CP_SCORE)
        h, w = self.stdscr.getmaxyx()

        score_text = f"{game.get_text('score')}: {game.score}"
        lives_text = f"{game.get_text('lives')}: {'♥' * game.lives}{'♡' * (game.INITIAL_LIVES - game.lives)}"
        level_text = f"{game.get_text('level')}: {game.level}"
        speed_text = f"{game.get_text('speed')}: {game.speed_level}"
        sound_text = game.get_text("sound_on") if game.sound_enabled else game.get_text("sound_off")

        # Layout: score | lives | level | speed | sound
        parts = [score_text, lives_text, level_text, speed_text, sound_text]
        gap = 2
        total_len = sum(len(p) for p in parts) + gap * (len(parts) - 1)
        x = (w - total_len) // 2
        if x < 1:
            x = 1

        for p in parts:
            self._addstr(1, x, p, cp)
            x += len(p) + gap

    def _draw_bricks(self, game: BreakoutGame) -> None:
        """Draw all non-destroyed bricks as coloured blocks."""
        for brick in game.bricks:
            if brick.destroyed:
                continue
            cp = curses.color_pair(CP_BRICK_BASE + brick.color_index)
            for dx in range(brick.width):
                try:
                    self.stdscr.addch(brick.y, brick.x + dx, "█", cp)
                except curses.error:
                    pass

    def _draw_paddle(self, game: BreakoutGame) -> None:
        """Draw the paddle as a solid bar."""
        cp = curses.color_pair(CP_PADDLE)
        for dx in range(game.PADDLE_WIDTH):
            try:
                self.stdscr.addch(game.PADDLE_Y, game.paddle_x + dx, "█", cp)
            except curses.error:
                pass

    def _draw_ball(self, game: BreakoutGame) -> None:
        """Draw the ball as a bright character."""
        cp = curses.color_pair(CP_BALL) | curses.A_BOLD
        bx, by = int(game.ball_x), int(game.ball_y)
        try:
            ch = "●" if game.ball_attached else "○"
            self.stdscr.addch(by, bx, ch, cp)
        except curses.error:
            pass

    # ------------------------------------------------------------------
    # Overlays
    # ------------------------------------------------------------------

    def _draw_pause_overlay(self, game: BreakoutGame) -> None:
        """Draw the PAUSED overlay in the centre of the screen."""
        h, w = self.stdscr.getmaxyx()
        text = game.get_text("paused")
        hint = game.get_text("pause_hint")
        self._draw_centred_box(h, w, [text, "", hint])

    def _draw_game_over(self, game: BreakoutGame) -> None:
        """Draw the GAME OVER screen."""
        h, w = self.stdscr.getmaxyx()
        lines = [
            f"  {game.get_text('game_over')}  ",
            "",
            f"  {game.get_text('final_score')}: {game.score}  ",
            "",
            f"  {game.get_text('press_r')}  ",
            f"  {game.get_text('press_h')}  ",
        ]
        self._draw_centred_box(h, w, lines)

    def _draw_victory(self, game: BreakoutGame) -> None:
        """Draw the VICTORY screen."""
        h, w = self.stdscr.getmaxyx()
        lines = [
            f"  {game.get_text('victory')}  ",
            "",
            f"  {game.get_text('final_score')}: {game.score}  ",
            "",
            f"  {game.get_text('press_r')}  ",
        ]
        self._draw_centred_box(h, w, lines)

    def _draw_centred_box(self, h: int, w: int, lines: list[str]) -> None:
        """Draw a centred overlay box with the given text lines."""
        box_h = len(lines) + 2
        box_w = max(len(l) for l in lines) + 4
        box_y = h // 2 - box_h // 2
        box_x = w // 2 - box_w // 2

        cp = curses.color_pair(CP_OVERLAY)

        # Draw box background
        for dy in range(box_h):
            for dx in range(box_w):
                try:
                    self.stdscr.addch(box_y + dy, box_x + dx, " ", cp)
                except curses.error:
                    pass

        # Draw text
        for i, line in enumerate(lines):
            self._addstr(box_y + 1 + i, box_x + 2, line, cp | curses.A_BOLD)

    # ------------------------------------------------------------------
    # Safe addstr wrapper
    # ------------------------------------------------------------------

    def _addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        """Write *text* at (y, x) with *attr*, ignoring curses errors."""
        try:
            self.stdscr.addstr(y, x, text, attr)
        except curses.error:
            pass
