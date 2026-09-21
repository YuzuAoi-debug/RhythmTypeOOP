import os
import math
import pygame
from global_state import GlobalState, get_fps_target, get_asset_path

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
        
        self.font_title = pygame.font.Font(get_asset_path("assets/font/RETROTECH.ttf"), 40)
        self.font_header_sub = pygame.font.Font(get_asset_path("assets/font/Comfortaa-Bold.ttf"), 18)
        self.font_brand = pygame.font.Font(get_asset_path("assets/font/RETROTECH.ttf"), 28)
        self.font_song = pygame.font.Font(get_asset_path("assets/font/Comfortaa-Bold.ttf"), 28)
        self.font_song_sub = pygame.font.Font(get_asset_path("assets/font/Comfortaa-Bold.ttf"), 17)
        self.font_diff = pygame.font.Font(get_asset_path("assets/font/Comfortaa-Bold.ttf"), 21)
        self.font_small = pygame.font.Font(get_asset_path("assets/font/Comfortaa-Bold.ttf"), 15)
        self.font_preview_title = pygame.font.Font(get_asset_path("assets/font/Comfortaa-Bold.ttf"), 28)
        self.font_preview_meta = pygame.font.Font(get_asset_path("assets/font/Comfortaa-Bold.ttf"), 21)
        self.font_preview_diffs = pygame.font.Font(get_asset_path("assets/font/Comfortaa-Bold.ttf"), 19)
        self.font_preview_hint = pygame.font.Font(get_asset_path("assets/font/Comfortaa-Bold.ttf"), 16)
        
        total_songs = len(GlobalState.song_list)
        self.expanded_song_index = GlobalState.expanded_song_index if 0 <= GlobalState.expanded_song_index < total_songs else (0 if total_songs > 0 else -1)
        self.selected_song_index = GlobalState.selected_song_index if 0 <= GlobalState.selected_song_index < total_songs else (0 if total_songs > 0 else -1)
        self.selected_diff_index = 0
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

        # Game Modifiers System
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

    def _trim_letterbox(self, surface):
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
    
    def _draw_marquee_text(self, font, text, color, pos, max_w, current_time_ms, speed_px_sec=45.0, pause_ms=1500.0):
        full_surf = font.render(text, True, color)
        text_w = full_surf.get_width()
        text_h = full_surf.get_height()

        if text_w <= max_w:
            self.screen.blit(full_surf, pos)
            return

        overflow = text_w - max_w
        scroll_ms = (overflow / speed_px_sec) * 1000.0
        total_cycle = pause_ms + scroll_ms + pause_ms

        cycle_pos = current_time_ms % total_cycle

        if cycle_pos < pause_ms:
            offset_x = 0.0
        elif cycle_pos < pause_ms + scroll_ms:
            prog = (cycle_pos - pause_ms) / scroll_ms
            offset_x = -overflow * prog
        else:
            offset_x = -overflow

        # Draw into an isolated transparent window to prevent smearing
        window_surf = pygame.Surface((max_w, text_h), pygame.SRCALPHA)
        window_surf.blit(full_surf, (offset_x, 0))
        self.screen.blit(window_surf, pos)
        
    def _get_diff_colors(self, diff_name: str, index: int, is_hovered: bool):
        d_lower = diff_name.lower()
        
        # Tier: 0 = Yellow (Normal/Easy), 1 = Orange (Hard), 2 = Red (Insane), 3 = Black (Special/Expert/Extra)
        if any(k in d_lower for k in ["easy", "normal", "beginner"]):
            tier = 0
        elif any(k in d_lower for k in ["hard", "advanced"]):
            tier = 1
        elif any(k in d_lower for k in ["insane", "hyper"]):
            tier = 2
        elif any(k in d_lower for k in ["special", "affection", "expert", "extra", "extreme", "master"]):
            tier = 3
        else:
            tier = min(3, index)
            
        if tier == 0:
            # Slight Yellow tint
            bg = (42, 38, 20, 235) if is_hovered else (28, 26, 16, 220)
            txt = (255, 230, 120) if is_hovered else (235, 215, 130)
            border = (120, 105, 45) if is_hovered else (75, 65, 30)
        elif tier == 1:
            # Slight Orange tint
            bg = (48, 32, 18, 235) if is_hovered else (32, 22, 15, 220)
            txt = (255, 175, 90) if is_hovered else (240, 155, 80)
            border = (140, 85, 40) if is_hovered else (85, 50, 25)
        elif tier == 2:
            # Slight Red tint
            bg = (48, 20, 24, 235) if is_hovered else (32, 16, 19, 220)
            txt = (255, 110, 125) if is_hovered else (240, 95, 110)
            border = (140, 50, 60) if is_hovered else (85, 30, 40)
        else:
            # Slight Black / Dark Obsidian tint
            bg = (24, 24, 30, 240) if is_hovered else (14, 14, 18, 230)
            txt = (230, 230, 245) if is_hovered else (175, 175, 195)
            border = (80, 80, 105) if is_hovered else (45, 45, 60)
            
        return bg, txt, border

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
            diff_idx = self.selected_diff_index if 0 <= self.selected_diff_index < len(song["difficulties"]) else 0
            diff = song["difficulties"][diff_idx]
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
            current_time = pygame.time.get_ticks()
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
                                self.selected_diff_index = 0
                                self._play_song_preview(GlobalState.song_list[new_idx])
                                self.target_scroll_y = -max(0.0, self.selected_song_index * 78.0 - 100.0)
                        elif event.key in (pygame.K_UP, pygame.K_k):
                            if GlobalState.song_list:
                                new_idx = (self.selected_song_index - 1) % len(GlobalState.song_list)
                                self.selected_song_index = new_idx
                                self.expanded_song_index = new_idx
                                self.selected_diff_index = 0
                                self._play_song_preview(GlobalState.song_list[new_idx])
                                self.target_scroll_y = -max(0.0, self.selected_song_index * 78.0 - 100.0)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            if 0 <= self.selected_song_index < len(GlobalState.song_list):
                                sel_song = GlobalState.song_list[self.selected_song_index]
                                diff_list = sel_song.get("difficulties", [])
                                cur_diff = diff_list[self.selected_diff_index] if 0 <= self.selected_diff_index < len(diff_list) else None
                                res = self._start_song(sel_song, cur_diff)
                                if res:
                                    return res

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_clicked = True
                if event.type == pygame.MOUSEWHEEL and not self.show_mods_modal:
                    self.target_scroll_y += event.y * 48.0
                if event.type == pygame.DROPFILE and not self.show_mods_modal:
                    from beatmap_importer import BeatmapImporter
                    imported = BeatmapImporter.import_file(event.file)
                    if imported:
                        self.expanded_song_index = GlobalState.expanded_song_index
                        self.selected_song_index = GlobalState.selected_song_index
                        self.selected_diff_index = 0
                        bg_path = imported.get("background_path")
                        if bg_path and bg_path not in self.bg_cache:
                            try:
                                raw = pygame.image.load(bg_path).convert()
                                self.bg_cache[bg_path] = raw
                                self.banner_cache[bg_path] = self._process_banner(raw)
                                self.frosted_bg_cache[bg_path] = self._process_frosted_bg(raw)
                            except Exception:
                                pass
                        self.target_scroll_y = -max(0.0, self.selected_song_index * 78.0 - 100.0)
                        self._play_song_preview(imported)

            # Calculate content height to clamp scrolling (leave room for bottom-left MODS bar)
            total_content_height = 0
            for i, song in enumerate(GlobalState.song_list):
                total_content_height += 78
                if self.expanded_song_index == i:
                    total_content_height += len(song["difficulties"]) * 54 + 10

            min_scroll = min(0.0, self.height - 200 - total_content_height)
            self.target_scroll_y = max(min_scroll, min(0.0, self.target_scroll_y))
            self.scroll_y += (self.target_scroll_y - self.scroll_y) * 0.25

            # Determine hovered song for dynamic background & preview card
            clip_rect = pygame.Rect(0, 120, 720, self.height - 195)
            curr_hovered_song_idx = -1
            curr_hovered_item = None
            
            y_offset = 130 + int(self.scroll_y)
            x_offset = 50
            for i, song in enumerate(GlobalState.song_list):
                song_rect = pygame.Rect(x_offset, y_offset, 650, 68)
                if song_rect.collidepoint(mouse_pos) and clip_rect.collidepoint(mouse_pos) and not self.show_mods_modal:
                    curr_hovered_song_idx = i
                    curr_hovered_item = f"song_{i}"
                
                y_offset += 78
                if self.expanded_song_index == i:
                    for d_idx, diff in enumerate(song["difficulties"]):
                        diff_rect = pygame.Rect(x_offset + 45, y_offset, 605, 46)
                        if diff_rect.collidepoint(mouse_pos) and clip_rect.collidepoint(mouse_pos) and not self.show_mods_modal:
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

                # --- DYNAMIC GLOW COLOR BY SONG ---
                # Check song title/id: if it's "confess" or has a custom accent, use warm yellow/orange
                song_title_lower = sel_song.get("title", "").lower()
                if "confess" in song_title_lower or "fennel" in song_title_lower:
                    # Warm Amber / Sunset Orange matching the artwork
                    card_accent = (255, 160, 40)
                    card_border_col = (230, 140, 30)
                else:
                    # Standard Cyan Blue
                    card_accent = self.ACCENT_COLOR
                    card_border_col = (
                        int(45 + (self.ACCENT_COLOR[0] - 45) * 0.4),
                        int(60 + (self.ACCENT_COLOR[1] - 60) * 0.4),
                        int(85 + (self.ACCENT_COLOR[2] - 85) * 0.4),
                    )
    

                # 1. NEON GLOW BACKPLATE
                card_pulse = (math.sin(current_time * 0.003) + 1.0) * 0.5
                glow_pad = 16
                glow_w = preview_rect.width + glow_pad * 2
                glow_h = preview_rect.height + glow_pad * 2
                glow_surf = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)

                card_glow_layers = [
                    (14, int(15 + 12 * card_pulse)),  # Wide outer haze
                    (8,  int(35 + 20 * card_pulse)),  # Mid aura
                    (3,  int(75 + 35 * card_pulse)),  # Core rim bloom
                ]
                for pad, alpha in card_glow_layers:
                    layer_rect = pygame.Rect(glow_pad - pad, glow_pad - pad, preview_rect.width + pad * 2, preview_rect.height + pad * 2)
                    pygame.draw.rect(glow_surf, (*card_accent, alpha), layer_rect, border_radius=12 + pad // 2)

                self.screen.blit(glow_surf, (preview_rect.x - glow_pad, preview_rect.y - glow_pad))

                # 2. CARD BODY
                card_surf = pygame.Surface((490, 520), pygame.SRCALPHA)
                pygame.draw.rect(card_surf, (22, 22, 30, 240), (0, 0, 490, 520), border_radius=12)
                self.screen.blit(card_surf, (740, 130))      
                          
                # Hero banner artwork (cleanly cropped, rounded, and bottom-faded)
                bg_path = sel_song.get("background_path")
                banner = self.banner_cache.get(bg_path)
                if not banner and bg_path and os.path.exists(bg_path):
                    try:
                        raw = pygame.image.load(bg_path).convert()
                        self.bg_cache[bg_path] = raw
                        banner = self._process_banner(raw)
                        self.banner_cache[bg_path] = banner
                    except Exception:
                        pass

                if banner:
                    self.screen.blit(banner, (740, 130))

                # Glowing accent border matching the outer aura
                border_alpha_color = (
                    int(45 + (self.ACCENT_COLOR[0] - 45) * 0.4),
                    int(60 + (self.ACCENT_COLOR[1] - 60) * 0.4),
                    int(85 + (self.ACCENT_COLOR[2] - 85) * 0.4),
                )
                pygame.draw.rect(self.screen, card_border_col, preview_rect, 2, border_radius=12)
                
                # CLEAR PREVIEW TEXT AREA (prevents text overlapping/ghosting)
                text_clear_rect = pygame.Rect(742, 370, 486, 150)
                pygame.draw.rect(self.screen, (22, 22, 30), text_clear_rect)

                # Sliding Marquee Title (Smooth loop without ellipses)
                self._draw_marquee_text(self.font_preview_title, sel_song["title"], self.TEXT_COLOR, (765, 388), 440, current_time)

                artist_text = sel_song.get("artist", "Unknown Artist")
                bpm_val = sel_song.get("bpm", 130.0)
                if "DT" in GlobalState.active_mods:
                    bpm_val *= 1.5
                meta_str = f"Artist: {artist_text}  |  BPM: {int(bpm_val)}" + (" (DT 1.5x)" if "DT" in GlobalState.active_mods else "")
                self._draw_marquee_text(self.font_preview_meta, meta_str, self.MUTED_COLOR, (765, 430), 440, current_time)

                diff_count = len(sel_song["difficulties"])
                p_diffs = self.font_preview_diffs.render(f"Available Difficulties: {diff_count}", True, self.ACCENT_COLOR)
                self.screen.blit(p_diffs, (765, 468))
                
                # Display Active Mods on Preview Panel
                mod_str = " ".join(sorted(GlobalState.active_mods)) if GlobalState.active_mods else "None"
                mult = GlobalState.get_score_multiplier()
                p_mods = self.font_small.render(f"Active Mods: {mod_str}  ({mult:.2f}x Multiplier)", True, self.TEXT_COLOR if GlobalState.active_mods else self.MUTED_COLOR)
                self.screen.blit(p_mods, (765, 498))

                # Play Button
                play_btn_rect = pygame.Rect(765, 532, 230, 46)
                is_play_hovered = play_btn_rect.collidepoint(mouse_pos) and not self.show_mods_modal
                if is_play_hovered:
                    curr_hovered_item = "preview_play_btn"
                    
                # Get currently active difficulty to launch
                diff_list = sel_song.get("difficulties", [])
                active_diff_idx = self.selected_diff_index if (0 <= self.selected_diff_index < len(diff_list) and preview_song_idx == self.selected_song_index) else 0
                active_diff = diff_list[active_diff_idx] if diff_list else None

                if is_play_hovered and mouse_clicked:
                    self._play_click()
                    res = self._start_song(sel_song, active_diff)
                    if res:
                        return res

                play_bg = self.ACCENT_COLOR if is_play_hovered else (28, 38, 48)
                play_border = (120, 240, 255) if is_play_hovered else (45, 65, 85)
                fg_color = (10, 10, 15) if is_play_hovered else self.ACCENT_COLOR
                
                pygame.draw.rect(self.screen, play_bg, play_btn_rect, border_radius=8)
                pygame.draw.rect(self.screen, play_border, play_btn_rect, 2, border_radius=8)
                
                # Render label text without broken unicode glyphs
                btn_text = f"PLAY  [{active_diff['name'].upper()}]" if active_diff else "PLAY TRACK"
                
                # Draw crisp geometric vector play triangle icon
                icon_w = 10
                icon_gap = 10
                max_label_w = 170
                
                full_lbl = self.font_diff.render(btn_text, True, fg_color)
                visible_w = min(full_lbl.get_width(), max_label_w)
                total_w = icon_w + icon_gap + visible_w
                start_x = play_btn_rect.centerx - total_w // 2
                
                # Vector play icon
                tri_p1 = (start_x, play_btn_rect.centery - 6)
                tri_p2 = (start_x, play_btn_rect.centery + 6)
                tri_p3 = (start_x + icon_w, play_btn_rect.centery)
                pygame.draw.polygon(self.screen, fg_color, [tri_p1, tri_p2, tri_p3])    

                # Button marquee
                text_x = start_x + icon_w + icon_gap
                text_y = play_btn_rect.centery - full_lbl.get_height() // 2
                self._draw_marquee_text(self.font_diff, btn_text, fg_color, (text_x, text_y), max_label_w, current_time, speed_px_sec=35.0)

                help_txt = self.font_small.render("Click PLAY or press ENTER / SPACE to start", True, self.MUTED_DARK)
                self.screen.blit(help_txt, (765, 592))
                           
            # Draw header (fixed at top)
            title_surf = self.font_title.render("SELECT A TRACK", True, self.TEXT_COLOR)
            self.screen.blit(title_surf, (50, 28))
            
            esc_surf = self.font_header_sub.render("Press ESC to return  |  Scroll with Mouse Wheel  |  Press F1 for Mods", True, self.MUTED_COLOR)
            self.screen.blit(esc_surf, (50, 78))

            # Brand logo badge at top right
            brand_base_x = self.width - 310
            brand_base_y = 28
            brand_font = pygame.font.Font(get_asset_path("assets/font/RETROTECH.ttf"), 30)
            surf_rhythm = brand_font.render("RHYTHM", True, self.TEXT_COLOR)
            surf_type = brand_font.render("TYPE", True, self.ACCENT_COLOR)

            if self.logo_badge:
                self.screen.blit(self.logo_badge, (brand_base_x, brand_base_y))
                badge_w = self.logo_badge.get_width()
                badge_h = self.logo_badge.get_height()
                badge_offset_x = badge_w + 10
                brand_y = brand_base_y + (badge_h - surf_rhythm.get_height()) // 2
            else:
                badge_offset_x = 0
                brand_y = brand_base_y

            brand_x = brand_base_x + badge_offset_x

            shadow_rhythm = brand_font.render("RHYTHM", True, (0, 0, 0))
            shadow_type = brand_font.render("TYPE", True, (0, 0, 0))
            self.screen.blit(shadow_rhythm, (brand_x + 3, brand_y + 3))
            self.screen.blit(shadow_type, (brand_x + shadow_rhythm.get_width() + 2 + 3, brand_y + 3))

            self.screen.blit(surf_rhythm, (brand_x, brand_y))
            self.screen.blit(surf_type, (brand_x + surf_rhythm.get_width() + 2, brand_y))

            # Clipping area for scrolling song list
            self.screen.set_clip(clip_rect)

            y_offset = 130 + int(self.scroll_y)
            x_offset = 50
            
            # Dynamic generation of the Accordion list
            for i, song in enumerate(GlobalState.song_list):
                song_rect = pygame.Rect(x_offset, y_offset, 650, 68)
                is_song_hovered = song_rect.collidepoint(mouse_pos) and clip_rect.collidepoint(mouse_pos) and not self.show_mods_modal
                
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
                        self.selected_diff_index = 0
                        self._play_song_preview(song)
                    else:
                        if self.expanded_song_index == i:
                            self.expanded_song_index = -1
                        else:
                            self.expanded_song_index = i
                
                y_offset += 78
                
                # Draw Difficulty Sub-menus with specific difficulty-tiered tints (yellow, orange, red, black)
                if self.expanded_song_index == i:
                    for d_idx, diff in enumerate(song["difficulties"]):
                        diff_rect = pygame.Rect(x_offset + 45, y_offset, 605, 46)
                        is_diff_hovered = diff_rect.collidepoint(mouse_pos) and clip_rect.collidepoint(mouse_pos) and not self.show_mods_modal
                        is_diff_selected = (self.selected_song_index == i and self.selected_diff_index == d_idx)
                        
                        d_bg, d_text_color, d_border = self._get_diff_colors(diff["name"], d_idx, is_diff_hovered)
                        
                        d_surf = pygame.Surface((605, 46), pygame.SRCALPHA)
                        pygame.draw.rect(d_surf, d_bg, (0, 0, 605, 46), border_radius=6)
                        self.screen.blit(d_surf, (diff_rect.x, diff_rect.y))
                        
                        # Border highlighting (accent border if selected or hovered)
                        border_color = self.ACCENT_COLOR if is_diff_selected else d_border
                        border_width = 2 if is_diff_selected else 1
                        pygame.draw.rect(self.screen, border_color, diff_rect, border_width, border_radius=6)
                        
                        diff_text = self._render_fitted_text(self.font_diff, diff["name"], d_text_color, 560)
                        self.screen.blit(diff_text, (diff_rect.x + 22, diff_rect.y + 11))
                        
                        # Handle difficulty selection on click (selects difficulty, does NOT start game immediately)
                        if mouse_clicked and is_diff_hovered and not self.show_mods_modal:
                            self._play_click()
                            self.selected_song_index = i
                            self.selected_diff_index = d_idx
                            
                        y_offset += 54
                    y_offset += 10

            if curr_hovered_item != self.hovered_item and not self.show_mods_modal:
                self.hovered_item = curr_hovered_item
                if curr_hovered_item is not None:
                    self._play_hover()

            self.screen.set_clip(None)

            # BOTTOM-LEFT MODS BAR
            mods_btn_rect = pygame.Rect(50, self.height - 62, 170, 44)
            is_mods_hovered = mods_btn_rect.collidepoint(mouse_pos) and not self.show_mods_modal
            if is_mods_hovered:
                curr_hovered_item = "mods_btn"

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

            # MOD SELECTION MODAL
            if self.show_mods_modal:
                dim_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                dim_surf.fill((0, 0, 0, 190))
                self.screen.blit(dim_surf, (0, 0))

                modal_rect = pygame.Rect(self.width // 2 - 290, self.height // 2 - 210, 580, 420)
                pygame.draw.rect(self.screen, (20, 20, 28), modal_rect, border_radius=14)
                pygame.draw.rect(self.screen, self.ACCENT_COLOR, modal_rect, 2, border_radius=14)

                m_title = self.font_preview_title.render("GAME MODIFIERS", True, self.TEXT_COLOR)
                self.screen.blit(m_title, (modal_rect.x + 30, modal_rect.y + 25))

                # Dynamically right-align with a 30px padding inside the border
                mult_val = GlobalState.get_score_multiplier()
                m_mult = self.font_diff.render(f"Score Multiplier: {mult_val:.2f}x", True, self.ACCENT_COLOR)
                mult_x = modal_rect.right - 30 - m_mult.get_width()
                mult_y = modal_rect.y + 32
                self.screen.blit(m_mult, (mult_x, mult_y))
                
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