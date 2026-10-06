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
                                                  
    if not file_to_import and len(sys.argv) > 1:
        arg = sys.argv[1].strip()
        if os.path.exists(arg):
            file_to_import = arg

                                                                
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

                               
    if os.path.exists(GlobalState.ICON_PATH):
        try:
            icon_surf = pygame.image.load(GlobalState.ICON_PATH)
            pygame.display.set_icon(icon_surf)
        except Exception:
            pass

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("RhythmType - Pure Python Edition")
    
                          
    current_state = "menu"
    
                                                                                    
    if file_to_import:
        imported = BeatmapImporter.import_file(file_to_import)
        if imported:
            current_state = "song_select"
    
    running = True
    last_frame = None
    
    while running:
        active_screen = pygame.display.get_surface()
        if current_state == "menu":
            menu = MainMenu(active_screen)
            next_state = menu.run(last_frame)
            last_frame = pygame.display.get_surface().copy()
            current_state = next_state
        elif current_state == "song_select":
            song_select = SongSelect(active_screen)
            next_state = song_select.run(last_frame)
            last_frame = pygame.display.get_surface().copy()
            current_state = next_state
        elif current_state == "play":
            game_manager = GameManager(active_screen)
            next_state = game_manager.run(last_frame)
            last_frame = pygame.display.get_surface().copy()
            current_state = next_state
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