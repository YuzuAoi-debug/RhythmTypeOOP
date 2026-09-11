import pygame
import random
from global_state import GlobalState

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        self.BG_COLOR = (14, 14, 18)
        self.PANEL_COLOR = (22, 22, 30)
        self.HOVER_COLOR = (40, 40, 56)
        self.ACCENT_COLOR = (0, 229, 255)
        self.TEXT_COLOR = (245, 245, 255)
        
        self.font_title = pygame.font.SysFont("Arial", 64, bold=True)
        self.font_btn = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18)
        
        self.playlist = []
        self.now_playing = ""
        self.options_open = False
        
        # Temporary settings buffer for options menu
        self.temp_speed = GlobalState.note_speed
        self.temp_menu_volume = GlobalState.menu_volume
        self.temp_game_volume = GlobalState.game_volume
        self.fps_modes = ["60fps", "refresh_rate", "unlimited"]
        self.temp_fps_mode = GlobalState.fps_mode

        pygame.mixer.init()
        # Track end of song for playlist looping
        self.SONG_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.SONG_END)
        self._play_next_song()

    def _play_next_song(self):
        if not self.playlist:
            self.playlist = GlobalState.song_list.copy()
            random.shuffle(self.playlist)
        
        if self.playlist:
            song = self.playlist.pop(0)
            self.now_playing = f"Now Playing ♫ : {song['title']}"
            try:
                pygame.mixer.music.load(song["audio_path"])
                pygame.mixer.music.set_volume(GlobalState.menu_volume)
                pygame.mixer.music.play()
            except Exception:
                self.now_playing = "Now Playing ♫ : (Audio file missing)"

    def draw_button(self, text, rect, is_hovered):
        color = self.HOVER_COLOR if is_hovered else self.PANEL_COLOR
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, self.ACCENT_COLOR if is_hovered else self.HOVER_COLOR, rect, 2, border_radius=8)
        
        surf = self.font_btn.render(text, True, self.TEXT_COLOR)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def draw_slider(self, label, value, rect, mouse_pos):
        label_surface = self.font_small.render(f"{label}  {value:.2f}", True, self.TEXT_COLOR)
        self.screen.blit(label_surface, (rect.x, rect.y - 25))
        pygame.draw.rect(self.screen, (55, 55, 70), rect, border_radius=6)
        fill_rect = pygame.Rect(rect.x, rect.y, int(rect.width * value), rect.height)
        pygame.draw.rect(self.screen, self.ACCENT_COLOR, fill_rect, border_radius=6)
        knob_x = rect.x + int(rect.width * value)
        pygame.draw.circle(self.screen, self.TEXT_COLOR, (knob_x, rect.centery), 9)
        return rect.collidepoint(mouse_pos)

    def run(self):
        clock = pygame.time.Clock()
        
        btn_width, btn_height = 300, 60
        start_y = self.height // 2
        
        # Rectangles for main menu buttons
        play_rect = pygame.Rect(100, start_y, btn_width, btn_height)
        options_rect = pygame.Rect(100, start_y + 80, btn_width, btn_height)
        exit_rect = pygame.Rect(100, start_y + 160, btn_width, btn_height)

        panel_rect = pygame.Rect(self.width // 2 - 270, self.height // 2 - 280, 540, 560)
        speed_minus_hundredth = pygame.Rect(panel_rect.x + 30, panel_rect.y + 125, 105, 48)
        speed_minus_tenth = pygame.Rect(panel_rect.x + 145, panel_rect.y + 125, 105, 48)
        speed_plus_hundredth = pygame.Rect(panel_rect.x + 290, panel_rect.y + 125, 105, 48)
        speed_plus_tenth = pygame.Rect(panel_rect.x + 405, panel_rect.y + 125, 105, 48)
        menu_slider_rect = pygame.Rect(panel_rect.x + 35, panel_rect.y + 235, 470, 14)
        game_slider_rect = pygame.Rect(panel_rect.x + 35, panel_rect.y + 305, 470, 14)
        fps_rect = pygame.Rect(panel_rect.x + 35, panel_rect.y + 365, 220, 42)
        close_opt_rect = pygame.Rect(panel_rect.x + 285, panel_rect.y + 365, 220, 42)

        running = True
        if GlobalState.fps_mode == "unlimited":
            target_fps = 0
        elif GlobalState.fps_mode == "refresh_rate":
            target_fps = 60
        else:
            target_fps = 60
        while running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == self.SONG_END:
                    self._play_next_song()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_clicked = True

            self.screen.fill(self.BG_COLOR)

            # Draw Branding & Now Playing
            title_surf = self.font_title.render("RHYTHMTYPE", True, self.TEXT_COLOR)
            self.screen.blit(title_surf, (100, 100))
            
            now_playing_surf = self.font_small.render(self.now_playing, True, self.ACCENT_COLOR)
            self.screen.blit(now_playing_surf, (100, 180))

            # Logic for Options Overlay vs Main Menu
            if self.options_open:
                # Dim background
                overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))
                
                # Options Box
                pygame.draw.rect(self.screen, self.PANEL_COLOR, panel_rect, border_radius=12)
                
                opt_title = self.font_btn.render("OPTIONS", True, self.TEXT_COLOR)
                self.screen.blit(opt_title, opt_title.get_rect(center=(self.width//2, panel_rect.y + 50)))
                
                # Speed Adjuster UI
                speed_label = self.font_small.render("Note Speed", True, self.TEXT_COLOR)
                self.screen.blit(speed_label, speed_label.get_rect(center=(self.width//2, panel_rect.y + 90)))
                
                speed_val = self.font_btn.render(f"{self.temp_speed:.2f}", True, self.ACCENT_COLOR)
                self.screen.blit(speed_val, speed_val.get_rect(center=(self.width//2, panel_rect.y + 112)))
                self.draw_button("-0.01", speed_minus_hundredth, speed_minus_hundredth.collidepoint(mouse_pos))
                self.draw_button("-0.1", speed_minus_tenth, speed_minus_tenth.collidepoint(mouse_pos))
                self.draw_button("+0.01", speed_plus_hundredth, speed_plus_hundredth.collidepoint(mouse_pos))
                self.draw_button("+0.1", speed_plus_tenth, speed_plus_tenth.collidepoint(mouse_pos))
                menu_slider_hover = self.draw_slider("Music", self.temp_menu_volume, menu_slider_rect, mouse_pos)
                game_slider_hover = self.draw_slider("Effects", self.temp_game_volume, game_slider_rect, mouse_pos)
                fps_label = self.font_small.render("Frame rate", True, self.TEXT_COLOR)
                self.screen.blit(fps_label, (fps_rect.x, fps_rect.y - 25))
                self.draw_button(self.temp_fps_mode, fps_rect, fps_rect.collidepoint(mouse_pos))
                self.draw_button("Save & Close", close_opt_rect, close_opt_rect.collidepoint(mouse_pos))
                
                if mouse_clicked:
                    if speed_minus_hundredth.collidepoint(mouse_pos):
                        self.temp_speed = max(0.01, round(self.temp_speed - 0.01, 2))
                    elif speed_minus_tenth.collidepoint(mouse_pos):
                        self.temp_speed = max(0.01, round(self.temp_speed - 0.1, 2))
                    elif speed_plus_hundredth.collidepoint(mouse_pos):
                        self.temp_speed = min(20.0, round(self.temp_speed + 0.01, 2))
                    elif speed_plus_tenth.collidepoint(mouse_pos):
                        self.temp_speed = min(20.0, round(self.temp_speed + 0.1, 2))
                    elif fps_rect.collidepoint(mouse_pos):
                        current_index = self.fps_modes.index(self.temp_fps_mode)
                        self.temp_fps_mode = self.fps_modes[(current_index + 1) % len(self.fps_modes)]
                    elif close_opt_rect.collidepoint(mouse_pos):
                        GlobalState.note_speed = self.temp_speed
                        GlobalState.menu_volume = self.temp_menu_volume
                        GlobalState.game_volume = self.temp_game_volume
                        pygame.mixer.music.set_volume(GlobalState.menu_volume)
                        GlobalState.fps_mode = self.temp_fps_mode
                        self.options_open = False

                if pygame.mouse.get_pressed()[0]:
                    if menu_slider_hover:
                        self.temp_menu_volume = max(0.0, min(1.0, (mouse_pos[0] - menu_slider_rect.x) / menu_slider_rect.width))
                    elif game_slider_hover:
                        self.temp_game_volume = max(0.0, min(1.0, (mouse_pos[0] - game_slider_rect.x) / game_slider_rect.width))
            else:
                # Main Buttons
                play_hover = play_rect.collidepoint(mouse_pos)
                opt_hover = options_rect.collidepoint(mouse_pos)
                exit_hover = exit_rect.collidepoint(mouse_pos)
                
                self.draw_button("PLAY", play_rect, play_hover)
                self.draw_button("OPTIONS", options_rect, opt_hover)
                self.draw_button("EXIT", exit_rect, exit_hover)
                
                if mouse_clicked:
                    if play_hover:
                        return "song_select"
                    elif opt_hover:
                        self.temp_speed = GlobalState.note_speed
                        self.temp_menu_volume = GlobalState.menu_volume
                        self.temp_game_volume = GlobalState.game_volume
                        self.temp_fps_mode = GlobalState.fps_mode
                        self.options_open = True
                    elif exit_hover:
                        return "quit"

            pygame.display.flip()
            clock.tick(target_fps)