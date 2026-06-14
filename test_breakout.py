"""Pytest tests for BreakoutGame (pure game logic, no curses).

Run with::

    python -m pytest test_breakout.py -v
"""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from breakout_game import BreakoutGame, Brick
from scores import ScoreManager, ScoreEntry


# ======================================================================
# Brick tests
# ======================================================================


class TestBrick:
    def test_contains(self) -> None:
        brick = Brick(x=10, y=5, width=6, color_index=1, row=0)
        assert brick.contains(10, 5)
        assert brick.contains(15, 5)
        assert not brick.contains(9, 5)
        assert not brick.contains(16, 5)
        assert not brick.contains(10, 4)
        assert not brick.contains(10, 6)

    def test_points_by_row(self) -> None:
        """Bottom row (4) → 10 pts, top row (0) → 50 pts."""
        assert Brick(x=0, y=0, width=6, color_index=1, row=4).points == 10
        assert Brick(x=0, y=0, width=6, color_index=1, row=3).points == 20
        assert Brick(x=0, y=0, width=6, color_index=1, row=2).points == 30
        assert Brick(x=0, y=0, width=6, color_index=1, row=1).points == 40
        assert Brick(x=0, y=0, width=6, color_index=1, row=0).points == 50

    def test_destroyed_default(self) -> None:
        brick = Brick(x=0, y=0, width=6, color_index=1, row=0)
        assert not brick.destroyed


# ======================================================================
# BreakoutGame tests
# ======================================================================


class TestBreakoutGameInitialState:
    def test_initial_lives(self) -> None:
        game = BreakoutGame()
        assert game.lives == 3

    def test_initial_score(self) -> None:
        game = BreakoutGame()
        assert game.score == 0

    def test_initial_level(self) -> None:
        game = BreakoutGame()
        assert game.level == 1

    def test_initial_speed_level(self) -> None:
        game = BreakoutGame()
        assert game.speed_level == 1

    def test_initial_language_chinese(self) -> None:
        game = BreakoutGame()
        assert game.language == "zh"

    def test_initial_sound_enabled(self) -> None:
        game = BreakoutGame()
        assert game.sound_enabled is True

    def test_initial_paused_false(self) -> None:
        game = BreakoutGame()
        assert game.paused is False

    def test_initial_game_over_false(self) -> None:
        game = BreakoutGame()
        assert game.game_over is False

    def test_initial_victory_false(self) -> None:
        game = BreakoutGame()
        assert game.victory is False

    def test_initial_ball_attached(self) -> None:
        game = BreakoutGame()
        assert game.ball_attached is True

    def test_initial_paddle_position(self) -> None:
        game = BreakoutGame()
        assert game.paddle_x == (80 - 8) // 2  # 36

    def test_initial_ball_on_paddle(self) -> None:
        game = BreakoutGame()
        assert game.ball_y == game.PADDLE_Y - 1
        assert game.ball_x == game.paddle_x + game.PADDLE_WIDTH // 2

    def test_brick_count(self) -> None:
        game = BreakoutGame()
        assert len(game.bricks) == 50  # 5 rows × 10 columns

    def test_remaining_bricks(self) -> None:
        game = BreakoutGame()
        assert game.remaining_bricks == 50


class TestBreakoutGamePaddle:
    def test_move_left(self) -> None:
        game = BreakoutGame()
        game.move_paddle(-1)
        assert game.paddle_x == 35

    def test_move_right(self) -> None:
        game = BreakoutGame()
        game.move_paddle(1)
        assert game.paddle_x == 37

    def test_move_left_boundary(self) -> None:
        game = BreakoutGame()
        game.paddle_x = game.PLAY_LEFT + 1
        game.move_paddle(-1)
        assert game.paddle_x == game.PLAY_LEFT + 1  # no movement

    def test_move_right_boundary(self) -> None:
        game = BreakoutGame()
        game.paddle_x = game.PLAY_RIGHT - game.PADDLE_WIDTH
        game.move_paddle(1)
        assert game.paddle_x == game.PLAY_RIGHT - game.PADDLE_WIDTH  # no movement

    def test_move_when_game_over(self) -> None:
        game = BreakoutGame()
        game.game_over = True
        game.move_paddle(-1)
        assert game.paddle_x == (80 - 8) // 2  # unchanged

    def test_move_when_victory(self) -> None:
        game = BreakoutGame()
        game.victory = True
        game.move_paddle(1)
        assert game.paddle_x == (80 - 8) // 2  # unchanged

    def test_move_when_paused(self) -> None:
        game = BreakoutGame()
        game.paused = True
        game.move_paddle(-1)
        assert game.paddle_x == (80 - 8) // 2  # unchanged

    def test_ball_follows_paddle_when_attached(self) -> None:
        game = BreakoutGame()
        game.move_paddle(1)
        assert game.ball_x == game.paddle_x + game.PADDLE_WIDTH // 2


class TestBreakoutGameBall:
    def test_launch_ball(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        assert game.ball_attached is False
        assert game.ball_dy == -1.0
        assert game.ball_dx == 0.0

    def test_launch_when_game_over(self) -> None:
        game = BreakoutGame()
        game.game_over = True
        game.launch_ball()
        assert game.ball_attached is True  # unchanged

    def test_launch_when_victory(self) -> None:
        game = BreakoutGame()
        game.victory = True
        game.launch_ball()
        assert game.ball_attached is True  # unchanged

    def test_launch_when_paused(self) -> None:
        game = BreakoutGame()
        game.paused = True
        game.launch_ball()
        assert game.ball_attached is True  # unchanged

    def test_launch_already_launched(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        game.launch_ball()  # second call should be no-op
        assert game.ball_attached is False

    def test_update_noop_when_attached(self) -> None:
        game = BreakoutGame()
        events = game.update()
        assert events == []
        assert game.ball_attached is True

    def test_update_noop_when_game_over(self) -> None:
        game = BreakoutGame()
        game.game_over = True
        events = game.update()
        assert events == []

    def test_update_noop_when_victory(self) -> None:
        game = BreakoutGame()
        game.victory = True
        events = game.update()
        assert events == []

    def test_update_noop_when_paused(self) -> None:
        game = BreakoutGame()
        game.paused = True
        events = game.update()
        assert events == []

    def test_ball_moves_up_on_update(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        initial_y = game.ball_y
        game.update()
        assert game.ball_y < initial_y  # ball moves up (dy = -1)

    def test_ball_wall_bounce_left(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        game.ball_x = float(game.PLAY_LEFT + 1)
        game.ball_dx = -1.0
        game.update()
        assert game.ball_dx > 0  # reversed direction

    def test_ball_wall_bounce_right(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        game.ball_x = float(game.PLAY_RIGHT - 1)
        game.ball_dx = 1.0
        game.update()
        assert game.ball_dx < 0  # reversed direction

    def test_ball_wall_bounce_top(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        game.ball_y = float(game.PLAY_TOP + 1)
        game.ball_dy = -1.0
        game.update()
        assert game.ball_dy > 0  # reversed direction


class TestBreakoutGamePaddleCollision:
    def test_paddle_collision_center(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        # Position ball directly above paddle center
        game.ball_x = float(game.paddle_x + game.PADDLE_WIDTH // 2)
        game.ball_y = float(game.PADDLE_Y - 1)
        game.ball_dx = 0.0
        game.ball_dy = 1.0  # moving down
        game.update()
        # Should bounce up, dx = 0 (center hit)
        assert game.ball_dy == -1.0
        assert game.ball_dx == 0.0

    def test_paddle_collision_left(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        # Position ball at left edge of paddle
        game.ball_x = float(game.paddle_x)
        game.ball_y = float(game.PADDLE_Y - 1)
        game.ball_dx = 0.0
        game.ball_dy = 1.0
        game.update()
        assert game.ball_dy == -1.0
        assert game.ball_dx == -1.0  # bounces left

    def test_paddle_collision_right(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        # Position ball at right edge of paddle
        game.ball_x = float(game.paddle_x + game.PADDLE_WIDTH - 1)
        game.ball_y = float(game.PADDLE_Y - 1)
        game.ball_dx = 0.0
        game.ball_dy = 1.0
        game.update()
        assert game.ball_dy == -1.0
        assert game.ball_dx == 1.0  # bounces right

    def test_paddle_collision_event(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        game.ball_x = float(game.paddle_x + game.PADDLE_WIDTH // 2)
        game.ball_y = float(game.PADDLE_Y - 1)
        game.ball_dx = 0.0
        game.ball_dy = 1.0
        events = game.update()
        assert "paddle_hit" in events


class TestBreakoutGameBrickCollision:
    def test_brick_destroyed_on_hit(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        # Position ball one step above the first brick (ball moves *before* collision)
        brick = game.bricks[0]
        game.ball_x = float(brick.x)
        game.ball_y = float(brick.y - 1)
        game.ball_dx = 0.0
        game.ball_dy = 1.0  # moving down into brick
        events = game.update()
        assert brick.destroyed
        assert "brick_hit" in events

    def test_brick_points_added_to_score(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        brick = game.bricks[0]
        points = brick.points
        game.ball_x = float(brick.x)
        game.ball_y = float(brick.y - 1)
        game.ball_dx = 0.0
        game.ball_dy = 1.0
        game.update()
        assert game.score == points

    def test_brick_bounces_ball(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        brick = game.bricks[0]
        game.ball_x = float(brick.x)
        game.ball_y = float(brick.y - 1)
        game.ball_dx = 0.0
        game.ball_dy = 1.0
        game.update()
        assert game.ball_dy == -1.0  # bounced back up

    def test_destroyed_brick_not_hit_again(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        brick = game.bricks[0]
        brick.destroyed = True
        game.ball_x = float(brick.x)
        game.ball_y = float(brick.y)
        game.ball_dx = 0.0
        game.ball_dy = 1.0
        events = game.update()
        assert "brick_hit" not in events

    def test_remaining_bricks_decreases(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        brick = game.bricks[0]
        game.ball_x = float(brick.x)
        game.ball_y = float(brick.y - 1)
        game.ball_dx = 0.0
        game.ball_dy = 1.0
        before = game.remaining_bricks
        game.update()
        assert game.remaining_bricks == before - 1


class TestBreakoutGameLives:
    def test_lose_life_when_ball_falls(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        # Position ball just above paddle so it passes through paddle
        game.ball_x = float(game.paddle_x + game.PADDLE_WIDTH // 2)
        game.ball_y = float(game.PADDLE_Y)
        game.ball_dx = 0.0
        game.ball_dy = 1.0
        events = game.update()
        assert game.lives == 2
        assert "life_lost" in events

    def test_game_over_when_no_lives(self) -> None:
        game = BreakoutGame()
        game.lives = 1
        game.launch_ball()
        game.ball_x = float(game.paddle_x + game.PADDLE_WIDTH // 2)
        game.ball_y = float(game.PADDLE_Y)
        game.ball_dx = 0.0
        game.ball_dy = 1.0
        events = game.update()
        assert game.lives == 0
        assert game.game_over
        assert "game_over" in events

    def test_ball_resets_after_life_lost(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        game.ball_x = float(game.paddle_x + game.PADDLE_WIDTH // 2)
        game.ball_y = float(game.PADDLE_Y)
        game.ball_dx = 0.0
        game.ball_dy = 1.0
        game.update()
        assert game.ball_attached is True
        assert game.ball_y == game.PADDLE_Y - 1


class TestBreakoutGameVictory:
    def test_victory_when_all_bricks_destroyed(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        # Destroy all bricks
        for brick in game.bricks:
            brick.destroyed = True
        events = game.update()
        assert game.victory
        assert "victory" in events

    def test_next_level(self) -> None:
        game = BreakoutGame()
        game.next_level()
        assert game.level == 2
        assert game.speed_level == 2
        assert game.ball_attached is True
        assert len(game.bricks) == 50
        assert game.remaining_bricks == 50

    def test_next_level_speed_cap(self) -> None:
        game = BreakoutGame()
        game.speed_level = 5
        game.next_level()
        assert game.speed_level == 5  # capped


class TestBreakoutGameToggles:
    def test_toggle_language(self) -> None:
        game = BreakoutGame()
        assert game.language == "zh"
        game.toggle_language()
        assert game.language == "en"
        game.toggle_language()
        assert game.language == "zh"

    def test_toggle_sound(self) -> None:
        game = BreakoutGame()
        assert game.sound_enabled is True
        game.toggle_sound()
        assert game.sound_enabled is False
        game.toggle_sound()
        assert game.sound_enabled is True

    def test_toggle_pause(self) -> None:
        game = BreakoutGame()
        assert game.paused is False
        game.toggle_pause()
        assert game.paused is True
        game.toggle_pause()
        assert game.paused is False

    def test_toggle_pause_noop_when_game_over(self) -> None:
        game = BreakoutGame()
        game.game_over = True
        game.toggle_pause()
        assert game.paused is False

    def test_toggle_pause_noop_when_victory(self) -> None:
        game = BreakoutGame()
        game.victory = True
        game.toggle_pause()
        assert game.paused is False


class TestBreakoutGameSpeed:
    def test_increase_speed(self) -> None:
        game = BreakoutGame()
        game.increase_speed()
        assert game.speed_level == 2

    def test_decrease_speed(self) -> None:
        game = BreakoutGame()
        game.speed_level = 3
        game.decrease_speed()
        assert game.speed_level == 2

    def test_increase_speed_max(self) -> None:
        game = BreakoutGame()
        game.speed_level = 5
        game.increase_speed()
        assert game.speed_level == 5

    def test_decrease_speed_min(self) -> None:
        game = BreakoutGame()
        game.decrease_speed()
        assert game.speed_level == 1

    def test_tick_delay_decreases_with_speed(self) -> None:
        game = BreakoutGame()
        d1 = game.tick_delay
        game.increase_speed()
        d2 = game.tick_delay
        assert d2 < d1


class TestBreakoutGameReset:
    def test_reset_restores_initial_state(self) -> None:
        game = BreakoutGame()
        game.launch_ball()
        game.score = 100
        game.lives = 1
        game.level = 3
        game.reset()
        assert game.lives == 3
        assert game.score == 0
        assert game.level == 1
        assert game.ball_attached is True
        assert game.game_over is False
        assert game.victory is False

    def test_reset_recreates_bricks(self) -> None:
        game = BreakoutGame()
        game.bricks = []
        game.reset()
        assert len(game.bricks) == 50


class TestBreakoutGameText:
    def test_get_text_chinese(self) -> None:
        game = BreakoutGame()
        assert game.get_text("score") == "分数"

    def test_get_text_english(self) -> None:
        game = BreakoutGame()
        game.toggle_language()
        assert game.get_text("score") == "Score"

    def test_get_texts_controls_zh(self) -> None:
        game = BreakoutGame()
        controls = game.get_texts("controls")
        assert len(controls) == 9
        assert "← → : 移动挡板" in controls

    def test_get_texts_controls_en(self) -> None:
        game = BreakoutGame()
        game.toggle_language()
        controls = game.get_texts("controls")
        assert "← → : Move Paddle" in controls


# ======================================================================
# ScoreManager tests
# ======================================================================


class TestScoreManager:
    def test_add_and_retrieve(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("[]")
            tmp = f.name
        try:
            mgr = ScoreManager(tmp)
            mgr.add_score(100, "Alice")
            mgr.add_score(200, "Bob")
            top = mgr.top_scores()
            assert len(top) == 2
            assert top[0].score == 200
            assert top[1].score == 100
        finally:
            os.unlink(tmp)

    def test_is_high_score_empty(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("[]")
            tmp = f.name
        try:
            mgr = ScoreManager(tmp)
            assert mgr.is_high_score(0) is True
        finally:
            os.unlink(tmp)

    def test_is_high_score_below_min(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("[]")
            tmp = f.name
        try:
            mgr = ScoreManager(tmp)
            # Fill with 10 scores of 100
            for _ in range(10):
                mgr.add_score(100)
            assert mgr.is_high_score(50) is False
            assert mgr.is_high_score(150) is True
        finally:
            os.unlink(tmp)

    def test_max_scores_capped(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("[]")
            tmp = f.name
        try:
            mgr = ScoreManager(tmp)
            for i in range(15):
                mgr.add_score(i)
            assert len(mgr.top_scores()) == 10
        finally:
            os.unlink(tmp)

    def test_clear(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("[]")
            tmp = f.name
        try:
            mgr = ScoreManager(tmp)
            mgr.add_score(100)
            mgr.clear()
            assert mgr.top_scores() == []
        finally:
            os.unlink(tmp)

    def test_load_from_file(self) -> None:
        data = [
            {"score": 300, "name": "Charlie", "date": "2024-01-01"},
            {"score": 200, "name": "Diana", "date": "2024-01-02"},
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            tmp = f.name
        try:
            mgr = ScoreManager(tmp)
            top = mgr.top_scores()
            assert len(top) == 2
            assert top[0].score == 300
            assert top[1].name == "Diana"
        finally:
            os.unlink(tmp)

    def test_corrupt_file_silent(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("not json")
            tmp = f.name
        try:
            mgr = ScoreManager(tmp)
            assert mgr.top_scores() == []
        finally:
            os.unlink(tmp)

    def test_missing_file_silent(self) -> None:
        mgr = ScoreManager("/tmp/__nonexistent_scores_file__.json")
        assert mgr.top_scores() == []


class TestScoreEntry:
    def test_to_dict(self) -> None:
        entry = ScoreEntry(100, "Test", "2024-06-15")
        d = entry.to_dict()
        assert d == {"score": 100, "name": "Test", "date": "2024-06-15"}

    def test_from_dict(self) -> None:
        entry = ScoreEntry.from_dict({"score": 50, "name": "Foo", "date": "2024-01-01"})
        assert entry.score == 50
        assert entry.name == "Foo"
        assert entry.date == "2024-01-01"
