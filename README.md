# RhythmType

A rhythm-typing hybrid game built with Python and Pygame. It combines the scrolling-note mechanics of traditional rhythm games with the keyboard-driven flow of typing tests, featuring dynamic Unstable Rate (UR) tracking, live audio synchronization, and an osu!lazer-inspired UI.

---

## Features

- **Rhythm & Typing Mechanics:** Type characters to the beat of hit objects parsed from `.osu` beatmaps.
- **Dynamic 3–6 Letter Word Engine:** Powered by a curated vocabulary of 1,300+ easy, familiar English words for instant offline word generation with zero latency.
- **Monkeytype-Style HUD:** Clean visual display showing the active word (typed letters highlighted in green) alongside upcoming words in the measure.
- **Dynamic Sound Effects:** Real-time hitsounds on valid keystrokes and miss sounds on wrong keys or timing misses with 32 mixer channels.
- **Audio & Timing Conductor:** Sub-millisecond monotonic pause-safe time tracker with hardware audio delay calibration and custom audio offset (±200 ms).
- **Unstable Rate (UR) & Grade Judgements:** Real-time O(1) standard deviation error tracking with SS, S, A, B, C, D grading.
- **Game Mods:** NF (No Fail), HR (Hard Rock), SD (Sudden Death), PF (Perfect), and DT (Double Time) — each with its own score multiplier.
- **Interactive Options Menu:** Real-time draggable sliders for Music/SFX volume, note speed, audio offset, background brightness, and frame rate — automatically persisted to `settings.json`.
- **Track Selection & Hero Previews:** Accordion song selector with mouse wheel support and high-resolution album art preview cards.
- **Dynamic Song Library:** Auto-scans `assets/audio/music/` at startup — drop in any beatmap folder and it appears automatically.
- **Beatmap Importer:** Drag-and-drop (or double-click) `.osz` / `.osu` files to import them directly into the library. Includes a `register_file_association.bat` helper for Windows file-type registration.

---

## Requirements

- Python 3.8+
- `pygame` or `pygame-ce`
- `numpy`

Install all dependencies at once:

```bash
pip install pygame-ce numpy
```

> **Note:** `pygame-ce` (Community Edition) is preferred for its `get_current_refresh_rate` API, which enables accurate refresh-rate-locked FPS. Standard `pygame` works but will fall back to a Windows ctypes query, or 60 FPS otherwise.

---

## Installation & Running

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd RhythmTypeOOP
   ```

2. **Install dependencies:**
   ```bash
   pip install pygame-ce numpy
   ```

3. **Run the game:**
   ```bash
   python main.py
   ```
   Or use the alternate entry point:
   ```bash
   python manage.py
   ```

4. **Windows launcher:** Double-click `RhythmType.bat` to launch without a terminal window.

---

## Importing Beatmaps

RhythmType reads standard osu! beatmap files (`.osu`) and packages (`.osz`).

### Method 1 — Drop folder manually
Place any osu! song folder inside `assets/audio/music/`. The game auto-scans on startup and picks it up.

### Method 2 — Drag & drop / double-click (Windows)
1. Run `register_file_association.bat` once to associate `.osz` and `.osu` files with RhythmType.
2. Double-click any `.osz` or `.osu` file. The game launches, imports the beatmap, and navigates directly to Song Select.

### Method 3 — CLI argument
```bash
python main.py "path/to/beatmap.osz"
```

---

## Controls

| Context | Action | Input |
|---|---|---|
| Main Menu | Navigate | Mouse click |
| Song Select | Scroll song list | Mouse wheel |
| Song Select | Change difficulty | Click difficulty tab |
| Song Select | Toggle mod | Click mod button (NF / HR / SD / PF / DT) |
| Any screen | Go back | `ESC` |
| Gameplay | Type notes | Keyboard (letters on approaching tiles) |
| Gameplay | Pause / Resume | `ESC` |
| Gameplay | Retry current track | `Ctrl + R` |

---

## Folder Structure

```
RhythmTypeOOP/
├── main.py                         # Root entry point
├── manage.py                       # Alternate entry point (python manage.py)
├── RhythmType.bat                  # Windows one-click launcher
├── register_file_association.bat   # Windows .osz/.osu file-type registration
├── settings.json                   # Auto-generated user settings (persisted)
├── pyproject.toml                  # Pyright type-checker configuration
├── requirements.txt
├── README.md
├── gameplay_audio/
│   ├── hitsound.wav                # Key hit sound effect
│   ├── miss-sound.wav              # Mistype / timing miss sound effect
│   ├── hover.mp3                   # UI hover sound
│   └── click.mp3                   # UI click sound
├── scripts/
│   ├── __init__.py
│   ├── beatmap_parser.py           # Parses .osu hit objects & metadata
│   ├── beatmap_importer.py         # Imports .osz / .osu files into the library
│   ├── conductor.py                # Audio playback & pause-safe time tracking
│   ├── game_manager.py             # Core gameplay loop, note rendering, input
│   ├── global_state.py             # Global settings, paths, song library, mods
│   ├── main_entry_point.py         # State machine (menu → song_select → play)
│   ├── main_menu.py                # Main menu & options overlay
│   ├── song_select.py              # Scrollable song & difficulty browser
│   └── word_generator.py           # 3–6 letter curated dictionary & word engine
└── assets/
    ├── images/
    │   ├── logo.png
    │   └── icon.png
    ├── font/
    └── audio/
        └── music/
            └── <song folders>/     # Drop osu! song folders here
```

---

## Settings

All settings are saved automatically to `settings.json` in the project root.

| Setting | Description | Default |
|---|---|---|
| `music_volume` | Background music volume (0.0 – 1.0) | `0.8` |
| `sfx_volume` | Sound effects volume (0.0 – 1.0) | `0.8` |
| `note_speed` | Note approach speed (0.01 – 20.0) | `9.0` |
| `fps_mode` | `"refresh_rate"` / `"60fps"` / `"unlimited"` | `"refresh_rate"` |
| `audio_offset_ms` | Hardware audio delay offset (-200 – +200 ms) | `0.0` |
| `bg_brightness` | Gameplay background dim (0.0 – 1.0) | `0.4` |

---

## Game Mods

| Mod | Effect | Score Multiplier |
|---|---|---|
| **NF** — No Fail | HP cannot reach zero | ×0.50 |
| **HR** — Hard Rock | Increases difficulty | ×1.06 |
| **SD** — Sudden Death | Fail on first miss | ×1.00 |
| **PF** — Perfect | Fail on anything less than perfect | ×1.00 |
| **DT** — Double Time | Song plays at increased speed | ×1.12 |

> NF is mutually exclusive with SD/PF. SD and PF are mutually exclusive with each other.