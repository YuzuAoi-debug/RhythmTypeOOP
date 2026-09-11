STREAMING_CHUNK:Writing project README...

RhythmType - Pure Python Edition

A rhythm-typing hybrid game built entirely from scratch using Python and Pygame. It combines the falling-note mechanics of traditional rhythm games with the keyboard-driven flow of typing tests, featuring dynamic Unstable Rate (UR) tracking and osu!lazer inspired UI aesthetics.

Requirements

Python 3.8+

Pygame (pip install pygame)

Folder Structure setup for GitHub

To run this project, make sure you set up the following directory structure in your repository:

RhythmType/
├── main.py
├── game_manager.py
├── main_menu.py
├── song_select.py
├── conductor.py
├── global_state.py
├── beatmap_parser.py
├── .gitignore
├── README.md
└── assets/
    ├── audio/
    │   └── test.mp3      <-- Add a valid MP3 file here
    └── beatmaps/
        └── test.osu      <-- Add a valid OSU beatmap file here


How to Play

Clone the repository.

Install pygame: pip install pygame

Add a test.mp3 and test.osu into their respective folders in assets/.

Run python main.py!