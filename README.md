# RhythmType - Pure Python Edition

A rhythm-typing hybrid game built with Python and Pygame. It combines the scrolling-note mechanics of traditional rhythm games with the keyboard-driven flow of typing tests, featuring dynamic Unstable Rate (UR) tracking, live audio synchronization, and osu!lazer-inspired UI aesthetics.

---

## Features

- **Rhythm & Typing Mechanics:** Type characters to the rhythm of hit objects parsed from `.osu` beatmaps.
- **Dynamic 3–6 Letter Word Engine:** Powered by a curated vocabulary of 1,300+ easy, familiar English words for instant, offline, zero-latency word generation.
- **Monkeytype-Style HUD:** Clean visual display showing the current active word (with typed letters highlighted in green) and upcoming words in the measure.
- **Dynamic Sound Effects:** Real-time hitsounds on valid keystrokes and miss sounds on wrong keys/timing misses with 32 mixer channels.
- **Audio & Timing Conductor:** Sub-millisecond monotonic pause-safe time tracker with hardware audio delay calibration and custom audio offset.
- **Unstable Rate (UR) & Grade Judgements:** Real-time $O(1)$ standard deviation error tracking with SS, S, A, B, C, D grading.
- **Interactive Options Menu:** Real-time draggable sliders for Music and Sound Effects volume, note speed tuning, audio offset (-100ms to +100ms), and frame rate settings with automatic `settings.json` persistence.
- **Track Selection & Hero Previews:** Accordion song selection with mouse wheel support, all 8 difficulties, and high-resolution album art preview cards.

---

## Requirements

- Python 3.8+
- Pygame or Pygame-ce (`pip install pygame-ce` or `pip install pygame`)

---

## Folder Structure

```
RhythmType/
├── main.py                     # Main root entry point
├── README.md
├── gameplay_audio/
│   ├── hitsound.wav            # Key hit sound effect
│   └── miss-sound.wav          # Mistype and timing miss sound effect
├── scripts/
│   ├── beatmap_parser.py       # Reads .osu beatmap hit objects
│   ├── conductor.py            # Audio playback and pause synchronization
│   ├── game_manager.py         # Core gameplay loop, note rendering, input handling
│   ├── global_state.py         # Global settings and path resolution
│   ├── main_entry_point.py     # State machine router
│   ├── main_menu.py            # Main menu and interactive options overlay
│   ├── song_select.py          # Scrollable song and difficulty browser
│   └── word_generator.py       # Curated 3-6 letter dictionary and API word generator
└── assets/
    └── audio/
        └── music/
            ├── fennel_confess/ # Fennel - confess (audio + difficulties)
            └── moonshot/       # Hoshimachi Suisei - Moonshot (audio + difficulties)
```

---

## How to Play

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd RhythmTypeOOP-main
   ```

2. Install dependencies:
   ```bash
   pip install pygame-ce
   ```

3. Run the game:
   ```bash
   python main.py
   ```

4. **Controls:**
   - **Main Menu / Song Select:** Mouse Click to navigate, Mouse Wheel to scroll song list, `ESC` to return.
   - **Gameplay:** Type the letters shown on the approaching note tiles as they reach the target ring.
   - **Pause:** Press `ESC` to pause/resume during gameplay. Press `Ctrl + R` to retry the current track.