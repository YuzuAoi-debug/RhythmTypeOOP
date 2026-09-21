import os
import math
import pygame
from global_state import GlobalState, get_fps_target

class SongSelect:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        self.BG_COLOR = (14, 14, 18)
        self.SONG_BG = (24, 24, 34)
        self.DIFF_BG = (19, 19, 26)
        self.HOVER_COLOR = (42, 42, 58)
        self.ACCENT_COLOR = (0, 229, 255)
        self.TEXT_COLOR = (245, 245, 255)
        self.MUTED_COLOR = (140, 140, 170)
        self.MUTED_DARK = (115, 115, 150)
        
        # Typography - enlarged and balanced for modern aesthetic
        self.font_title = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_header_sub = pygame.font.SysFont("Arial", 18)
        self.font_brand = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_song = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_song_sub = pygame.font.SysFont("Arial", 17)
        self.font_diff = pygame.font.SysFont("Arial", 21, bold=True)
        self.font_preview_title = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_preview_meta = pygame.font.SysFont("Arial", 21)
        self.font_preview_diffs = pygame.font.SysFont("Arial", 19, bold=True)
        self.font_preview_hint = pygame.font.SysFont("Arial", 16)
        
        total_songs = len(GlobalState.song_list)
        self.expanded_song_index = GlobalState.expanded_song_index if 0 <= GlobalState.expanded_song_index < total_songs else (0 if total_songs > 0 else -1)
        self.selected_song_index = GlobalState.selected_song_index if 0 <= GlobalState.selected_song_index < total_songs else (0 if total_songs > 0 else -1)
        self.scroll_y = -max(0.0, self.selected_song_index * 78.0 - 100.0)
        self.target_scroll_y = self.scroll_y

        # Dynamic background state for hovering & smooth transitions
        self.active_bg_index = self.selected_song_index
        self.prev_bg_index = None
        self.bg_transition_alpha = 1.0

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

        # Cache preview background art, pre-processed banners, and frosted glass backgrounds
        self.bg_cache = {}
        self.banner_cache = {}
        self.frosted_bg_cache = {}
        for song in GlobalState.song_list:
            bg_path = song.get("background_path")
            if bg_path and bg_path not in self.bg_cache:
                try:
                    raw = pygame.image.load(bg_path).convert()
                    self.bg_cache[bg_path] = raw
                    self.banner_cache[bg_path] = self._process_banner(raw)
                    self.frosted_bg_cache[bg_path] = self._process_frosted_bg(raw)
                except Exception:
                    pass

<<<<<<< Updated upstream
        # Banner gradient fade cache
        self.fade_surf = pygame.Surface((490, 80), pygame.SRCALPHA)
        for y in range(80):
            alpha = int(255 * (y / 80.0))
            pygame.draw.line(self.fade_surf, (22, 22, 30, alpha), (0, y), (490, y))

        self.show_mods_modal = False
        self.mods_info = [
            {"code": "NF", "name": "No Fail", "desc": "Can't fail even at 0% HP", "mult": "0.50x"},
            {"code": "HR", "name": "Hard Rock", "desc": "Tighter timing & 1.4x speed", "mult": "1.06x"},
            {"code": "SD", "name": "Sudden Death", "desc": "1 Miss or Wrong = Fail", "mult": "1.00x"},
            {"code": "PF", "name": "Perfect", "desc": "SS or Instant Fail", "mult": "1.00x"},
            {"code": "DT", "name": "Double Time", "desc": "1.5x Song Speed", "mult": "1.12x"},
        ]

        # Start preview playback of selected song immediately
        if 0 <= self.selected_song_index < len(GlobalState.song_list):
            self._play_song_preview(GlobalState.song_list[self.selected_song_index])

    def _play_song_preview(self, song):
        if not song or not song.get("audio_path"):
            return
        try:
            pygame.mixer.music.load(song["audio_path"])
            pygame.mixer.music.set_volume(GlobalState.music_volume)
            pygame.mixer.music.play(-1)
        except Exception:
            pass
=======
    def _trim_letterbox(self, surface):
        """Trims black letterbox bars at top and bottom of an image."""
        w, h = surface.get_size()
        top_trim = 0
        for y in range(min(h // 4, 200)):
            p_left = surface.get_at((30, y))[:3]
            p_right = surface.get_at((w - 30, y))[:3]
            if max(p_left) < 40 and max(p_right) < 40:
                top_trim = y + 1
            else:
                break
                
        bottom_trim = h
        for y in range(h - 1, max(h - 1 - min(h // 4, 200), top_trim + 50), -1):
            p_left = surface.get_at((30, y))[:3]
            p_right = surface.get_at((w - 30, y))[:3]
            if max(p_left) < 40 and max(p_right) < 40:
                bottom_trim = y
            else:
                break
                
        if bottom_trim - top_trim >= 50:
            return surface.subsurface((0, top_trim, w, bottom_trim - top_trim))
        return surface

    def _process_banner(self, bg_raw, target_w=490, target_h=240, border_radius=12, bg_color=(22, 22, 30)):
        """Trims black letterbox bars, crops to aspect-fill, rounds top corners, and fades bottom into card."""
        trimmed = self._trim_letterbox(bg_raw)
        cw, ch = trimmed.get_size()
        scale = max(target_w / cw, target_h / ch)
        scaled_w = max(target_w, int(math.ceil(cw * scale)))
        scaled_h = max(target_h, int(math.ceil(ch * scale)))
        scaled_surf = pygame.transform.smoothscale(trimmed, (scaled_w, scaled_h))

        # Center crop
        crop_x = max(0, min(scaled_w - target_w, (scaled_w - target_w) // 2))
        crop_y = max(0, min(scaled_h - target_h, (scaled_h - target_h) // 2))
        center_cropped = scaled_surf.subsurface((crop_x, crop_y, target_w, target_h)).copy()

        # Smooth gradient fade at bottom into the card background
        fade_surf = pygame.Surface((target_w, 85), pygame.SRCALPHA)
        for y in range(85):
            alpha = int(255 * (y / 85.0))
            pygame.draw.line(fade_surf, (bg_color[0], bg_color[1], bg_color[2], alpha), (0, y), (target_w, y))
        center_cropped.blit(fade_surf, (0, target_h - 85))

        # Rounded top corners mask to match preview card border radius
        mask_surf = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
        mask_surf.fill((0, 0, 0, 0))
        pygame.draw.rect(mask_surf, (255, 255, 255, 255), (0, 0, target_w, target_h),
                         border_top_left_radius=border_radius, border_top_right_radius=border_radius)

        final_banner = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
        final_banner.blit(center_cropped, (0, 0))
        final_banner.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return final_banner

    def _process_frosted_bg(self, bg_raw):
        """Creates a blurry, frosted-glass acrylic background from raw image."""
        target_w, target_h = self.width, self.height
        trimmed = self._trim_letterbox(bg_raw)
        w, h = trimmed.get_size()
        scale = max(target_w / w, target_h / h)
        sw = max(target_w, int(math.ceil(w * scale)))
        sh = max(target_h, int(math.ceil(h * scale)))
        scaled = pygame.transform.smoothscale(trimmed, (sw, sh))

        crop_x = max(0, min(sw - target_w, (sw - target_w) // 2))
        crop_y = max(0, min(sh - target_h, (sh - target_h) // 2))
        cropped = scaled.subsurface((crop_x, crop_y, target_w, target_h)).copy()

        # Multi-stage smoothscale for silky frosted glass blur
        pass1 = pygame.transform.smoothscale(cropped, (40, 22))
        pass2 = pygame.transform.smoothscale(pass1, (160, 90))
        pass3 = pygame.transform.smoothscale(pass2, (20, 11))
        blurred = pygame.transform.smoothscale(pass3, (target_w, target_h))

        # Dark translucent acrylic overlay for readability & contrast (behind glass look)
        glass_overlay = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
        glass_overlay.fill((14, 14, 20, 190))
        blurred.blit(glass_overlay, (0, 0))
        return blurred

    def _render_fitted_text(self, font, text, color, max_w):
        """Renders text and gracefully fits it within max_w bounds if necessary."""
        surf = font.render(text, True, color)
        if surf.get_width() > max_w:
            scale_ratio = max_w / surf.get_width()
            if scale_ratio >= 0.8:
                new_w = int(surf.get_width() * scale_ratio)
                new_h = int(surf.get_height() * scale_ratio)
                return pygame.transform.smoothscale(surf, (new_w, new_h))
            else:
                for i in range(len(text), 0, -1):
                    t = text[:i] + "..."
                    s = font.render(t, True, color)
                    if s.get_width() <= max_w:
                        return s
        return surf
>>>>>>> Stashed changes

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

    def _start_song(self, song, diff=None):
        if not diff and song.get("difficulties"):
            diff = song["difficulties"][0]
        if not diff:
            return None

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
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.show_mods_modal:
                            self.show_mods_modal = False
                        else:
                            return "menu"
                    if event.key == pygame.K_F1:
                        self._play_click()
                        self.show_mods_modal = not self.show_mods_modal

                    if not self.show_mods_modal:
                        # Arrow navigation across song list
                        if event.key in (pygame.K_DOWN, pygame.K_j):
                            if GlobalState.song_list:
                                new_idx = (self.selected_song_index + 1) % len(GlobalState.song_list)
                                self.selected_song_index = new_idx
                                self.expanded_song_index = new_idx
                                self._play_song_preview(GlobalState.song_list[new_idx])
                                self.target_scroll_y = -max(0.0, self.selected_song_index * 75.0 - 100.0)
                        elif event.key in (pygame.K_UP, pygame.K_k):
                            if GlobalState.song_list:
                                new_idx = (self.selected_song_index - 1) % len(GlobalState.song_list)
                                self.selected_song_index = new_idx
                                self.expanded_song_index = new_idx
                                self._play_song_preview(GlobalState.song_list[new_idx])
                                self.target_scroll_y = -max(0.0, self.selected_song_index * 75.0 - 100.0)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            if 0 <= self.selected_song_index < len(GlobalState.song_list):
                                res = self._start_song(GlobalState.song_list[self.selected_song_index])
                                if res:
                                    return res

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_clicked = True
<<<<<<< Updated upstream
                if event.type == pygame.MOUSEWHEEL and not self.show_mods_modal:
                    self.target_scroll_y += event.y * 45.0
                if event.type == pygame.DROPFILE and not self.show_mods_modal:
=======
                if event.type == pygame.MOUSEWHEEL:
                    self.target_scroll_y += event.y * 48.0
                if event.type == pygame.DROPFILE:
>>>>>>> Stashed changes
                    from beatmap_importer import BeatmapImporter
                    imported = BeatmapImporter.import_file(event.file)
                    if imported:
                        self.expanded_song_index = GlobalState.expanded_song_index
                        self.selected_song_index = GlobalState.selected_song_index
                        bg_path = imported.get("background_path")
                        if bg_path and bg_path not in self.bg_cache:
                            try:
                                raw = pygame.image.load(bg_path).convert()
                                self.bg_cache[bg_path] = raw
                                self.banner_cache[bg_path] = self._process_banner(raw)
                                self.frosted_bg_cache[bg_path] = self._process_frosted_bg(raw)
                            except Exception:
                                pass
<<<<<<< Updated upstream
                        self.target_scroll_y = -max(0.0, self.selected_song_index * 75.0 - 100.0)
                        self._play_song_preview(imported)
=======
                        self.target_scroll_y = -max(0.0, self.selected_song_index * 78.0 - 100.0)
>>>>>>> Stashed changes

            # Calculate content height to clamp scrolling
            total_content_height = 0
            for i, song in enumerate(GlobalState.song_list):
                total_content_height += 78
                if self.expanded_song_index == i:
                    total_content_height += len(song["difficulties"]) * 54 + 10

            min_scroll = min(0.0, self.height - 180 - total_content_height)
            self.target_scroll_y = max(min_scroll, min(0.0, self.target_scroll_y))
            self.scroll_y += (self.target_scroll_y - self.scroll_y) * 0.25

            # Determine hovered song for dynamic background & preview card
            clip_rect = pygame.Rect(0, 120, 720, self.height - 130)
            curr_hovered_song_idx = -1
            curr_hovered_item = None
            
            y_offset = 130 + int(self.scroll_y)
            x_offset = 50
            for i, song in enumerate(GlobalState.song_list):
                song_rect = pygame.Rect(x_offset, y_offset, 650, 68)
                if song_rect.collidepoint(mouse_pos) and clip_rect.collidepoint(mouse_pos):
                    curr_hovered_song_idx = i
                    curr_hovered_item = f"song_{i}"
                
                y_offset += 78
                if self.expanded_song_index == i:
                    for diff in song["difficulties"]:
                        diff_rect = pygame.Rect(x_offset + 45, y_offset, 605, 46)
                        if diff_rect.collidepoint(mouse_pos) and clip_rect.collidepoint(mouse_pos):
                            curr_hovered_song_idx = i
                            curr_hovered_item = f"diff_{diff['name']}_{y_offset}"
                        y_offset += 54
                    y_offset += 10

            # Target background based on hover, falling back to selected song
            target_bg_idx = curr_hovered_song_idx if curr_hovered_song_idx != -1 else self.selected_song_index
            if 0 <= target_bg_idx < len(GlobalState.song_list):
                if target_bg_idx != self.active_bg_index:
                    self.prev_bg_index = self.active_bg_index
                    self.active_bg_index = target_bg_idx
                    self.bg_transition_alpha = 0.0

            # Advance background cross-fade transition
            if self.bg_transition_alpha < 1.0:
                self.bg_transition_alpha = min(1.0, self.bg_transition_alpha + 0.12)

            # Draw Frosted Glass Dynamic Background
            self.screen.fill(self.BG_COLOR)
            
            prev_bg_surf = None
            if self.prev_bg_index is not None and 0 <= self.prev_bg_index < len(GlobalState.song_list):
                prev_path = GlobalState.song_list[self.prev_bg_index].get("background_path")
                prev_bg_surf = self.frosted_bg_cache.get(prev_path)
            
            active_bg_surf = None
            if 0 <= self.active_bg_index < len(GlobalState.song_list):
                active_path = GlobalState.song_list[self.active_bg_index].get("background_path")
                active_bg_surf = self.frosted_bg_cache.get(active_path)

            if prev_bg_surf and self.bg_transition_alpha < 1.0:
                self.screen.blit(prev_bg_surf, (0, 0))
                if active_bg_surf:
                    active_bg_surf.set_alpha(int(255 * self.bg_transition_alpha))
                    self.screen.blit(active_bg_surf, (0, 0))
                    active_bg_surf.set_alpha(255)
            elif active_bg_surf:
                self.screen.blit(active_bg_surf, (0, 0))

            # Display song in preview card (follows hover, or active selection)
            preview_song_idx = curr_hovered_song_idx if curr_hovered_song_idx != -1 else self.selected_song_index
            if 0 <= preview_song_idx < len(GlobalState.song_list):
                sel_song = GlobalState.song_list[preview_song_idx]
                preview_rect = pygame.Rect(740, 130, 490, 520)
                
                # Frosted glass card plate
                card_surf = pygame.Surface((490, 520), pygame.SRCALPHA)
                pygame.draw.rect(card_surf, (22, 22, 30, 235), (0, 0, 490, 520), border_radius=12)
                self.screen.blit(card_surf, (740, 130))

                # Hero banner artwork (cleanly cropped, rounded, and bottom-faded)
                bg_path = sel_song.get("background_path")
                banner = self.banner_cache.get(bg_path)
                if not banner and bg_path and os.path.exists(bg_path):
                    try:
<<<<<<< Updated upstream
                        banner = pygame.transform.smoothscale(bg_raw, (490, 240))
                        # Rounded top corners clipping
                        self.screen.blit(banner, (740, 130))
                        # Subtle gradient fade at bottom of banner
                        self.screen.blit(self.fade_surf, (740, 290))
=======
                        raw = pygame.image.load(bg_path).convert()
                        self.bg_cache[bg_path] = raw
                        banner = self._process_banner(raw)
                        self.banner_cache[bg_path] = banner
>>>>>>> Stashed changes
                    except Exception:
                        pass

                if banner:
                    self.screen.blit(banner, (740, 130))

                # Card outline
                pygame.draw.rect(self.screen, (55, 55, 75), preview_rect, 2, border_radius=12)

                # Track Details
                p_title = self._render_fitted_text(self.font_preview_title, sel_song["title"], self.TEXT_COLOR, 440)
                self.screen.blit(p_title, (765, 388))

                artist_text = sel_song.get("artist", "Unknown Artist")
                bpm_val = sel_song.get("bpm", 130.0)
<<<<<<< Updated upstream
                if "DT" in GlobalState.active_mods:
                    bpm_val *= 1.5
                p_meta = self.font_diff.render(f"Artist: {artist_text}  |  BPM: {int(bpm_val)}" + (" (DT 1.5x)" if "DT" in GlobalState.active_mods else ""), True, self.MUTED_COLOR)
                self.screen.blit(p_meta, (765, 430))
=======
                p_meta = self._render_fitted_text(self.font_preview_meta, f"Artist: {artist_text}  |  BPM: {int(bpm_val)}", self.MUTED_COLOR, 440)
                self.screen.blit(p_meta, (765, 434))
>>>>>>> Stashed changes

                diff_count = len(sel_song["difficulties"])
                p_diffs = self.font_preview_diffs.render(f"Available Difficulties: {diff_count}", True, self.ACCENT_COLOR)
                self.screen.blit(p_diffs, (765, 474))

<<<<<<< Updated upstream
                # Display Active Mods on Preview Panel
                mod_str = " ".join(sorted(GlobalState.active_mods)) if GlobalState.active_mods else "None"
                mult = GlobalState.get_score_multiplier()
                p_mods = self.font_small.render(f"Active Mods: {mod_str}  ({mult:.2f}x Multiplier)", True, self.TEXT_COLOR if GlobalState.active_mods else self.MUTED_COLOR)
                self.screen.blit(p_mods, (765, 500))

                # Interactive Quick Play Button
                play_btn_rect = pygame.Rect(765, 535, 200, 44)
                is_play_hovered = play_btn_rect.collidepoint(mouse_pos) and not self.show_mods_modal
                if is_play_hovered and mouse_clicked:
                    self._play_click()
                    res = self._start_song(sel_song)
                    if res:
                        return res

                pygame.draw.rect(self.screen, self.ACCENT_COLOR if is_play_hovered else (30, 42, 52), play_btn_rect, border_radius=8)
                p_label = self.font_diff.render("▶ PLAY TRACK", True, (10, 10, 15) if is_play_hovered else self.ACCENT_COLOR)
                self.screen.blit(p_label, p_label.get_rect(center=play_btn_rect.center))

                help_txt = self.font_small.render("Press ENTER or click difficulty to start", True, (90, 90, 120))
                self.screen.blit(help_txt, (765, 592))
=======
                help_txt = self.font_preview_hint.render("Click a difficulty on the left to start track", True, self.MUTED_DARK)
                self.screen.blit(help_txt, (765, 595))
>>>>>>> Stashed changes
            
            # Draw header (fixed at top)
            title_surf = self.font_title.render("SELECT A TRACK", True, self.TEXT_COLOR)
            self.screen.blit(title_surf, (50, 28))
            
<<<<<<< Updated upstream
            esc_surf = self.font_small.render("Press ESC to return  |  Scroll with Mouse Wheel  |  Press F1 for Mods", True, self.MUTED_COLOR)
            self.screen.blit(esc_surf, (50, 75))
=======
            esc_surf = self.font_header_sub.render("Press ESC to return  |  Scroll with Mouse Wheel", True, self.MUTED_COLOR)
            self.screen.blit(esc_surf, (50, 78))
>>>>>>> Stashed changes

            # Brand logo badge at top right
            if self.logo_badge:
                self.screen.blit(self.logo_badge, (self.width - 240, 28))
                brand_text = self.font_brand.render("RhythmType", True, self.TEXT_COLOR)
                self.screen.blit(brand_text, (self.width - 180, 36))

<<<<<<< Updated upstream
            # Clipping area for scrolling song list (leave room for bottom-left MODS bar)
            clip_rect = pygame.Rect(0, 120, 720, self.height - 195)
=======
            # Clipping area for scrolling song list
>>>>>>> Stashed changes
            self.screen.set_clip(clip_rect)

            y_offset = 130 + int(self.scroll_y)
            x_offset = 50
            
            # Dynamic generation of the Accordion list
            for i, song in enumerate(GlobalState.song_list):
<<<<<<< Updated upstream
                song_rect = pygame.Rect(x_offset, y_offset, 650, 65)
                is_song_hovered = song_rect.collidepoint(mouse_pos) and clip_rect.collidepoint(mouse_pos) and not self.show_mods_modal
                if is_song_hovered:
                    curr_hovered_item = f"song_{i}"
=======
                song_rect = pygame.Rect(x_offset, y_offset, 650, 68)
                is_song_hovered = song_rect.collidepoint(mouse_pos) and clip_rect.collidepoint(mouse_pos)
>>>>>>> Stashed changes
                
                # Draw Main Song Plate with subtle frosted translucency
                plate_surf = pygame.Surface((650, 68), pygame.SRCALPHA)
                plate_color = (42, 42, 58, 235) if is_song_hovered else (24, 24, 34, 220)
                pygame.draw.rect(plate_surf, plate_color, (0, 0, 650, 68), border_radius=8)
                self.screen.blit(plate_surf, (x_offset, y_offset))

                if self.selected_song_index == i:
                    pygame.draw.rect(self.screen, self.ACCENT_COLOR, song_rect, 2, border_radius=8)
                
                song_text = self._render_fitted_text(self.font_song, song["title"], self.TEXT_COLOR, 600)
                self.screen.blit(song_text, (x_offset + 20, y_offset + 10))

                diff_badge = self.font_song_sub.render(f"{len(song['difficulties'])} Difficulties", True, self.MUTED_COLOR)
                self.screen.blit(diff_badge, (x_offset + 20, y_offset + 40))
                
                if mouse_clicked and is_song_hovered and not self.show_mods_modal:
                    self._play_click()
                    if self.selected_song_index != i:
                        self.selected_song_index = i
                        self.expanded_song_index = i
                        self._play_song_preview(song)
                    else:
                        if self.expanded_song_index == i:
                            self.expanded_song_index = -1
                        else:
                            self.expanded_song_index = i
                
                y_offset += 78
                
                # Draw Difficulty Sub-menus if expanded
                if self.expanded_song_index == i:
                    for diff in song["difficulties"]:
<<<<<<< Updated upstream
                        diff_rect = pygame.Rect(x_offset + 45, y_offset, 605, 44)
                        is_diff_hovered = diff_rect.collidepoint(mouse_pos) and clip_rect.collidepoint(mouse_pos) and not self.show_mods_modal
                        if is_diff_hovered:
                            curr_hovered_item = f"diff_{diff['name']}_{y_offset}"
=======
                        diff_rect = pygame.Rect(x_offset + 45, y_offset, 605, 46)
                        is_diff_hovered = diff_rect.collidepoint(mouse_pos) and clip_rect.collidepoint(mouse_pos)
>>>>>>> Stashed changes
                        
                        d_surf = pygame.Surface((605, 46), pygame.SRCALPHA)
                        d_color = (42, 42, 58, 235) if is_diff_hovered else (19, 19, 26, 220)
                        pygame.draw.rect(d_surf, d_color, (0, 0, 605, 46), border_radius=6)
                        self.screen.blit(d_surf, (diff_rect.x, diff_rect.y))
                        
                        diff_text = self._render_fitted_text(self.font_diff, diff["name"], self.ACCENT_COLOR if is_diff_hovered else self.TEXT_COLOR, 560)
                        self.screen.blit(diff_text, (diff_rect.x + 22, diff_rect.y + 11))
                        
                        # Handle selection and payload binding
                        if mouse_clicked and is_diff_hovered and not self.show_mods_modal:
                            self._play_click()
                            res = self._start_song(song, diff)
                            if res:
                                return res
                            
                        y_offset += 54
                    y_offset += 10

            if curr_hovered_item != self.hovered_item and not self.show_mods_modal:
                self.hovered_item = curr_hovered_item
                if curr_hovered_item is not None:
                    self._play_hover()

            self.screen.set_clip(None)

            # --- BOTTOM-LEFT MODS BAR ---
            mods_btn_rect = pygame.Rect(50, self.height - 62, 170, 44)
            is_mods_hovered = mods_btn_rect.collidepoint(mouse_pos) and not self.show_mods_modal
            if is_mods_hovered and mouse_clicked:
                self._play_click()
                self.show_mods_modal = True

            mods_btn_bg = self.HOVER_COLOR if is_mods_hovered else (24, 24, 34)
            pygame.draw.rect(self.screen, mods_btn_bg, mods_btn_rect, border_radius=8)
            pygame.draw.rect(self.screen, self.ACCENT_COLOR if (is_mods_hovered or GlobalState.active_mods) else (55, 55, 75), mods_btn_rect, 2, border_radius=8)
            
            mod_btn_text = f"MODS ({len(GlobalState.active_mods)}) [F1]" if GlobalState.active_mods else "MODS [F1]"
            mod_btn_surf = self.font_diff.render(mod_btn_text, True, self.ACCENT_COLOR if GlobalState.active_mods else self.TEXT_COLOR)
            self.screen.blit(mod_btn_surf, mod_btn_surf.get_rect(center=mods_btn_rect.center))

            # Active Mod Badges next to MODS button at bottom left
            if GlobalState.active_mods:
                badge_x = 235
                for m_code in sorted(GlobalState.active_mods):
                    b_rect = pygame.Rect(badge_x, self.height - 56, 42, 32)
                    pygame.draw.rect(self.screen, (35, 35, 52), b_rect, border_radius=6)
                    pygame.draw.rect(self.screen, self.ACCENT_COLOR, b_rect, 1, border_radius=6)
                    b_txt = self.font_diff.render(m_code, True, self.ACCENT_COLOR)
                    self.screen.blit(b_txt, b_txt.get_rect(center=b_rect.center))
                    badge_x += 48

            # --- MOD SELECTION MODAL ---
            if self.show_mods_modal:
                dim_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                dim_surf.fill((0, 0, 0, 190))
                self.screen.blit(dim_surf, (0, 0))

                modal_rect = pygame.Rect(self.width // 2 - 290, self.height // 2 - 210, 580, 420)
                pygame.draw.rect(self.screen, (20, 20, 28), modal_rect, border_radius=14)
                pygame.draw.rect(self.screen, self.ACCENT_COLOR, modal_rect, 2, border_radius=14)

                m_title = self.font_preview_title.render("GAME MODIFIERS", True, self.TEXT_COLOR)
                self.screen.blit(m_title, (modal_rect.x + 30, modal_rect.y + 25))

                mult_val = GlobalState.get_score_multiplier()
                m_mult = self.font_diff.render(f"Score Multiplier: {mult_val:.2f}x", True, self.ACCENT_COLOR)
                self.screen.blit(m_mult, (modal_rect.x + modal_rect.width - 210, modal_rect.y + 30))

                pygame.draw.line(self.screen, (45, 45, 65), (modal_rect.x + 30, modal_rect.y + 70), (modal_rect.x + modal_rect.width - 30, modal_rect.y + 70), 1)

                # Render Mod Card Items
                card_y = modal_rect.y + 85
                for m_info in self.mods_info:
                    code = m_info["code"]
                    is_active = code in GlobalState.active_mods
                    card_rect = pygame.Rect(modal_rect.x + 30, card_y, modal_rect.width - 60, 50)
                    is_card_hovered = card_rect.collidepoint(mouse_pos)

                    if mouse_clicked and is_card_hovered:
                        self._play_click()
                        GlobalState.toggle_mod(code)

                    c_bg = (40, 40, 60) if is_active else ((32, 32, 45) if is_card_hovered else (24, 24, 34))
                    pygame.draw.rect(self.screen, c_bg, card_rect, border_radius=8)
                    pygame.draw.rect(self.screen, self.ACCENT_COLOR if is_active else ((70, 70, 95) if is_card_hovered else (45, 45, 60)), card_rect, 2 if is_active else 1, border_radius=8)

                    # Badge pill
                    badge_rect = pygame.Rect(card_rect.x + 15, card_rect.y + 11, 45, 28)
                    pygame.draw.rect(self.screen, self.ACCENT_COLOR if is_active else (50, 50, 70), badge_rect, border_radius=5)
                    code_surf = self.font_diff.render(code, True, (10, 10, 15) if is_active else self.TEXT_COLOR)
                    self.screen.blit(code_surf, code_surf.get_rect(center=badge_rect.center))

                    # Title & Description
                    name_surf = self.font_diff.render(m_info["name"], True, self.TEXT_COLOR)
                    self.screen.blit(name_surf, (card_rect.x + 75, card_rect.y + 6))

                    desc_surf = self.font_small.render(m_info["desc"], True, self.MUTED_COLOR)
                    self.screen.blit(desc_surf, (card_rect.x + 75, card_rect.y + 26))

                    mult_surf = self.font_diff.render(m_info["mult"], True, self.ACCENT_COLOR if is_active else self.MUTED_COLOR)
                    self.screen.blit(mult_surf, (card_rect.x + card_rect.width - 70, card_rect.y + 14))

                    card_y += 58

                # Close Button
                close_rect = pygame.Rect(modal_rect.x + modal_rect.width // 2 - 60, modal_rect.y + modal_rect.height - 48, 120, 36)
                is_close_hovered = close_rect.collidepoint(mouse_pos)
                if mouse_clicked and is_close_hovered:
                    self._play_click()
                    self.show_mods_modal = False

                pygame.draw.rect(self.screen, (45, 45, 62) if is_close_hovered else (30, 30, 42), close_rect, border_radius=6)
                pygame.draw.rect(self.screen, self.ACCENT_COLOR if is_close_hovered else (60, 60, 80), close_rect, 1, border_radius=6)
                c_txt = self.font_small.render("CLOSE", True, self.ACCENT_COLOR if is_close_hovered else self.TEXT_COLOR)
                self.screen.blit(c_txt, c_txt.get_rect(center=close_rect.center))

            pygame.display.flip()
            clock.tick(target_fps)

        return "menu"