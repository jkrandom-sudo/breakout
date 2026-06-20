# Breakout

A console-based Breakout game for the terminal, written in Python using `curses`.

## 简介

A classic brick-breaking game rendered in the terminal. Use the paddle to keep the ball in play and destroy all bricks to win. Features bilingual UI (Chinese / English), persistent high scores, adjustable game speed, and sound effects via terminal bell.

一款经典的打砖块游戏，在终端中运行。支持中文/英文双语界面、分数持久化、游戏速度调节，以及终端铃声音效。

## How to Run / 如何运行

```bash
python3 game.py
```

Requires a terminal that supports curses (Linux, macOS). Windows users may need `windows-curses`.

运行需要支持 curses 的终端（Linux、macOS）。Windows 用户可能需要安装 `windows-curses`。

## Controls / 操作说明

| Key | Action |
|---|---|
| `←` `→` | Move paddle left / right |
| `Space` | Launch ball |
| `P` | Pause / resume |
| `H` | Show help overlay |
| `L` | Toggle language (Chinese / English) |
| `S` | Toggle sound |
| `=` `+` | Increase speed |
| `-` `_` | Decrease speed |
| `R` | Restart game |
| `Q` | Quit |

## Features / 游戏特性

- **Bilingual UI** — Full Chinese and English support, switch anytime with `L`
- **Persistent high scores** — Top 10 scores saved to `scores.json`
- **5 speed levels** — Adjust with `=` / `-` keys
- **Sound effects** — Terminal bell on paddle hit, brick destroy, life lost
- **Color bricks** — 5 rows of rainbow-colored bricks (red, orange, yellow, green, blue)
- **Score by row** — Top row bricks worth more (50 pts) than bottom row (10 pts)
- **Zero dependencies** — Uses only Python standard library

## Project Structure / 项目结构

```
breakout/
├── game.py           # Entry point, main loop, input handling
├── breakout_game.py  # Pure game logic (no curses imports)
├── renderer.py       # Curses rendering layer
├── scores.py         # High-score persistence (JSON)
├── i18n.py           # Bilingual string translations
├── scores.json       # High scores file (created on first run)
└── test_breakout.py  # Unit tests for game logic
```

## Architecture / 架构

The game is cleanly separated into three layers:

1. **Game logic** (`breakout_game.py`) — Pure Python, no curses. Contains paddle, ball, bricks, collision detection, scoring, lives, level, speed, and language state. Fully unit-testable.
2. **Rendering** (`renderer.py`) — curses-only code. Subscribes to game state and draws to terminal.
3. **Entry point** (`game.py`) — Sets up curses, creates game/renderer/score instances, runs the main loop.

## Dependencies / 依赖

None. Python standard library only (`curses`, `json`, `os`, `time`, `datetime`).
