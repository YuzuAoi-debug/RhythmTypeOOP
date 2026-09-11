import pygame
from global_state import GlobalState

class SongSelect:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        self.BG_COLOR = (14, 14, 18)
        self.SONG_BG = (25, 25, 32)
        self.DIFF_BG = (20, 20, 26)
        self.HOVER_COLOR = (45, 45, 60)
        self.ACCENT_COLOR = (0, 229, 255)
        self.TEXT_COLOR = (245, 245, 255)
        
        self.font_title = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_song = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_diff = pygame.font.SysFont("Arial", 20)
        
        self.expanded_song_index = -1

    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "menu"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_clicked = True

            self.screen.fill(self.BG_COLOR)
            
            title_surf = self.font_title.render("SELECT A TRACK", True, self.TEXT_COLOR)
            self.screen.blit(title_surf, (50, 40))
            
            esc_surf = self.font_diff.render("Press ESC to return", True, (100, 100, 130))
            self.screen.blit(esc_surf, (50, 90))

            y_offset = 150
            x_offset = 50
            
            # Dynamic generation of the Accordion list
            for i, song in enumerate(GlobalState.song_list):
                song_rect = pygame.Rect(x_offset, y_offset, 600, 65)
                is_song_hovered = song_rect.collidepoint(mouse_pos)
                
                # Draw Main Song Plate
                pygame.draw.rect(self.screen, self.HOVER_COLOR if is_song_hovered else self.SONG_BG, song_rect, border_radius=8)
                if self.expanded_song_index == i:
                    pygame.draw.rect(self.screen, self.ACCENT_COLOR, song_rect, 2, border_radius=8)
                
                song_text = self.font_song.render(song["title"], True, self.TEXT_COLOR)
                self.screen.blit(song_text, (x_offset + 20, y_offset + 15))
                
                if mouse_clicked and is_song_hovered:
                    # Toggle expansion
                    if self.expanded_song_index == i:
                        self.expanded_song_index = -1
                    else:
                        self.expanded_song_index = i
                
                y_offset += 75
                
                # Draw Difficulty Sub-menus if expanded
                if self.expanded_song_index == i:
                    for diff in song["difficulties"]:
                        # Push difficulty buttons inwards slightly (like SIZE_SHRINK_END in Godot)
                        diff_rect = pygame.Rect(x_offset + 50, y_offset, 550, 45)
                        is_diff_hovered = diff_rect.collidepoint(mouse_pos)
                        
                        pygame.draw.rect(self.screen, self.HOVER_COLOR if is_diff_hovered else self.DIFF_BG, diff_rect, border_radius=6)
                        
                        diff_text = self.font_diff.render(diff["name"], True, self.ACCENT_COLOR if is_diff_hovered else self.TEXT_COLOR)
                        self.screen.blit(diff_text, (diff_rect.x + 20, diff_rect.y + 10))
                        
                        # Handle selection and payload binding
                        if mouse_clicked and is_diff_hovered:
                            GlobalState.selected_song_data = {
                                "title": song["title"],
                                "audio_path": song["audio_path"],
                                "osu_path": diff["osu_path"]
                            }
                            # Stop the background menu music before gameplay
                            pygame.mixer.music.stop()
                            return "play"
                            
                        y_offset += 55
                    y_offset += 10 # Extra padding after an open accordion item

            pygame.display.flip()
            clock.tick(60)