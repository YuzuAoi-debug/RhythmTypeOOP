import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Base project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

def get_asset_path(rel_path: str) -> str:
    """Resolve a relative asset path to an absolute path based on project root."""
    return str((BASE_DIR / rel_path).resolve())

def get_fps_target(mode: str) -> int:
    """Returns the target frame rate based on the active display and user setting."""
    if mode == "unlimited":
        return 0
    elif mode == "60fps":
        return 60
    elif mode == "refresh_rate":
        try:
            import pygame
            rr = pygame.display.get_current_refresh_rate()
            return int(rr) if rr and rr > 0 else 60
        except Exception:
            return 60
    return 60

SETTINGS_FILE = BASE_DIR / "settings.json"

class GlobalState:
    # Volume settings (0.0 to 1.0)
    music_volume: float = 0.8
    sfx_volume: float = 0.8
    
    # Backward compatibility aliases
    menu_volume: float = 0.8
    game_volume: float = 0.8
    
    note_speed: float = 9.0
    hp: float = 100.0
    fps_mode: str = "refresh_rate"  # "unlimited", "60fps", "refresh_rate"
    audio_offset_ms: float = 0.0     # Hardware audio delay offset (-100ms to +100ms)
    bg_brightness: float = 0.4       # Gameplay background brightness (0.0 to 1.0)
    
    # Audio file paths
    HITSOUND_PATH = get_asset_path("gameplay_audio/hitsound.wav")
    MISS_SOUND_PATH = get_asset_path("gameplay_audio/miss-sound.wav")
    HOVER_SOUND_PATH = get_asset_path("gameplay_audio/hover.mp3")
    CLICK_SOUND_PATH = get_asset_path("gameplay_audio/click.mp3")
    
    # Image file paths
    LOGO_PATH = get_asset_path("assets/images/logo.png")
    ICON_PATH = get_asset_path("assets/images/icon.png")
    
    MUSIC_DIR = BASE_DIR / "assets" / "audio" / "music"

    @staticmethod
    def get_asset_path(rel_path: str) -> str:
        return get_asset_path(rel_path)

    # Active song indices for SongSelect navigation
    selected_song_index: int = 0
    expanded_song_index: int = 0

    # Payload for the active song to play
    selected_song_data = {}
    
    # Master Song Library Database with all difficulties & background assets
    song_list: List[Dict[str, Any]] = [
        {
            "title": "Fennel - confess",
            "artist": "Fennel",
            "audio_path": get_asset_path("assets/audio/music/fennel_confess/audio.mp3"),
            "background_path": get_asset_path("assets/audio/music/fennel_confess/camera.jpeg"),
            "bpm": 130.0,
            "difficulties": [
                {"name": "Normal", "osu_path": get_asset_path("assets/audio/music/fennel_confess/normal.txt")},
                {"name": "Hard", "osu_path": get_asset_path("assets/audio/music/fennel_confess/hard.txt")},
                {"name": "Insane", "osu_path": get_asset_path("assets/audio/music/fennel_confess/insane.txt")},
                {"name": "Affection", "osu_path": get_asset_path("assets/audio/music/fennel_confess/affection.txt")}
            ]
        },
        {
            "title": "Hoshimachi Suisei - Moonshot",
            "artist": "Hoshimachi Suisei",
            "audio_path": get_asset_path("assets/audio/music/moonshot/audio.ogg"),
            "background_path": get_asset_path("assets/audio/music/moonshot/face.jpg"),
            "bpm": 168.0,
            "difficulties": [
                {"name": "Normal", "osu_path": get_asset_path("assets/audio/music/moonshot/Hoshimachi Suisei - Moonshot [Normal].txt")},
                {"name": "Hard", "osu_path": get_asset_path("assets/audio/music/moonshot/Hoshimachi Suisei - Moonshot [Hard].txt")},
                {"name": "Insane", "osu_path": get_asset_path("assets/audio/music/moonshot/Hoshimachi Suisei - Moonshot [Insane].txt")},
                {"name": "Special", "osu_path": get_asset_path("assets/audio/music/moonshot/Hoshimachi Suisei - Moonshot [Special].txt")}
            ]
        }
    ]

    @classmethod
    def scan_songs(cls):
        """Dynamically scans assets/audio/music/ directory to discover all beatmaps and difficulties."""
        if not cls.MUSIC_DIR.exists():
            return

        try:
            from beatmap_parser import BeatmapParser
            scanned = []
            for entry in sorted(cls.MUSIC_DIR.iterdir()):
                if entry.is_dir():
                    song_data = BeatmapParser.scan_song_directory(str(entry))
                    if song_data and song_data.get("difficulties"):
                        song_data["difficulties"].sort(key=lambda d: d.get("note_count", 0))
                        scanned.append(song_data)

            if scanned:
                cls.song_list = scanned
        except Exception as e:
            print(f"Warning: Error scanning songs ({e}). Using default song list.")

    @classmethod
    def load_settings(cls):
        """Load user settings from settings.json if present."""
        if not SETTINGS_FILE.exists():
            return
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            cls.music_volume = float(data.get("music_volume", cls.music_volume))
            cls.sfx_volume = float(data.get("sfx_volume", cls.sfx_volume))
            cls.menu_volume = cls.music_volume
            cls.game_volume = cls.sfx_volume
            cls.note_speed = float(data.get("note_speed", cls.note_speed))
            cls.fps_mode = str(data.get("fps_mode", cls.fps_mode))
            cls.audio_offset_ms = float(data.get("audio_offset_ms", cls.audio_offset_ms))
            cls.bg_brightness = float(data.get("bg_brightness", cls.bg_brightness))
        except Exception as e:
            print(f"Warning: Failed to load settings ({e}), using defaults.")

    @classmethod
    def save_settings(cls):
        """Save user settings to settings.json."""
        try:
            payload = {
                "music_volume": round(cls.music_volume, 2),
                "sfx_volume": round(cls.sfx_volume, 2),
                "note_speed": round(cls.note_speed, 2),
                "fps_mode": cls.fps_mode,
                "audio_offset_ms": round(cls.audio_offset_ms, 1),
                "bg_brightness": round(cls.bg_brightness, 2)
            }
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
        except Exception as e:
            print(f"Warning: Failed to save settings ({e}).")

# Auto-load existing settings and scan available beatmaps upon import
GlobalState.load_settings()
GlobalState.scan_songs()