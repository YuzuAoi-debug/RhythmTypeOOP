import os
import wave
import math
import random
import pygame
from global_state import GlobalState, get_fps_target
from conductor import Conductor
from beatmap_parser import BeatmapParser
from word_generator import WordGenerator

class GameManager:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        # Colors (osu! lazer dark theme vibe)
        self.BG_COLOR = (14, 14, 18)
        self.LINE_COLOR = (40, 40, 56)
        self.TEXT_COLOR = (245, 245, 255)
        self.ACCENT_COLOR = (0, 229, 255)
        self.MUTED_COLOR = (100, 100, 130)
        self.GREEN_COLOR = (0, 255, 180)
        
        # Fonts (Matching Main Menu Theme)
        from global_state import get_asset_path
        font_retro = get_asset_path("assets/font/RETROTECH.ttf")
        font_game = get_asset_path("assets/font/Comfortaa-Bold.ttf")
               
        try:
            self.font_large = pygame.font.Font(font_game, 36)
            self.font_med = pygame.font.Font(font_game, 28)
            self.font_small = pygame.font.Font(font_game, 15)
            self.font_guide = pygame.font.Font(font_game, 18) 
            self.font_score = pygame.font.Font(font_game, 40)
            self.font_combo = pygame.font.Font(font_game, 44)        
            
        except Exception:
            self.font_large = pygame.font.SysFont("Arial", 44, bold=True)
            self.font_med = pygame.font.SysFont("Arial", 28, bold=True)
            self.font_small = pygame.font.SysFont("Arial", 16)
            self.font_guide = pygame.font.SysFont("Arial", 22, bold=True)
            self.font_score = pygame.font.SysFont("Arial", 48, bold=True)
            self.font_combo = pygame.font.SysFont("Arial", 52, bold=True)
 
        # Defeat / Fail Screen Fonts: Preserved as RETROTECH
        try:
            self.font_fail_title = pygame.font.Font(font_retro, 52)
            self.font_fail_stat = pygame.font.Font(font_retro, 28)
            self.font_fail_sub = pygame.font.Font(font_retro, 18)
            self.font_fail_btn = pygame.font.Font(font_retro, 20)
        except Exception:
            self.font_fail_title = pygame.font.SysFont("Arial", 52, bold=True)
            self.font_fail_stat = pygame.font.SysFont("Arial", 28, bold=True)
            self.font_fail_sub = pygame.font.SysFont("Arial", 18)
            self.font_fail_btn = pygame.font.SysFont("Arial", 20, bold=True)
                    
        # Gameplay Constants
        is_hr = "HR" in GlobalState.active_mods
        self.SCROLL_SPEED = 560.0 if is_hr else 400.0
        self.SPAWN_DISTANCE = 900.0
        
        # HardRock (HR) tightens timing windows by ~30%
        self.PERFECT_WINDOW = 0.028 if is_hr else 0.04  # 28ms vs 40ms
        self.GREAT_WINDOW = 0.056 if is_hr else 0.08    # 56ms vs 80ms
        self.GOOD_WINDOW = 0.084 if is_hr else 0.12     # 84ms vs 120ms
        self.MISS_WINDOW = 0.105 if is_hr else 0.15     # 105ms vs 150ms
        
        # Horizontal layout coordinates
        self.target_x = 200
        self.lane_y = self.height // 2 - 50

        # Sound effects
        self.hitsound = None
        self.miss_sound = None
        try:
            self.hitsound = pygame.mixer.Sound(GlobalState.HITSOUND_PATH)
            self.miss_sound = pygame.mixer.Sound(GlobalState.MISS_SOUND_PATH)
            self.hitsound.set_volume(GlobalState.sfx_volume)
            self.miss_sound.set_volume(GlobalState.sfx_volume)
        except Exception as e:
            print(f"Warning: Failed to load sound effects: {e}")

        # Pre-bake complete note tile surfaces for all letters A-Z (eliminates per-frame copies)
        self.base_note_surf = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.rect(self.base_note_surf, (30, 30, 45, 225), (0, 0, 70, 70), border_radius=15)
        pygame.draw.rect(self.base_note_surf, (*self.ACCENT_COLOR, 255), (0, 0, 70, 70), 3, border_radius=15)

        self.note_surfaces = {}
        for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            surf = self.base_note_surf.copy()
            char_surf = self.font_med.render(c, True, self.TEXT_COLOR)
            surf.blit(char_surf, char_surf.get_rect(center=(35, 35)))
            self.note_surfaces[c] = surf

        # Pre-render judgement text templates
        self.judgement_surfaces = {
            "PERFECT!": self.font_large.render("PERFECT!", True, (0, 255, 180)),
            "GREAT!": self.font_large.render("GREAT!", True, (100, 220, 255)),
            "GOOD": self.font_large.render("GOOD", True, (255, 200, 0)),
            "WRONG": self.font_large.render("WRONG", True, (255, 70, 70)),
            "MISS": self.font_large.render("MISS", True, (255, 60, 60))
        }

    def _play_hitsound(self):
        if self.hitsound:
            self.hitsound.set_volume(GlobalState.sfx_volume)
            self.hitsound.play()

    def _play_miss_sound(self):
        if self.miss_sound:
            self.miss_sound.set_volume(GlobalState.sfx_volume)
            self.miss_sound.play()

    def _draw_centered(self, text, font, color, y):
        surface = font.render(text, True, color)
        self.screen.blit(surface, surface.get_rect(center=(self.width // 2, y)))

    def _draw_button(self, text, rect, hovered, accent_color=None):
        if accent_color is None:
            accent_color = self.ACCENT_COLOR
        color = (45, 45, 62) if hovered else (26, 26, 36)
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, accent_color if hovered else (65, 65, 85), rect, 2, border_radius=8)
        surface = self.font_small.render(text, True, accent_color if hovered else self.TEXT_COLOR)
        self.screen.blit(surface, surface.get_rect(center=rect.center))

    def _pause_screen(self, conductor, clock):
        conductor.pause()
        panel_rect = pygame.Rect(self.width // 2 - 260, self.height // 2 - 180, 520, 360)
        resume_rect = pygame.Rect(panel_rect.x + 40, panel_rect.y + 240, 130, 50)
        retry_rect = pygame.Rect(panel_rect.x + 195, panel_rect.y + 240, 130, 50)
        menu_rect = pygame.Rect(panel_rect.x + 350, panel_rect.y + 240, 130, 50)

        frozen_frame = self.screen.copy()
        dim_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim_overlay.fill((0, 0, 0, 175))
        
        time_start = pygame.time.get_ticks()
        fade_duration = 300.0

        while True:
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    conductor.stop()
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_clicked = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        conductor.unpause()
                        return "resume"
                    if event.key == pygame.K_r and (event.mod & pygame.KMOD_CTRL):
                        conductor.stop()
                        return "retry"

            if mouse_clicked:
                if resume_rect.collidepoint(mouse_pos):
                    conductor.unpause()
                    return "resume"
                if retry_rect.collidepoint(mouse_pos):
                    conductor.stop()
                    return "retry"
                if menu_rect.collidepoint(mouse_pos):
                    conductor.stop()
                    return "menu"

            time_ms = pygame.time.get_ticks() - time_start
            fade_progress = min(1.0, time_ms / fade_duration)
            p = 1.0 - (1.0 - fade_progress)**5
            
            self.screen.blit(frozen_frame, (0, 0))
            
            current_overlay = dim_overlay.copy()
            current_overlay.set_alpha(int(175 * p))
            self.screen.blit(current_overlay, (0, 0))
            
            y_offset = int(20 * (1.0 - p))
            panel_rect_anim = panel_rect.move(0, y_offset)
            resume_rect_anim = resume_rect.move(0, y_offset)
            retry_rect_anim = retry_rect.move(0, y_offset)
            menu_rect_anim = menu_rect.move(0, y_offset)

            panel_surf = pygame.Surface((panel_rect_anim.width, panel_rect_anim.height), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (22, 22, 30, int(255*p)), panel_surf.get_rect(), border_radius=12)
            pygame.draw.rect(panel_surf, (50, 50, 70, int(255*p)), panel_surf.get_rect(), 2, border_radius=12)
            self.screen.blit(panel_surf, panel_rect_anim.topleft)

            def draw_fade_centered(text, font, color, y):
                surf = font.render(text, True, color)
                surf.set_alpha(int(255 * p))
                self.screen.blit(surf, surf.get_rect(center=(self.width // 2, y + y_offset)))
                
            draw_fade_centered("PAUSED", self.font_large, self.TEXT_COLOR, self.height // 2 - 90)
            draw_fade_centered("ESC: Resume   |   CTRL + R: Restart Track", self.font_small, self.MUTED_COLOR, self.height // 2 - 30)
            draw_fade_centered("Use buttons below to navigate", self.font_small, self.MUTED_COLOR, self.height // 2 + 10)

            if p > 0.9:
                self._draw_button("RESUME", resume_rect_anim, resume_rect_anim.collidepoint(mouse_pos))
                self._draw_button("RETRY", retry_rect_anim, retry_rect_anim.collidepoint(mouse_pos))
                self._draw_button("MENU", menu_rect_anim, menu_rect_anim.collidepoint(mouse_pos))

            pygame.display.flip()
            clock.tick(30)

    def _show_fail_screen(self, score, max_combo, clock, last_frame=None):
        pygame.mixer.music.stop()
        retry_rect = pygame.Rect(self.width // 2 - 160, 390, 140, 48)
        menu_rect = pygame.Rect(self.width // 2 + 20, 390, 140, 48)

        # Pre-render a menacing dark red radial vignette
        vignette_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        max_radius = int(math.hypot(self.width/2, self.height/2))
        for r in range(max_radius, 0, -15):
            alpha = max(0, min(150, int(150 * (r / max_radius))))
            pygame.draw.circle(vignette_surf, (15, 0, 5, alpha), (self.width // 2, self.height // 2), r)

        # Pre-render soft edge gradient for the top wave to remove the hard vector edge
        gradient_h = 400
        wave_gradient = pygame.Surface((1, gradient_h), pygame.SRCALPHA)
        for y in range(gradient_h):
            # Ease-in alpha for a very soft leading edge
            alpha_ratio = y / gradient_h
            alpha = int(255 * (alpha_ratio ** 2))
            wave_gradient.set_at((0, y), (20, 2, 4, alpha))
        wave_gradient = pygame.transform.scale(wave_gradient, (self.width, gradient_h))

        # Initialize floating red pixels
        embers = []
        for _ in range(80):
            embers.append({
                "x": random.uniform(0, self.width),
                "y": random.uniform(0, self.height),
                "vx": random.uniform(-20, 20),
                "vy": random.uniform(-80, -20),
                "size": random.randint(2, 6),
                "pulse": random.uniform(0, math.pi * 2)
            })

        time_start = pygame.time.get_ticks()
        fade_duration = 2000.0
        dt = 1.0 / 30.0

        while True:
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_clicked = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and (event.mod & pygame.KMOD_CTRL):
                        return "retry"
                    if event.key in (pygame.K_ESCAPE, pygame.K_m, pygame.K_RETURN):
                        return "menu"

            if mouse_clicked:
                if retry_rect.collidepoint(mouse_pos):
                    return "retry"
                if menu_rect.collidepoint(mouse_pos):
                    return "menu"

            time_ms = pygame.time.get_ticks() - time_start
            fade_progress = min(1.0, time_ms / fade_duration)
            
            if fade_progress < 0.4:
                if last_frame:
                    self.screen.blit(last_frame, (0, 0))
                else:
                    self.screen.fill((10, 4, 6))
                
                # Surge up: from off-screen to covering screen
                p = fade_progress / 0.4
                p = 1.0 - (1.0 - p)**3 # Ease out
                start_offset = 350
                end_offset = -(self.height - 250) - 150
                wave_y_offset = start_offset + (end_offset - start_offset) * p
            else:
                # Dark Void Background
                self.screen.fill((10, 4, 6))
                
                # Settle down: from covering screen to normal resting position
                p = (fade_progress - 0.4) / 0.6
                p = 1.0 - (1.0 - p)**3 # Ease out
                start_offset = -(self.height - 250) - 150
                end_offset = 0
                wave_y_offset = start_offset + (end_offset - start_offset) * p
            
            # Procedural Fluid Sine Waves (Multi-octave for organic liquid feel)
            for i in range(5):
                wave_pts = [(0, self.height)]
                base_y = self.height - 250 + i * 60 + wave_y_offset
                
                if i == 0:
                    # Draw the soft gradient above the highest wave to eliminate the hard "upper edge"
                    self.screen.blit(wave_gradient, (0, int(base_y - gradient_h + 30)))
                    
                speed = 0.001 + i * 0.0002
                freq = 0.0015 + i * 0.0005
                amp = 20 + i * 10
                for x in range(0, self.width + 20, 10):
                    # Combine 3 sine waves for a turbulent, highly fluid curve
                    y = base_y                         + math.sin(time_ms * speed + x * freq) * amp                         + math.cos(time_ms * speed * 1.4 + x * freq * 2.3 + i) * (amp * 0.4)                         + math.sin(time_ms * speed * 0.8 + x * freq * 0.4 + i*2) * (amp * 0.2)
                    wave_pts.append((x, y))
                wave_pts.append((self.width, self.height))
                pygame.draw.polygon(self.screen, (20 + i*10, 2 + i*2, 4 + i*3), wave_pts)

            # Only show UI elements after the wave has crashed down (fade_progress > 0.4)
            if fade_progress > 0.4:
                ui_alpha_progress = min(1.0, (fade_progress - 0.4) / 0.6)
                
                # Pulsing ambient vignette
                pulse = (math.sin(time_ms * 0.003) + 1.0) * 0.5
                vignette_surf.set_alpha(int((100 + 55 * pulse) * ui_alpha_progress))
                self.screen.blit(vignette_surf, (0, 0))

                # Update & Draw Floating Red Pixels
                for ember in embers:
                    ember["x"] += ember["vx"] * dt
                    ember["y"] += ember["vy"] * dt
                    if ember["y"] < -20:
                        ember["y"] = self.height + 20
                        ember["x"] = random.uniform(0, self.width)
                    
                    e_pulse = (math.sin(time_ms * 0.005 + ember["pulse"]) + 1.0) * 0.5
                    e_alpha = int((100 + 155 * e_pulse) * ui_alpha_progress)
                    e_size = int(ember["size"])
                    
                    ember_surf = pygame.Surface((e_size, e_size), pygame.SRCALPHA)
                    ember_surf.fill((255, 40, 40, e_alpha))
                    self.screen.blit(ember_surf, (int(ember["x"]), int(ember["y"])))

                # Ken Burns subtle panning
                pan_offset_y = int(math.sin(time_ms * 0.001) * 15)

                # Glitched FAILED Text
                glitch_x = int(math.sin(time_ms * 0.05) * 4 * pulse)
                glitch_y = int(math.cos(time_ms * 0.07) * 3 * pulse)
                
                fail_text = "TRACK FAILED"
                red_surf = self.font_fail_title.render(fail_text, True, (255, 20, 20))
                blue_surf = self.font_fail_title.render(fail_text, True, (0, 255, 255))
                main_surf = self.font_fail_title.render(fail_text, True, (255, 230, 230))
                
                red_surf.set_alpha(int(255 * ui_alpha_progress))
                blue_surf.set_alpha(int(255 * ui_alpha_progress))
                main_surf.set_alpha(int(255 * ui_alpha_progress))
                
                center_x, center_y = self.width // 2, 130 + pan_offset_y
                self.screen.blit(red_surf, red_surf.get_rect(center=(center_x + glitch_x, center_y + glitch_y)))
                self.screen.blit(blue_surf, blue_surf.get_rect(center=(center_x - glitch_x, center_y - glitch_y)))
                self.screen.blit(main_surf, main_surf.get_rect(center=(center_x, center_y)))

                score_surf = self.font_med.render(f"Score  {int(score):06d}", True, (200, 180, 180))
                combo_surf = self.font_med.render(f"Max Combo  {max_combo}x", True, (200, 180, 180))
                inst_surf = self.font_small.render("Press CTRL+R or click buttons below", True, (150, 100, 100))
                
                score_surf.set_alpha(int(255 * ui_alpha_progress))
                combo_surf.set_alpha(int(255 * ui_alpha_progress))
                inst_surf.set_alpha(int(255 * ui_alpha_progress))
                
                self.screen.blit(score_surf, score_surf.get_rect(center=(center_x, 260)))
                self.screen.blit(combo_surf, combo_surf.get_rect(center=(center_x, 300)))
                self.screen.blit(inst_surf, inst_surf.get_rect(center=(center_x, 350)))

                red_accent = (255, 60, 80)
                if ui_alpha_progress > 0.9:
                    self._draw_button("RETRY", retry_rect, retry_rect.collidepoint(mouse_pos), red_accent)
                    self._draw_button("MENU", menu_rect, menu_rect.collidepoint(mouse_pos), red_accent)

            pygame.display.flip()
            dt = clock.tick(30) / 1000.0

    def _show_results(self, score, max_combo, timing_errors, counts, ur_value, clock, last_frame=None):
        pygame.mixer.music.stop()
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        time_start = pygame.time.get_ticks()
        fade_duration = 600.0
        c300 = counts["perfect"]
        c100 = counts["great"]
        c50 = counts["good"]
        cmiss = counts["miss"]
        total = max(1, c300 + c100 + c50 + cmiss)

        # Standard accuracy formula: (300*c300 + 100*c100 + 50*c50) / (300*total)
        accuracy = (300 * c300 + 100 * c100 + 50 * c50) / (300 * total)

        ratio_300 = c300 / total
        ratio_50 = c50 / total

        # Official grading rules:
        if c300 == total and cmiss == 0:
            grade = "SS"
        elif ratio_300 > 0.90 and ratio_50 < 0.01 and cmiss == 0:
            grade = "S"
        elif (ratio_300 > 0.80 and cmiss == 0) or ratio_300 > 0.90:
            grade = "A"
        elif (ratio_300 > 0.70 and cmiss == 0) or ratio_300 > 0.80:
            grade = "B"
        elif ratio_300 > 0.60:
            grade = "C"
        else:
            grade = "D"

        retry_rect = pygame.Rect(self.width // 2 - 160, 485, 140, 48)
        menu_rect = pygame.Rect(self.width // 2 + 20, 485, 140, 48)

        while True:
            fade_progress = min(1.0, (pygame.time.get_ticks() - time_start) / 600.0)
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_clicked = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and (event.mod & pygame.KMOD_CTRL):
                        return "retry"
                    if event.key in (pygame.K_ESCAPE, pygame.K_m, pygame.K_RETURN):
                        return "menu"

            if mouse_clicked:
                if retry_rect.collidepoint(mouse_pos):
                    return "retry"
                if menu_rect.collidepoint(mouse_pos):
                    return "menu"

            self.screen.fill(self.BG_COLOR)
            self._draw_centered("RESULTS", self.font_med, self.TEXT_COLOR, 70)
            self._draw_centered(grade, pygame.font.SysFont("Arial", 90, bold=True), self.ACCENT_COLOR, 175)
            self._draw_centered(f"Accuracy  {accuracy * 100:.2f}%", self.font_med, self.TEXT_COLOR, 270)
            self._draw_centered(f"Score  {int(score):06d}    Max combo  {max_combo}x", self.font_small, self.TEXT_COLOR, 315)
            self._draw_centered(f"PERFECT {counts['perfect']}   GREAT {counts['great']}   GOOD {counts['good']}   MISS {counts['miss']}", self.font_small, self.MUTED_COLOR, 355)
            mod_str = " ".join(sorted(GlobalState.active_mods)) if GlobalState.active_mods else "None"
            mult = GlobalState.get_score_multiplier()
            self._draw_centered(f"UR: {ur_value:.1f}  |  Mods: {mod_str} ({mult:.2f}x)", self.font_small, self.MUTED_COLOR, 390)
            self._draw_centered("CTRL+R to retry   |   ENTER / ESC to menu", self.font_small, (80, 80, 110), 440)

            self._draw_button("RETRY", retry_rect, retry_rect.collidepoint(mouse_pos))
            self._draw_button("MENU", menu_rect, menu_rect.collidepoint(mouse_pos))

            if fade_progress < 1.0:
                fade_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                fade_surf.fill((0, 0, 0, int(255 * (1.0 - fade_progress))))
                self.screen.blit(fade_surf, (0, 0))

            if last_frame:
                if fade_progress < 1.0:
                    if not hasattr(self, 'results_trans') or self.results_trans['time_start'] != time_start:
                        mx, my = pygame.mouse.get_pos()
                        trans_tiles = []
                        for y in range(0, self.height, 40):
                            for x in range(0, self.width, 40):
                                cx = x + 20
                                cy = y + 20
                                dist = math.hypot(cx - mx, cy - my)
                                trans_tiles.append({
                                    'x': x, 'y': y, 'dist': dist,
                                    'vx': (cx - mx) / (dist + 1) * random.uniform(200, 900),
                                    'vy': (cy - my) / (dist + 1) * random.uniform(200, 900),
                                    'delay': dist / 1800.0
                                })
                        self.results_trans = {'tiles': trans_tiles, 'mx': mx, 'my': my, 'time_start': time_start}

                    for t in self.results_trans['tiles']:
                        local_p = (fade_progress - t['delay']) / 0.4
                        if local_p <= 0:
                            self.screen.blit(last_frame, (t['x'], t['y']), pygame.Rect(t['x'], t['y'], 40, 40))
                        elif local_p < 1:
                            ease_p = 1.0 - (1.0 - local_p)**3
                            nx = t['x'] + t['vx'] * ease_p
                            ny = t['y'] + t['vy'] * ease_p
                            s = int(40 * (1.0 - ease_p))
                            if s > 0:
                                self.screen.blit(last_frame, (int(nx + 20 - s/2), int(ny + 20 - s/2)), pygame.Rect(t['x'], t['y'], s, s))

                    shock_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    shockwave_radius = fade_progress * 2000
                    shockwave_thickness = int(max(1, 200 * (1.0 - fade_progress)))
                    if shockwave_radius > 0:
                        pygame.draw.circle(shock_surf, (0, 229, 255, int(255 * (1.0 - fade_progress))), (self.results_trans['mx'], self.results_trans['my']), int(shockwave_radius), shockwave_thickness)
                        for _ in range(40):
                            angle = random.uniform(0, math.pi * 2)
                            r_offset = random.uniform(-shockwave_thickness, shockwave_thickness * 1.5)
                            px = self.results_trans['mx'] + math.cos(angle) * (shockwave_radius + r_offset)
                            py = self.results_trans['my'] + math.sin(angle) * (shockwave_radius + r_offset)
                            psize = random.randint(2, 8)
                            palpha = int(255 * (1.0 - fade_progress) * random.uniform(0.5, 1.0))
                            pygame.draw.circle(shock_surf, (0, 255, 255, palpha), (int(px), int(py)), psize)
                    self.screen.blit(shock_surf, (0, 0))
                else:
                    last_frame = None

            pygame.display.flip()
            clock.tick(30)

    @staticmethod
    def _get_dt_audio_path(audio_path: str) -> str:
        """Returns path to 1.5x sped-up audio file, generating and caching it if needed."""
        if not audio_path or not os.path.exists(audio_path):
            return audio_path

        cache_path = os.path.splitext(audio_path)[0] + "_dt15.wav"
        if os.path.exists(cache_path):
            return cache_path

        try:
            import numpy as np

            orig = pygame.mixer.Sound(audio_path)
            raw = orig.get_raw()
            arr = np.frombuffer(raw, dtype=np.int16).reshape(-1, 2)
            target_len = int(len(arr) / 1.5)
            indices = (np.arange(target_len) * 1.5).astype(np.int64)
            fast_arr = arr[indices]

            with wave.open(cache_path, "wb") as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframes(fast_arr.tobytes())

            return cache_path
        except Exception as e:
            print(f"Warning: Failed to generate DT audio: {e}")
            return audio_path

    def run(self, last_frame=None):
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        song_data = GlobalState.selected_song_data
        
        # Load background art if available and brightness > 0
        bg_surface = None
        bg_path = song_data.get("background_path", "")
        if bg_path and GlobalState.bg_brightness > 0.0:
            try:
                raw_bg = pygame.image.load(bg_path).convert()
                bg_surface = pygame.transform.smoothscale(raw_bg, (self.width, self.height))
                if GlobalState.bg_brightness < 1.0:
                    dark_tint = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    dim_alpha = int(255 * (1.0 - max(0.0, min(1.0, GlobalState.bg_brightness))))
                    dark_tint.fill((10, 10, 15, dim_alpha))
                    bg_surface.blit(dark_tint, (0, 0))
            except Exception:
                bg_surface = None

        # Load audio (use 1.5x sped-up audio if DoubleTime is active)
        audio_to_play = song_data.get("audio_path", "")
        if "DT" in GlobalState.active_mods and audio_to_play:
            audio_to_play = self._get_dt_audio_path(audio_to_play)

        try:
            pygame.mixer.music.load(audio_to_play)
            pygame.mixer.music.set_volume(GlobalState.music_volume)
        except Exception:
            print("Audio file missing, running silent simulation.")

        hit_times = BeatmapParser.load_osu_beatmap(song_data.get("osu_path", ""))
        if not hit_times:
            hit_times = [1.0 + i * 0.6 for i in range(50)]

        # Generate sequence of words matching note count
        words_list = WordGenerator.get_word_sequence(len(hit_times))

        notes = []
        word_index = 0
        char_index = 0

        for t in hit_times:
            current_word = words_list[word_index]
            char = current_word[char_index]
            notes.append({
                "target_time": t,
                "char": char,
                "word_index": word_index,
                "char_index": char_index,
                "x": self.target_x + self.SPAWN_DISTANCE,
                "hit": False,
                "missed": False
            })
            char_index += 1
            if char_index >= len(current_word):
                word_index += 1
                char_index = 0

        conductor = Conductor(bpm=song_data.get("bpm", 130.0))
        
        # Countdown & Skip Intro State Variables
        countdown_timer = 3.0
        countdown_active = True
        first_note_time = hit_times[0] if hit_times else 999.0

        score = 0
        combo = 0
        max_combo = 0
        hp = GlobalState.hp
        counts = {"perfect": 0, "great": 0, "good": 0, "miss": 0}

        current_note_idx = 0

        # Game Mods configuration
        mod_score_mult = GlobalState.get_score_multiplier()
        is_hr = "HR" in GlobalState.active_mods
        is_sd = "SD" in GlobalState.active_mods
        is_pf = "PF" in GlobalState.active_mods
        is_nf = "NF" in GlobalState.active_mods
        hp_miss_drain = 12.0 if is_hr else 8.0
        hp_wrong_drain = 8.0 if is_hr else 5.0

        # Animation & Feedback State Variables
        feedback_text = ""
        feedback_timer = 0.0
        feedback_max_time = 0.35
        feedback_y_offset = 0.0
        hit_ripples = []
        particles = []
        display_hp = float(hp)
        combo_pop_timer = 0.0

        # O(1) Running Unstable Rate (UR) tracking
        timing_errors = []
        err_count = 0
        err_sum = 0.0
        err_sum_sq = 0.0
        ur_value = 0.0

        # Monkeytype HUD cached render surfaces
        cached_hud_idx = -1
        cached_hud_surfs = []
        cached_hud_total_w = 0

        clock = pygame.time.Clock()
        target_fps = get_fps_target(GlobalState.fps_mode)

        song_ended = False
        end_cooldown = 1.0

        IGNORED_KEYS = {
            pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LCTRL, pygame.K_RCTRL,
            pygame.K_LALT, pygame.K_RALT, pygame.K_CAPSLOCK, pygame.K_TAB,
            pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
            pygame.K_HOME, pygame.K_END, pygame.K_PAGEUP, pygame.K_PAGEDOWN
        }

        time_start = pygame.time.get_ticks()
        running = True
        while running:
            dt = clock.tick(target_fps) / 1000.0
            mouse_pos = pygame.mouse.get_pos()

            speed_multiplier = GlobalState.note_speed / 9.0
            current_speed = self.SCROLL_SPEED * speed_multiplier
            max_travel_time = self.SPAWN_DISTANCE / current_speed
            intro_end_time = max(0.0, first_note_time - max_travel_time - 0.8)

            if countdown_active:
                countdown_timer -= dt
                current_time = -max(0.0, countdown_timer)
                if countdown_timer <= 0:
                    countdown_timer = 0.0
                    countdown_active = False
                    conductor.start_song()
            else:
                conductor.update()
                current_time = conductor.song_position

            can_skip_intro = (not countdown_active and current_time < intro_end_time and intro_end_time > 2.0)

            # Check missed notes at head of queue
            while current_note_idx < len(notes):
                target_note = notes[current_note_idx]
                if current_time > target_note["target_time"] + self.MISS_WINDOW:
                    target_note["missed"] = True
                    counts["miss"] += 1
                    hp = max(0.0, hp - hp_miss_drain)
                    if is_sd or is_pf:
                        hp = 0.0
                    feedback_text = "MISS"
                    self._play_miss_sound()
                    combo = 0
                    feedback_timer = feedback_max_time
                    feedback_y_offset = 0.0
                    hp_drop_w = (self.width - 450) * (hp_miss_drain / 100.0)
                    chunk_x = 350 + (self.width - 450) * (hp / 100.0)
                    ratio = max(0.0, min(1.0, hp / 100.0))
                    chunk_col = (int(255 + (0 - 255) * ratio), int(70 + (229 - 70) * ratio), int(70 + (255 - 70) * ratio))
                    particles.append({
                        "x": chunk_x, "y": 30, "w": hp_drop_w, "h": 22,
                        "vx": random.uniform(50, 100), "vy": random.uniform(-150, -50),
                        "rot": 0.0, "vrot": random.uniform(-5, 5),
                        "life": 0.8, "max_life": 0.8,
                        "color": chunk_col, "type": "chunk"
                    })
                    current_note_idx += 1
                else:
                    break

            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    conductor.stop()
                    return "quit"
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    skip_rect = pygame.Rect(self.width // 2 - 130, self.height - 110, 260, 44)
                    if skip_rect.collidepoint(event.pos):
                        if countdown_active:
                            countdown_active = False
                            countdown_timer = 0.0
                            conductor.start_song()
                            if intro_end_time > 2.0:
                                conductor.seek(intro_end_time)
                        elif can_skip_intro:
                            conductor.seek(intro_end_time)
                elif event.type == pygame.KEYDOWN:
                    # Instant track retry via Ctrl + R
                    if event.key == pygame.K_r and (event.mod & pygame.KMOD_CTRL):
                        conductor.stop()
                        return "play"

                    if event.key == pygame.K_ESCAPE:
                        pause_result = self._pause_screen(conductor, clock)
                        if pause_result != "resume":
                            conductor.stop()
                            return "quit" if pause_result == "quit" else "play" if pause_result == "retry" else "menu"
                        continue

                    # SPACE key skips countdown or intro
                    if event.key == pygame.K_SPACE:
                        if countdown_active:
                            countdown_active = False
                            countdown_timer = 0.0
                            conductor.start_song()
                            if intro_end_time > 2.0:
                                conductor.seek(intro_end_time)
                        elif can_skip_intro:
                            conductor.seek(intro_end_time)
                        continue

                    # Filter modifier and navigation keys
                    if event.key in IGNORED_KEYS:
                        continue

                    # Extract alphanumeric character
                    key_char = ""
                    if event.unicode and event.unicode.isalpha():
                        key_char = event.unicode.upper()
                    else:
                        name = pygame.key.name(event.key).upper()
                        if len(name) == 1 and 'A' <= name <= 'Z':
                            key_char = name

                    if not key_char:
                        continue

                    if current_note_idx < len(notes):
                        active_note = notes[current_note_idx]
                        time_error = current_time - active_note["target_time"]
                        abs_err = abs(time_error)

                        if abs_err <= self.MISS_WINDOW:
                            if key_char == active_note["char"]:
                                error_ms = time_error * 1000.0
                                timing_errors.append(error_ms)

                                # O(1) Running variance calculation
                                err_count += 1
                                err_sum += error_ms
                                err_sum_sq += error_ms * error_ms
                                if err_count > 1:
                                    mean_err = err_sum / err_count
                                    variance = max(0.0, (err_sum_sq / err_count) - (mean_err * mean_err))
                                    ur_value = math.sqrt(variance) * 10.0

                                if abs_err <= self.PERFECT_WINDOW:
                                    feedback_text = "PERFECT!"
                                    score += 300 * (1 + combo * 0.1) * mod_score_mult
                                    combo += 1
                                    counts["perfect"] += 1
                                    hp = min(100.0, hp + 1.0)
                                    for _ in range(12):
                                        angle = random.uniform(0, math.pi * 2)
                                        speed = random.uniform(150, 400)
                                        particles.append({
                                            "x": self.target_x,
                                            "y": self.lane_y,
                                            "vx": math.cos(angle) * speed,
                                            "vy": math.sin(angle) * speed,
                                            "life": random.uniform(0.4, 0.8),
                                            "max_life": 0.8,
                                            "color": (255, 215, 0),
                                            "type": "glitter",
                                            "size": random.uniform(2, 6)
                                        })
                                elif abs_err <= self.GREAT_WINDOW:
                                    feedback_text = "GREAT!"
                                    score += 150 * (1 + combo * 0.1) * mod_score_mult
                                    combo += 1
                                    counts["great"] += 1
                                    hp = min(100.0, hp + 0.5)
                                    if is_pf:
                                        hp = 0.0
                                else:
                                    feedback_text = "GOOD"
                                    score += 50 * (1 + combo * 0.1) * mod_score_mult
                                    combo += 1
                                    counts["good"] += 1
                                    if is_pf:
                                        hp = 0.0

                                self._play_hitsound()
                                active_note["hit"] = True
                                feedback_timer = feedback_max_time
                                feedback_y_offset = 0.0
                                combo_pop_timer = 0.15

                                if combo > max_combo:
                                    max_combo = combo

                                # Expanding ripple animation
                                hit_ripples.append({
                                    "x": self.target_x,
                                    "y": self.lane_y,
                                    "radius": 35.0,
                                    "alpha": 255.0,
                                    "color": (0, 255, 180) if abs_err <= self.PERFECT_WINDOW else (100, 220, 255) if abs_err <= self.GREAT_WINDOW else (255, 200, 0)
                                })

                                current_note_idx += 1
                            else:
                                feedback_text = "WRONG"
                                self._play_miss_sound()
                                combo = 0
                                hp = max(0.0, hp - hp_wrong_drain)
                                if is_sd or is_pf:
                                    hp = 0.0
                                feedback_timer = feedback_max_time
                                feedback_y_offset = 0.0
                                hp_drop_w = (self.width - 450) * (hp_wrong_drain / 100.0)
                                chunk_x = 350 + (self.width - 450) * (hp / 100.0)
                                ratio = max(0.0, min(1.0, hp / 100.0))
                                chunk_col = (int(255 + (0 - 255) * ratio), int(70 + (229 - 70) * ratio), int(70 + (255 - 70) * ratio))
                                particles.append({
                                    "x": chunk_x, "y": 30, "w": hp_drop_w, "h": 22,
                                    "vx": random.uniform(50, 100), "vy": random.uniform(-150, -50),
                                    "rot": 0.0, "vrot": random.uniform(-5, 5),
                                    "life": 0.8, "max_life": 0.8,
                                    "color": chunk_col, "type": "chunk"
                                })

            # Fail condition (ignored if No Fail mod is active)
            if hp <= 0 and not is_nf:
                conductor.stop()
                last_frame = self.screen.copy()
                return self._show_fail_screen(score, max_combo, clock, last_frame)

            # Completion condition
            if current_note_idx >= len(notes):
                song_ended = True

            if song_ended:
                end_cooldown -= dt
                if end_cooldown <= 0.0:
                    conductor.stop()
                    last_frame = self.screen.copy()
                    return self._show_results(score, max_combo, timing_errors, counts, ur_value, clock, last_frame)

            # --- RENDERING ---
            if bg_surface:
                self.screen.blit(bg_surface, (0, 0))
            else:
                self.screen.fill(self.BG_COLOR)

            # Styled HP bar & Particles Update
            display_hp += (hp - display_hp) * 10.0 * dt
            
            hp_bar_w = self.width - 450
            skew = 15
            
            ratio = max(0.0, min(1.0, display_hp / 100.0))
            fill_color = (
                int(255 + (0 - 255) * ratio),
                int(70 + (229 - 70) * ratio),
                int(70 + (255 - 70) * ratio)
            )

            bg_poly = [(350 + skew, 30), (350 + hp_bar_w, 30), (350 + hp_bar_w - skew, 52), (350, 52)]
            pygame.draw.polygon(self.screen, (22, 22, 30), bg_poly)
            
            fill_w = int(hp_bar_w * ratio)
            if fill_w > 0:
                fill_poly = [(350 + skew, 30), (350 + fill_w, 30), (350 + max(0, fill_w - skew), 52), (350, 52)]
                pygame.draw.polygon(self.screen, fill_color, fill_poly)
                
            pygame.draw.polygon(self.screen, (45, 48, 65), bg_poly, 2)
            
            hp_label = self.font_small.render(f"HP {display_hp:.0f}%", True, fill_color)
            self.screen.blit(hp_label, (self.width - 90, 32))
            
            # Particle Render
            active_particles = []
            for p in particles:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                if p["type"] == "chunk":
                    p["vy"] += 500 * dt
                    p["rot"] += p["vrot"] * 60 * dt
                elif p["type"] == "damage":
                    p["vy"] += 500 * dt
                else:
                    p["vy"] += 200 * dt
                p["life"] -= dt
                if p["life"] > 0:
                    alpha = max(0, int(255 * (p["life"] / p["max_life"])))
                    if p["type"] == "chunk":
                        cw, ch = int(p["w"]), int(p["h"])
                        if cw > 0:
                            surf = pygame.Surface((cw + skew, ch), pygame.SRCALPHA)
                            local_poly = [(skew, 0), (cw, 0), (max(0, cw - skew), ch), (0, ch)]
                            pygame.draw.polygon(surf, (*p["color"], alpha), local_poly)
                            rotated = pygame.transform.rotate(surf, p["rot"])
                            self.screen.blit(rotated, (p["x"], p["y"]))
                    else:
                        size = max(1, int(p.get("size", 2) * (p["life"] / p["max_life"])))
                        if size > 0:
                            p_surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                            if p["type"] == "glitter":
                                pygame.draw.circle(p_surf, (*p["color"], alpha), (size, size), size)
                            else:
                                pygame.draw.rect(p_surf, (*p["color"], alpha), (0, 0, size*2, size*2))
                            self.screen.blit(p_surf, (p["x"] - size, p["y"] - size))
                    active_particles.append(p)
            particles = active_particles

            # Render Active Mod Badges on HUD
            if GlobalState.active_mods:
                badge_x = self.width - 50
                for mod_name in sorted(GlobalState.active_mods):
                    badge_rect = pygame.Rect(badge_x - 38, 65, 38, 22)
                    pygame.draw.rect(self.screen, (40, 40, 60), badge_rect, border_radius=4)
                    pygame.draw.rect(self.screen, self.ACCENT_COLOR, badge_rect, 1, border_radius=4)
                    b_txt = self.font_small.render(mod_name, True, self.ACCENT_COLOR)
                    self.screen.blit(b_txt, b_txt.get_rect(center=badge_rect.center))
                    badge_x -= 44

            # Horizontal Target Lane & Ambient Rings
            pygame.draw.line(self.screen, (0, 100, 120), (0, self.lane_y), (self.width, self.lane_y), 8)
            pygame.draw.line(self.screen, self.ACCENT_COLOR, (0, self.lane_y), (self.width, self.lane_y), 2)
            
            beat_progress = (conductor.song_position / (60.0 / conductor.bpm)) % 1.0 if conductor.bpm > 0 else 0
            pulse_radius = 45 + 5 * (1.0 - beat_progress)
            
            pygame.draw.circle(self.screen, (25, 25, 38), (self.target_x, self.lane_y), int(pulse_radius))
            pygame.draw.circle(self.screen, self.ACCENT_COLOR, (self.target_x, self.lane_y), int(pulse_radius), 3)
            pygame.draw.circle(self.screen, (0, 100, 120), (self.target_x, self.lane_y), int(pulse_radius) + 3, 2)

            # Update & Render Expanding Hit Ripples
            active_ripples = []
            for ripple in hit_ripples:
                ripple["radius"] += 120.0 * dt
                ripple["alpha"] -= 500.0 * dt
                if ripple["alpha"] > 0 and ripple["radius"] < 75:
                    r_rad = int(ripple["radius"])
                    r_alpha = max(0, min(255, ripple["alpha"]))
                    r_surf = pygame.Surface((r_rad * 2 + 4, r_rad * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(r_surf, (*ripple["color"], r_alpha), (r_rad + 2, r_rad + 2), r_rad, 3)
                    self.screen.blit(r_surf, (ripple["x"] - r_rad - 2, ripple["y"] - r_rad - 2))
                    active_ripples.append(ripple)
            hit_ripples = active_ripples

            # Render Scrolling Notes using pre-baked surfaces (zero per-frame allocations)
            for idx in range(current_note_idx, len(notes)):
                n = notes[idx]
                time_left = n["target_time"] - current_time

                if time_left > max_travel_time:
                    break

                n["x"] = self.target_x + (time_left * current_speed)

                if -50 <= n["x"] <= self.width + 50:
                    dist_from_spawn = (self.target_x + self.SPAWN_DISTANCE) - n["x"]
                    alpha_factor = min(1.0, max(0.0, dist_from_spawn / 100.0)) if dist_from_spawn < 100 else 1.0

                    base_tile = self.note_surfaces.get(n["char"])
                    if base_tile:
                        if alpha_factor < 1.0:
                            faded = base_tile.copy()
                            faded.set_alpha(int(255 * alpha_factor))
                            self.screen.blit(faded, (n["x"] - 35, self.lane_y - 35))
                        else:
                            self.screen.blit(base_tile, (n["x"] - 35, self.lane_y - 35))

            # --- MONKEYTYPE-STYLE UPCOMING WORDS GUIDE (Cached) ---
            hud_y = self.lane_y + 120
            
            panel_w = 700
            panel_rect = pygame.Rect(self.width // 2 - panel_w // 2, hud_y - 25, panel_w, 95)
            panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (15, 15, 22, 190), panel_surf.get_rect(), border_radius=12)
            pygame.draw.rect(panel_surf, (45, 48, 65, 220), panel_surf.get_rect(), 2, border_radius=12)
            self.screen.blit(panel_surf, panel_rect)

            guide_label = self.font_small.render("UPCOMING WORDS", True, self.MUTED_COLOR)
            self.screen.blit(guide_label, (self.width // 2 - guide_label.get_width() // 2, hud_y - 15))
            
            # Left side of panel: Max Combo
            mc_lbl = self.font_small.render("MAX COMBO: ", True, self.MUTED_COLOR)
            mc_val = self.font_small.render(f"{max_combo}x", True, self.TEXT_COLOR)
            self.screen.blit(mc_lbl, (panel_rect.left + 25, hud_y - 15))
            self.screen.blit(mc_val, (panel_rect.left + 25 + mc_lbl.get_width(), hud_y - 15))
            
            # Right side of panel: UR (Unstable Rate)
            ur_lbl = self.font_small.render("UR: ", True, self.MUTED_COLOR)
            ur_col = self.TEXT_COLOR
            if ur_value > 0:
                if ur_value < 100: ur_col = self.ACCENT_COLOR
                elif ur_value > 150: ur_col = (255, 70, 70)
            ur_val = self.font_small.render(f"{ur_value:.1f}" if ur_value > 0 else "---", True, ur_col)
            ur_start_x = panel_rect.right - 25 - (ur_lbl.get_width() + ur_val.get_width())
            self.screen.blit(ur_lbl, (ur_start_x, hud_y - 15))
            self.screen.blit(ur_val, (ur_start_x + ur_lbl.get_width(), hud_y - 15))

            if current_note_idx < len(notes):
                # Re-render HUD only when active note index changes
                if current_note_idx != cached_hud_idx:
                    cached_hud_idx = current_note_idx
                    cached_hud_surfs = []
                    cached_hud_total_w = 0

                    active_note = notes[current_note_idx]
                    cur_w_idx = active_note["word_index"]
                    cur_c_idx = active_note["char_index"]
                    cur_word = words_list[cur_w_idx] if cur_w_idx < len(words_list) else ""

                    # 1. Completed letters (Green)
                    if cur_c_idx > 0:
                        s = self.font_guide.render(cur_word[:cur_c_idx], True, self.GREEN_COLOR)
                        cached_hud_surfs.append(s)
                        cached_hud_total_w += s.get_width()

                    # 2. Active target letter (Cyan)
                    s = self.font_guide.render(cur_word[cur_c_idx], True, self.ACCENT_COLOR)
                    cached_hud_surfs.append(s)
                    cached_hud_total_w += s.get_width()

                    # 3. Remaining letters of current word (White)
                    if cur_c_idx + 1 < len(cur_word):
                        s = self.font_guide.render(cur_word[cur_c_idx + 1:], True, self.TEXT_COLOR)
                        cached_hud_surfs.append(s)
                        cached_hud_total_w += s.get_width()

                    # 4. Next upcoming words (up to 4 words)
                    subsequent_words = words_list[cur_w_idx + 1: cur_w_idx + 5]
                    for sub_w in subsequent_words:
                        s = self.font_guide.render("  " + sub_w, True, self.MUTED_COLOR)
                        cached_hud_surfs.append(s)
                        cached_hud_total_w += s.get_width()

                cur_x = self.width // 2 - cached_hud_total_w // 2
                for surf in cached_hud_surfs:
                    self.screen.blit(surf, (cur_x, hud_y + 30))
                    cur_x += surf.get_width()

            # --- HUD: Score & Combo ---
            score_surf = self.font_score.render(f"{int(score):06d}", True, self.TEXT_COLOR)
            self.screen.blit(score_surf, (50, 24))

            if combo > 1:
                combo_surf = self.font_combo.render(f"{combo}x", True, self.ACCENT_COLOR)
                combo_rect = combo_surf.get_rect(center=(self.width // 2, self.lane_y - 75))
                self.screen.blit(combo_surf, combo_rect)

            # Judgement Popups (without per-frame allocations)
            if feedback_timer > 0:
                feedback_timer -= dt
                feedback_y_offset -= 30.0 * dt

                progress_ratio = feedback_timer / feedback_max_time
                current_alpha = max(0, min(255, int(255 * progress_ratio)))

                base_judgement = self.judgement_surfaces.get(feedback_text)
                if base_judgement:
                    base_judgement.set_alpha(current_alpha)
                    self.screen.blit(base_judgement, base_judgement.get_rect(center=(self.target_x, self.lane_y - 90 + feedback_y_offset)))

            # --- Countdown Overlay ---
            if countdown_active and countdown_timer > 0:
                count_num = math.ceil(countdown_timer)
                count_str = str(count_num) if count_num > 0 else "GO!"

                cnt_font = pygame.font.SysFont("Arial", 110, bold=True)
                cnt_surf = cnt_font.render(count_str, True, self.ACCENT_COLOR)
                cnt_rect = cnt_surf.get_rect(center=(self.width // 2, self.height // 2 - 20))
                self.screen.blit(cnt_surf, cnt_rect)

                cnt_sub = self.font_small.render("GET READY!   |   Press SPACE or Click to Skip", True, self.TEXT_COLOR)
                self.screen.blit(cnt_sub, cnt_sub.get_rect(center=(self.width // 2, self.height // 2 + 50)))

            # --- Skip Intro Button ---
            elif can_skip_intro:
                skip_rect = pygame.Rect(self.width // 2 - 130, self.height - 110, 260, 44)
                is_skip_hovered = skip_rect.collidepoint(mouse_pos)

                s_bg = self.ACCENT_COLOR if is_skip_hovered else (24, 24, 34)
                s_border = (120, 240, 255) if is_skip_hovered else self.ACCENT_COLOR
                s_fg = (10, 10, 15) if is_skip_hovered else self.ACCENT_COLOR

                s_surf = pygame.Surface((260, 44), pygame.SRCALPHA)
                pygame.draw.rect(s_surf, (*s_bg, 230), (0, 0, 260, 44), border_radius=10)
                self.screen.blit(s_surf, skip_rect)
                pygame.draw.rect(self.screen, s_border, skip_rect, 2, border_radius=10)

                txt = self.font_guide.render("SKIP INTRO  [SPACE]", True, s_fg)
                self.screen.blit(txt, txt.get_rect(center=skip_rect.center))


            if last_frame:
                fade_progress = min(1.0, (pygame.time.get_ticks() - time_start) / 600.0)
                if fade_progress < 1.0:
                    if not hasattr(self, 'run_trans') or self.run_trans['time_start'] != time_start:
                        mx, my = pygame.mouse.get_pos()
                        trans_tiles = []
                        for y in range(0, self.height, 40):
                            for x in range(0, self.width, 40):
                                cx = x + 20
                                cy = y + 20
                                dist = math.hypot(cx - mx, cy - my)
                                trans_tiles.append({
                                    'x': x, 'y': y, 'dist': dist,
                                    'vx': (cx - mx) / (dist + 1) * random.uniform(200, 900),
                                    'vy': (cy - my) / (dist + 1) * random.uniform(200, 900),
                                    'delay': dist / 1800.0
                                })
                        self.run_trans = {'tiles': trans_tiles, 'mx': mx, 'my': my, 'time_start': time_start}

                    for t in self.run_trans['tiles']:
                        local_p = (fade_progress - t['delay']) / 0.4
                        if local_p <= 0:
                            self.screen.blit(last_frame, (t['x'], t['y']), pygame.Rect(t['x'], t['y'], 40, 40))
                        elif local_p < 1:
                            ease_p = 1.0 - (1.0 - local_p)**3
                            nx = t['x'] + t['vx'] * ease_p
                            ny = t['y'] + t['vy'] * ease_p
                            s = int(40 * (1.0 - ease_p))
                            if s > 0:
                                self.screen.blit(last_frame, (int(nx + 20 - s/2), int(ny + 20 - s/2)), pygame.Rect(t['x'], t['y'], s, s))

                    shock_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    shockwave_radius = fade_progress * 2000
                    shockwave_thickness = int(max(1, 200 * (1.0 - fade_progress)))
                    if shockwave_radius > 0:
                        pygame.draw.circle(shock_surf, (0, 229, 255, int(255 * (1.0 - fade_progress))), (self.run_trans['mx'], self.run_trans['my']), int(shockwave_radius), shockwave_thickness)
                        for _ in range(40):
                            angle = random.uniform(0, math.pi * 2)
                            r_offset = random.uniform(-shockwave_thickness, shockwave_thickness * 1.5)
                            px = self.run_trans['mx'] + math.cos(angle) * (shockwave_radius + r_offset)
                            py = self.run_trans['my'] + math.sin(angle) * (shockwave_radius + r_offset)
                            psize = random.randint(2, 8)
                            palpha = int(255 * (1.0 - fade_progress) * random.uniform(0.5, 1.0))
                            pygame.draw.circle(shock_surf, (0, 255, 255, palpha), (int(px), int(py)), psize)
                    self.screen.blit(shock_surf, (0, 0))
                else:
                    last_frame = None

            pygame.display.flip()

        conductor.stop()
        return "menu"