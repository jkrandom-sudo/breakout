"""BreakoutGame — Pure game logic with no curses imports.

This module contains the BreakoutGame class and supporting Brick class.
It has zero dependencies on curses, enabling unit testing without a terminal.
"""

from __future__ import annotations

import json
import os
from typing import Any


class Brick:
    """A single breakable brick in the game grid.

    Attributes:
        x: Left-edge column of the brick.
        y: Top-edge row of the brick.
        width: Brick width in characters.
        height: Brick height in characters (always 1).
        color_index: Logical color index (1-5, maps to rainbow).
        row: Grid row (0 = top, 4 = bottom).
        destroyed: Whether the brick has been hit.
    """

    def __init__(self, x: int, y: int, width: int, color_index: int, row: int) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = 1
        self.color_index = color_index
        self.row = row
        self.destroyed = False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def points(self) -> int:
        """Points awarded for destroying this brick.

        Bottom row (row 4) → 10 pts, top row (row 0) → 50 pts.
        """
        return (4 - self.row) * 10 + 10

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def contains(self, x: int, y: int) -> bool:
        """Return True if the point (*x*, *y*) falls inside this brick."""
        return self.x <= x <= self.x + self.width - 1 and self.y <= y <= self.y + self.height - 1


class BreakoutGame:
    """Encapsulates all Breakout game state and logic.

    This class has **no curses imports**.  It manages the paddle, ball,
    bricks, score, lives, level, speed, language, sound, and pause state.
    Call :meth:`update` each tick to advance the simulation; it returns a
    list of event strings that the rendering layer can use for sound effects.

    Constants
    ---------
    SCREEN_WIDTH / SCREEN_HEIGHT
        Nominal terminal dimensions (80 × 24).
    PLAY_LEFT / PLAY_RIGHT / PLAY_TOP / PLAY_BOTTOM
        Inner play-area boundaries (inside the border frame).
    BRICK_*
        Brick layout constants.
    PADDLE_WIDTH / PADDLE_Y
        Paddle geometry.
    INITIAL_LIVES
        Starting life count.
    MAX_SPEED_LEVEL / MIN_SPEED_LEVEL
        Speed-level range (1-5).
    """

    # --- Geometry constants ------------------------------------------------
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 24
    PLAY_LEFT = 1
    PLAY_RIGHT = 78
    PLAY_TOP = 3
    PLAY_BOTTOM = 22

    BRICK_WIDTH = 6
    BRICK_HEIGHT = 1
    BRICK_GAP = 1
    BRICKS_PER_ROW = 10
    BRICK_ROWS = 5
    BRICK_TOP_Y = 5

    PADDLE_WIDTH = 8
    PADDLE_Y = PLAY_BOTTOM - 1

    INITIAL_LIVES = 3
    MAX_SPEED_LEVEL = 5
    MIN_SPEED_LEVEL = 1

    # --- Bilingual UI strings ----------------------------------------------
    TEXTS: dict[str, dict[str, Any]] = {
        "zh": {
            "score": "分数",
            "lives": "生命",
            "level": "关卡",
            "speed": "速度",
            "sound_on": "音效: 开",
            "sound_off": "音效: 关",
            "paused": "游戏暂停",
            "pause_hint": "按 P 继续",
            "game_over": "游戏结束",
            "victory": "恭喜通关！",
            "final_score": "最终得分",
            "high_scores": "最高分",
            "rank": "排名",
            "name": "姓名",
            "score_col": "分数",
            "date": "日期",
            "press_r": "按 R 重新开始",
            "press_h": "按 H 查看帮助",
            "enter_name": "请输入你的名字",
            "new_high_score": "新纪录！",
            "controls_title": "操作说明",
            "no_scores": "暂无记录",
            "controls": [
                "← → : 移动挡板",
                "空格 : 发射球",
                "P    : 暂停/继续",
                "L    : 切换语言",
                "S    : 音效开关",
                "=/-  : 加速/减速",
                "H    : 帮助",
                "R    : 重新开始",
                "Q    : 退出",
            ],
            "close_hint": "按任意键关闭",
        },
        "en": {
            "score": "Score",
            "lives": "Lives",
            "level": "Level",
            "speed": "Speed",
            "sound_on": "Sound: ON",
            "sound_off": "Sound: OFF",
            "paused": "PAUSED",
            "pause_hint": "Press P to resume",
            "game_over": "GAME OVER",
            "victory": "VICTORY!",
            "final_score": "Final Score",
            "high_scores": "High Scores",
            "rank": "Rank",
            "name": "Name",
            "score_col": "Score",
            "date": "Date",
            "press_r": "Press R to restart",
            "press_h": "Press H for help",
            "enter_name": "Enter your name",
            "new_high_score": "New High Score!",
            "controls_title": "Controls",
            "no_scores": "No scores yet",
            "controls": [
                "← → : Move Paddle",
                "Space: Launch Ball",
                "P    : Pause/Resume",
                "L    : Toggle Language",
                "S    : Toggle Sound",
                "=/-  : Speed Up/Down",
                "H    : Help",
                "R    : Restart",
                "Q    : Quit",
            ],
            "close_hint": "Press any key to close",
        },
    }

    # --- Speed-level → tick delay (seconds) --------------------------------
    SPEED_DELAYS: dict[int, float] = {
        1: 0.080,
        2: 0.065,
        3: 0.050,
        4: 0.035,
        5: 0.020,
    }

    # ======================================================================
    # Construction & reset
    # ======================================================================

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Reset all game state to initial values."""
        self.lives = self.INITIAL_LIVES
        self.score = 0
        self.level = 1
        self.speed_level = 1
        self.language: str = "zh"
        self.sound_enabled: bool = True
        self.paused: bool = False
        self.game_over: bool = False
        self.victory: bool = False
        self.ball_attached: bool = True

        # Paddle
        self.paddle_x: int = (self.SCREEN_WIDTH - self.PADDLE_WIDTH) // 2

        # Ball (attached to paddle centre)
        self.ball_x: float = float(self.paddle_x + self.PADDLE_WIDTH // 2)
        self.ball_y: float = float(self.PADDLE_Y - 1)
        self.ball_dx: float = 0.0
        self.ball_dy: float = -1.0

        # Bricks
        self.bricks: list[Brick] = self._create_bricks()

    # ======================================================================
    # Brick creation
    # ======================================================================

    def _create_bricks(self) -> list[Brick]:
        """Build the 5×10 brick grid.

        Each row is a different colour (rainbow: red, orange, yellow, green,
        blue from top to bottom).  Colour indices 1-5 map to curses colour
        pairs in the renderer.
        """
        bricks: list[Brick] = []
        total_w = self.BRICKS_PER_ROW * self.BRICK_WIDTH + (
            self.BRICKS_PER_ROW - 1
        ) * self.BRICK_GAP
        start_x = (self.SCREEN_WIDTH - total_w) // 2
        colours = [1, 2, 3, 4, 5]  # red, orange, yellow, green, blue

        for row in range(self.BRICK_ROWS):
            y = self.BRICK_TOP_Y + row * (self.BRICK_HEIGHT + self.BRICK_GAP)
            for col in range(self.BRICKS_PER_ROW):
                x = start_x + col * (self.BRICK_WIDTH + self.BRICK_GAP)
                bricks.append(Brick(x, y, self.BRICK_WIDTH, colours[row], row))
        return bricks

    # ======================================================================
    # Queries
    # ======================================================================

    @property
    def remaining_bricks(self) -> int:
        """Number of bricks still standing."""
        return sum(1 for b in self.bricks if not b.destroyed)

    @property
    def tick_delay(self) -> float:
        """Current frame delay in seconds based on speed level."""
        return self.SPEED_DELAYS.get(self.speed_level, 0.080)

    # ------------------------------------------------------------------
    # Localised text helpers
    # ------------------------------------------------------------------

    def get_text(self, key: str) -> str:
        """Return a localised string for *key*."""
        return self.TEXTS[self.language][key]  # type: ignore[return-value]

    def get_texts(self, key: str) -> list[str]:
        """Return a localised list of strings for *key*."""
        return self.TEXTS[self.language][key]  # type: ignore[return-value]

    # ======================================================================
    # Player actions
    # ======================================================================

    def toggle_language(self) -> None:
        """Switch between Chinese and English."""
        self.language = "en" if self.language == "zh" else "zh"

    def toggle_sound(self) -> None:
        """Enable / disable terminal bell."""
        self.sound_enabled = not self.sound_enabled

    def toggle_pause(self) -> None:
        """Pause or resume the game (no-op during game-over / victory)."""
        if not self.game_over and not self.victory:
            self.paused = not self.paused

    def move_paddle(self, direction: int) -> None:
        """Move paddle left (-1) or right (+1).

        The ball follows the paddle while attached.
        """
        if self.game_over or self.victory or self.paused:
            return
        new_x = self.paddle_x + direction
        if new_x >= self.PLAY_LEFT + 1 and new_x + self.PADDLE_WIDTH <= self.PLAY_RIGHT:
            self.paddle_x = new_x
            if self.ball_attached:
                self.ball_x = float(self.paddle_x + self.PADDLE_WIDTH // 2)

    def launch_ball(self) -> None:
        """Detach the ball from the paddle and set it in motion."""
        if self.ball_attached and not self.game_over and not self.victory and not self.paused:
            self.ball_attached = False
            self.ball_dx = 0.0
            self.ball_dy = -1.0

    def increase_speed(self) -> None:
        """Raise speed level (max 5)."""
        self.speed_level = min(self.MAX_SPEED_LEVEL, self.speed_level + 1)

    def decrease_speed(self) -> None:
        """Lower speed level (min 1)."""
        self.speed_level = max(self.MIN_SPEED_LEVEL, self.speed_level - 1)

    def next_level(self) -> None:
        """Advance to the next level, recreating bricks and resetting the ball."""
        self.level += 1
        self.victory = False
        self._reset_ball()
        self.bricks = self._create_bricks()
        if self.speed_level < self.MAX_SPEED_LEVEL:
            self.speed_level += 1

    # ======================================================================
    # Game-loop update
    # ======================================================================

    def update(self) -> list[str]:
        """Advance the simulation by one tick.

        Returns a list of event strings that occurred this tick:
        ``"paddle_hit"``, ``"brick_hit"``, ``"life_lost"``, ``"game_over"``,
        ``"victory"``.  The caller can use these to trigger sound effects.
        """
        events: list[str] = []

        if self.game_over or self.victory or self.paused or self.ball_attached:
            return events

        # Move ball
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        # Wall collisions
        self._check_wall_collision()

        # Brick collisions
        if self._check_brick_collision():
            events.append("brick_hit")

        # Paddle collision
        if self._check_paddle_collision():
            events.append("paddle_hit")

        # Ball fell below paddle?
        if int(self.ball_y) >= self.PLAY_BOTTOM:
            self.lives -= 1
            events.append("life_lost")
            if self.lives <= 0:
                self.game_over = True
                events.append("game_over")
            else:
                self._reset_ball()

        # All bricks destroyed → victory
        if self.remaining_bricks == 0:
            self.victory = True
            events.append("victory")

        return events

    # ======================================================================
    # Internal helpers
    # ======================================================================

    def _check_wall_collision(self) -> None:
        """Bounce the ball off the play-area walls."""
        if self.ball_x <= self.PLAY_LEFT + 1:
            self.ball_x = float(self.PLAY_LEFT + 1)
            self.ball_dx = -self.ball_dx
        elif self.ball_x >= self.PLAY_RIGHT - 1:
            self.ball_x = float(self.PLAY_RIGHT - 1)
            self.ball_dx = -self.ball_dx

        if self.ball_y <= self.PLAY_TOP + 1:
            self.ball_y = float(self.PLAY_TOP + 1)
            self.ball_dy = -self.ball_dy

    def _check_brick_collision(self) -> bool:
        """Detect and handle ball-brick collisions.

        Returns True if any brick was hit.
        """
        bx, by = int(self.ball_x), int(self.ball_y)
        for brick in self.bricks:
            if brick.destroyed:
                continue
            if brick.contains(bx, by):
                brick.destroyed = True
                self.score += brick.points
                self.ball_dy = -self.ball_dy
                return True
        return False

    def _check_paddle_collision(self) -> bool:
        """Detect and handle ball-paddle collision.

        The ball's horizontal direction depends on where it hits the paddle:
        left third → dx = -1, centre third → dx = 0, right third → dx = +1.
        Returns True if the paddle was hit.
        """
        if (
            self.PADDLE_Y - 1 <= int(self.ball_y) <= self.PADDLE_Y
            and self.ball_dy > 0
            and self.paddle_x <= int(self.ball_x) <= self.paddle_x + self.PADDLE_WIDTH - 1
        ):
            hit_pos = int(self.ball_x) - self.paddle_x
            third = self.PADDLE_WIDTH // 3  # 2 (since 8 // 3 = 2)

            if hit_pos < third:
                self.ball_dx = -1.0
            elif hit_pos < self.PADDLE_WIDTH - third:
                self.ball_dx = 0.0
            else:
                self.ball_dx = 1.0

            self.ball_dy = -1.0
            self.ball_y = float(self.PADDLE_Y - 1)
            return True
        return False

    def _reset_ball(self) -> None:
        """Re-attach the ball to the paddle after losing a life."""
        self.ball_attached = True
        self.ball_x = float(self.paddle_x + self.PADDLE_WIDTH // 2)
        self.ball_y = float(self.PADDLE_Y - 1)
        self.ball_dx = 0.0
        self.ball_dy = -1.0
