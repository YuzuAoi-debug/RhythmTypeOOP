import sys
import pygame
from global_state import GlobalState, get_fps_target
from game_manager import GameManager
from main_menu import MainMenu
from song_select import SongSelect

def main():
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
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("RhythmType - Pure Python Edition")
    
    # State Machine Router
    current_state = "menu"
    
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