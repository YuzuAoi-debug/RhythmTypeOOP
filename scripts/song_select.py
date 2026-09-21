import os
import pygame
from global_state import GlobalState, get_fps_target

class SongSelect:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        self.BG_COLOR = (14, 14, 18)
        self.SONG_BG = (24, 24, 32)
        self.DIFF_BG = (19, 19, 26)
        self.HOVER_COLOR = (42, 42, 58)
        self.ACCENT_COLOR = (0, 229, 255)
        self.TEXT_COLOR = (245, 245, 255)
        self.MUTED_COLOR = (110, 110, 140)
        
        self.font_title = pygame.font.SysFont("Arial", 38, bold=True)
        self.font_song = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_diff = pygame.font.SysFont("Arial", 19)
        self.font_small = pygame.font.SysFont("Arial", 15)
        self.font_preview_title = pygame.font.SysFont("Arial", 28, bold=True)
        
        total_songs = len(GlobalState.song_list)
        self.expanded_song_index = GlobalState.expanded_song_index if 0 <= GlobalState.expanded_song_index < total_songs else (0 if total_songs > 0 else -1)
        self.selected_song_index = GlobalState.selected_song_index if 0 <= GlobalState.selected_song_index < total_songs else (0 if total_songs > 0 else -1)
        self.scroll_y = -max(0.0, self.selected_song_index * 75.0 - 100.0)
        self.target_scroll_y = self.scroll_y

        # Load logo badge for header
        self.logo_badge = None
        if os.path.exists(GlobalState.LOGO_PATH):
            try:
                raw_logo = pygame.image.load(GlobalState.LOGO_PATH).convert_alpha()
                self.logo_badge = pygame.transform.smoothscale(raw_logo, (48, 48))
            except Exception:
                pass

        # Hover and click sounds
        self.hover_sound = None
        self.click_sound = None
        self.hovered_item = None
        if os.path.exists(GlobalState.HOVER_SOUND_PATH):
            try:
                self.hover_sound = pygame.mixer.Sound(GlobalState.HOVER_SOUND_PATH)
            except Exception:
                pass
        if os.path.exists(GlobalState.CLICK_SOUND_PATH):
            try:
                self.click_sound = pygame.mixer.Sound(GlobalState.CLICK_SOUND_PATH)
            except Exception:
                pass

        # Cache preview background art
        self.bg_cache = {}
        for song in GlobalState.song_list:
            bg_path = song.get("background_path")
            if bg_path and bg_path not in self.bg_cache:
                try:
                    raw = pygame.image.load(bg_path).convert()
                    self.bg_cache[bg_path] = raw
                except Exception:
                    pass

    def _play_hover(self):
        if self.hover_sound:
            try:
                self.hover_sound.set_volume(GlobalState.sfx_volume)
                self.hover_sound.play()
            except Exception:
                pass

    def _play_click(self):
        if self.click_sound:
            try:
                self.click_sound.set_volume(GlobalState.sfx_volume)
                self.click_sound.play()
            except Exception:
                pass

    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            target_fps = get_fps_target(GlobalState.fps_mode)
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "menu"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_clicked = True
                if event.type == pygame.MOUSEWHEEL:
                    self.target_scroll_y += event.y * 45.0
                if event.type == pygame.DROPFILE:
                    from beatmap_importer import BeatmapImporter
                    imported = BeatmapImporter.import_file(event.file)
                    if imported:
                        self.expanded_song_index = GlobalState.expanded_song_index
                        self.selected_song_index = GlobalState.selected_song_index
                        bg_path = imported.get("background_path")
                        if bg_path and bg_path not in self.bg_cache:
                            try:
                                self.bg_cache[bg_path] = pygame.image.load(bg_path).convert()
                            except Exception:
                                pass
                        self.target_scroll_y = -max(0.0, self.selected_song_index * 75.0 - 100.0)

            # Calculate content height to clamp scrolling
            total_content_height = 0
            for i, song in enumerate(GlobalState.song_list):
                total_content_height += 75
                if self.expanded_song_index == i:
                    total_content_height += len(song["difficulties"]) * 52 + 10

            min_scroll = min(0.0, self.height - 180 - total_content_height)
            self.target_scroll_y = max(min_scroll, min(0.0, self.target_scroll_y))
            self.scroll_y += (self.target_scroll_y - self.scroll_y) * 0.25

            self.screen.fill(self.BG_COLOR)

            # Draw Preview Card on Right Side
            if 0 <= self.selected_song_index < len(GlobalState.song_list):
                sel_song = GlobalState.song_list[self.selected_song_index]
                preview_rect = pygame.Rect(740, 130, 490, 520)
                pygame.draw.rect(self.screen, (22, 22, 30), preview_rect, border_radius=12)
                pygame.draw.rect(self.screen, (45, 45, 60), preview_rect, 2, border_radius=12)

                # Hero banner artwork
                bg_raw = self.bg_cache.get(sel_song.get("background_path"))
                if bg_raw:
                    try:
                        banner = pygame.transform.smoothscale(bg_raw, (490, 240))
                        # Rounded top corners clipping
                        self.screen.blit(banner, (740, 130))
                        # Subtle gradient fade at bottom of banner
                        fade_surf = pygame.Surface((490, 80), pygame.SRCALPHA)
                        for y in range(80):
                            alpha = int(255 * (y / 80.0))
                            pygame.draw.line(fade_surf, (22, 22, 30, alpha), (0, y), (490, y))
                        self.screen.blit(fade_surf, (740, 290))
                    except Exception:
                        pass

                # Track Details
                p_title = self.font_preview_title.render(sel_song["title"], True, self.TEXT_COLOR)
                self.screen.blit(p_title, (765, 390))

                artist_text = sel_song.get("artist", "Unknown Artist")
                bpm_val = sel_song.get("bpm", 130.0)
                p_meta = self.font_diff.render(f"Artist: {artist_text}  |  BPM: {int(bpm_val)}", True, self.MUTED_COLOR)
                self.screen.blit(p_meta, (765, 430))

                diff_count = len(sel_song["difficulties"])
                p_diffs = self.font_small.render(f"Available Difficulties: {diff_count}", True, self.ACCENT_COLOR)
                self.screen.blit(p_diffs, (765, 470))

                help_txt = self.font_small.render("Click a difficulty on the left to start track", True, (90, 90, 120))
                self.screen.blit(help_txt, (765, 580))
            
            # Draw header (fixed at top)
            title_surf = self.font_title.render("SELECT A TRACK", True, self.TEXT_COLOR)
            self.screen.blit(title_surf, (50, 30))
            
            esc_surf = self.font_small.render("Press ESC to return  |  Scroll with Mouse Wheel", True, self.MUTED_COLOR)
            self.screen.blit(esc_surf, (50, 75))

            # Brand logo badge at top right
            if self.logo_badge:
                self.screen.blit(self.logo_badge, (self.width - 240, 30))
                brand_text = self.font_song.render("RhythmType", True, self.TEXT_COLOR)
                self.screen.blit(brand_text, (self.width - 180, 38))

            # Clipping area for scrolling song list
            clip_rect = pygame.Rect(0, 120, 720, self.height - 130)
            self.screen.set_clip(clip_rect)

            y_offset = 130 + int(self.scroll_y)
            x_offset = 50
            curr_hovered_item = None
            
            # Dynamic generation of the Accordion list
            for i, song in enumerate(GlobalState.song_list):
                song_rect = pygame.Rect(x_offset, y_offset, 650, 65)
                is_song_hovered = song_rect.collidepoint(mouse_pos) and clip_rect.collidepoint(mouse_pos)
                if is_song_hovered:
                    curr_hovered_item = f"song_{i}"
                
                # Draw Main Song Plate
                plate_color = self.HOVER_COLOR if is_song_hovered else self.SONG_BG
                pygame.draw.rect(self.screen, plate_color, song_rect, border_radius=8)
                if self.selected_song_index == i:
                    pygame.draw.rect(self.screen, self.ACCENT_COLOR, song_rect, 2, border_radius=8)
                
                song_text = self.font_song.render(song["title"], True, self.TEXT_COLOR)
                self.screen.blit(song_text, (x_offset + 20, y_offset + 12))

                diff_badge = self.font_small.render(f"{len(song['difficulties'])} Difficulties", True, self.MUTED_COLOR)
                self.screen.blit(diff_badge, (x_offset + 20, y_offset + 40))
                
                if mouse_clicked and is_song_hovered:
                    self._play_click()
                    self.selected_song_index = i
                    if self.expanded_song_index == i:
                        self.expanded_song_index = -1
                    else:
                        self.expanded_song_index = i
                
                y_offset += 75
                
                # Draw Difficulty Sub-menus if expanded
                if self.expanded_song_index == i:
                    for diff in song["difficulties"]:
                        diff_rect = pygame.Rect(x_offset + 45, y_offset, 605, 44)
                        is_diff_hovered = diff_rect.collidepoint(mouse_pos) and clip_rect.collidepoint(mouse_pos)
                        if is_diff_hovered:
                            curr_hovered_item = f"diff_{diff['name']}_{y_offset}"
                        
                        d_color = self.HOVER_COLOR if is_diff_hovered else self.DIFF_BG
                        pygame.draw.rect(self.screen, d_color, diff_rect, border_radius=6)
                        
                        diff_text = self.font_diff.render(diff["name"], True, self.ACCENT_COLOR if is_diff_hovered else self.TEXT_COLOR)
                        self.screen.blit(diff_text, (diff_rect.x + 20, diff_rect.y + 10))
                        
                        # Handle selection and payload binding
                        if mouse_clicked and is_diff_hovered:
                            self._play_click()
                            GlobalState.selected_song_data = {
                                "title": song["title"],
                                "artist": song.get("artist", ""),
                                "audio_path": song["audio_path"],
                                "background_path": song.get("background_path", ""),
                                "bpm": song.get("bpm", 130.0),
                                "osu_path": diff["osu_path"],
                                "diff_name": diff["name"]
                            }
                            self.screen.set_clip(None)
                            pygame.mixer.music.stop()
                            return "play"
                            
                        y_offset += 52
                    y_offset += 10

            if curr_hovered_item != self.hovered_item:
                if curr_hovered_item is not None:
                    self._play_hover()
                self.hovered_item = curr_hovered_item

            self.screen.set_clip(None)
            pygame.display.flip()
            clock.tick(target_fps)