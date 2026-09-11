import pygame
import sys
from global_state import GlobalState
from game_manager import GameManager
from main_menu import MainMenu
from song_select import SongSelect

def get_fps_target(mode: str) -> int:
    if mode == "unlimited":
        return 0
    elif mode == "60fps":
        return 60
    elif mode == "refresh_rate":
        return 60
    return 60

def main():
    pygame.init()
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