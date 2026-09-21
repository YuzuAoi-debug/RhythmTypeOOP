import os
import sys
from typing import Optional
import pygame

from global_state import GlobalState, get_fps_target
from game_manager import GameManager
from main_menu import MainMenu
from song_select import SongSelect
from beatmap_importer import BeatmapImporter

def main(file_to_import: Optional[str] = None):
    # Check CLI arguments if not explicitly passed
    if not file_to_import and len(sys.argv) > 1:
        arg = sys.argv[1].strip()
        if os.path.exists(arg):
            file_to_import = arg

    # Pre-initialize Pygame mixer for low-latency audio playback
    try:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    except Exception:
        pass

    pygame.init()
    
    try:
        pygame.mixer.set_num_channels(32)
    except Exception:
        pass

    WIDTH, HEIGHT = 1280, 720

    # Set window / taskbar icon
    if os.path.exists(GlobalState.ICON_PATH):
        try:
            icon_surf = pygame.image.load(GlobalState.ICON_PATH)
            pygame.display.set_icon(icon_surf)
        except Exception:
            pass

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("RhythmType - Pure Python Edition")
    
    # State Machine Router
    current_state = "menu"
    
    # If a beatmap file was passed to open, import it and go straight to song select
    if file_to_import:
        imported = BeatmapImporter.import_file(file_to_import)
        if imported:
            current_state = "song_select"
    
    running = True
    while running:
        if current_state == "menu":
            menu = MainMenu(screen)
            current_state = menu.run()
        elif current_state == "song_select":
            song_select = SongSelect(screen)
            current_state = song_select.run()
        elif current_state == "play":
            game_manager = GameManager(screen)
            current_state = game_manager.run()
        elif current_state == "retry":
            current_state = "play"
        elif current_state == "quit":
            running = False
        else:
            current_state = "menu"

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()