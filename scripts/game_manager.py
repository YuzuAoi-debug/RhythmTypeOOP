import os
import wave
import math
import random
import pygame
from global_state import GlobalState, get_fps_target
from conductor import Conductor
from beatmap_parser import BeatmapParser
from word_generator import WordGenerator
import score_db

class GameManager:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
                                             
        self.BG_COLOR = (14, 14, 18)
        self.LINE_COLOR = (40, 40, 56)
        self.TEXT_COLOR = (245, 245, 255)
        self.ACCENT_COLOR = (0, 229, 255)
        self.MUTED_COLOR = (100, 100, 130)
        self.GREEN_COLOR = (0, 255, 180)
        
                                          
        from global_state import get_asset_path
        font_retro = get_asset_path("assets/font/RETROTECH.ttf")
        font_game = get_asset_path("assets/font/Comfortaa-Bold.ttf")
               
        try:
            self.font_large = pygame.font.Font(font_game, 36)
            self.font_med = pygame.font.Font(font_game, 28)
            self.font_small = pygame.font.Font(font_game, 15)
            self.font_mono = pygame.font.Font(font_game, 12)
            self.font_guide = pygame.font.Font(font_game, 18) 
            self.font_score = pygame.font.Font(font_game, 40)
            self.font_combo = pygame.font.Font(font_game, 44)
                                                                          
            self.font_res_grade  = pygame.font.Font(font_game, 110)
            self.font_res_score  = pygame.font.Font(font_game, 38)
            self.font_res_stat   = pygame.font.Font(font_game, 20)
            self.font_res_label  = pygame.font.Font(font_game, 13)
            self.font_res_header = pygame.font.Font(font_game, 16)
            self.font_res_title  = pygame.font.Font(font_game, 22)
            self.font_res_artist = pygame.font.Font(font_game, 14)
            self.font_res_hint   = pygame.font.Font(font_game, 13)
        except Exception:
            self.font_large = pygame.font.SysFont("Arial", 44, bold=True)
            self.font_med = pygame.font.SysFont("Arial", 28, bold=True)
            self.font_small = pygame.font.SysFont("Arial", 16)
            self.font_mono = pygame.font.SysFont("Arial", 12)
            self.font_guide = pygame.font.SysFont("Arial", 22, bold=True)
            self.font_score = pygame.font.SysFont("Arial", 48, bold=True)
            self.font_combo = pygame.font.SysFont("Arial", 52, bold=True)
            self.font_res_grade  = pygame.font.SysFont("Arial", 110, bold=True)
            self.font_res_score  = pygame.font.SysFont("Arial",  38, bold=True)
            self.font_res_stat   = pygame.font.SysFont("Arial",  20, bold=True)
            self.font_res_label  = pygame.font.SysFont("Arial",  13)
            self.font_res_header = pygame.font.SysFont("Arial",  16)
            self.font_res_title  = pygame.font.SysFont("Arial",  22, bold=True)
            self.font_res_artist = pygame.font.SysFont("Arial",  14)
            self.font_res_hint   = pygame.font.SysFont("Arial",  13)

                                                            
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
                    
                            
        is_hr = "HR" in GlobalState.active_mods
        self.SCROLL_SPEED = 560.0 if is_hr else 400.0
        self.SPAWN_DISTANCE = 900.0
        
                                                       
        self.PERFECT_WINDOW = 0.028 if is_hr else 0.04                
        self.GREAT_WINDOW = 0.056 if is_hr else 0.08                  
        self.GOOD_WINDOW = 0.084 if is_hr else 0.12                    
        self.MISS_WINDOW = 0.105 if is_hr else 0.15                     
        
                                       
        self.target_x = 200
        self.lane_y = self.height // 2 - 50

                       
        self.hitsound = None
        self.miss_sound = None
        self.fail_sound = None
        self.fail_ambient_sound = None
        
        try:
            self.hitsound = pygame.mixer.Sound(GlobalState.HITSOUND_PATH)
            self.miss_sound = pygame.mixer.Sound(GlobalState.MISS_SOUND_PATH)
            self.hitsound.set_volume(GlobalState.sfx_volume)
            self.miss_sound.set_volume(GlobalState.sfx_volume)
            
            fail_path = get_asset_path("gameplay_audio/losesfx.mp3")
            if os.path.exists(fail_path):
                self.fail_sound = pygame.mixer.Sound(fail_path)
                
            ambient_path = get_asset_path("gameplay_audio/retrolose_sfx.mp3")
            if os.path.exists(ambient_path):
                self.fail_ambient_sound = pygame.mixer.Sound(ambient_path)
            else:
                print(f"[Audio Warning] Ambient file not found at: {ambient_path}")
                
        except Exception as e:
            print(f"Warning: Failed to load sound effects: {e}")

                                                                                                
        self.base_note_surf = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.rect(self.base_note_surf, (30, 30, 45, 225), (0, 0, 70, 70), border_radius=15)
        pygame.draw.rect(self.base_note_surf, (*self.ACCENT_COLOR, 255), (0, 0, 70, 70), 3, border_radius=15)

        self.note_surfaces = {}
        for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            surf = self.base_note_surf.copy()
            char_surf = self.font_med.render(c, True, self.TEXT_COLOR)
            surf.blit(char_surf, char_surf.get_rect(center=(35, 35)))
            self.note_surfaces[c] = surf

                                             
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
        
        if self.fail_sound:
            self.fail_sound.set_volume(max(0.2, float(GlobalState.sfx_volume)))
            self.fail_sound.play()
            
        self.ambient_channel = None
        if self.fail_ambient_sound:
            ambient_vol = max(0.04, min(0.9, float(GlobalState.music_volume) * 0.15))
            self.fail_ambient_sound.set_volume(ambient_vol)        
            self.ambient_channel = self.fail_ambient_sound.play(loops=-1, fade_ms=5200)
            
        retry_rect = pygame.Rect(self.width // 2 - 160, 390, 140, 48)
        menu_rect = pygame.Rect(self.width // 2 + 20, 390, 140, 48)

                                                        
        vignette_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        max_radius = int(math.hypot(self.width/2, self.height/2))
        for r in range(max_radius, 0, -15):
            alpha = max(0, min(150, int(150 * (r / max_radius))))
            pygame.draw.circle(vignette_surf, (15, 0, 5, alpha), (self.width // 2, self.height // 2), r)

                                                                                       
        gradient_h = 400
        wave_gradient = pygame.Surface((1, gradient_h), pygame.SRCALPHA)
        for y in range(gradient_h):
                                                        
            alpha_ratio = y / gradient_h
            alpha = int(255 * (alpha_ratio ** 2))
            wave_gradient.set_at((0, y), (20, 2, 4, alpha))
        wave_gradient = pygame.transform.scale(wave_gradient, (self.width, gradient_h))

                                        
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
                        if self.fail_ambient_sound:
                            self.fail_ambient_sound.fadeout(500)
                        return "retry"
                    if event.key in (pygame.K_ESCAPE, pygame.K_m, pygame.K_RETURN):
                        return "menu"

            if mouse_clicked:
                if retry_rect.collidepoint(mouse_pos):
                    if self.fail_ambient_sound:
                        self.fail_ambient_sound.fadeout(500)
                    return "retry"
                if menu_rect.collidepoint(mouse_pos):
                    if self.fail_ambient_sound:
                        self.fail_ambient_sound.fadeout(500)
                    return "menu"

            time_ms = pygame.time.get_ticks() - time_start
            fade_progress = min(1.0, time_ms / fade_duration)
            
            if fade_progress < 0.4:
                if last_frame:
                    self.screen.blit(last_frame, (0, 0))
                else:
                    self.screen.fill((10, 4, 6))
                
                                                              
                p = fade_progress / 0.4
                p = 1.0 - (1.0 - p)**3           
                start_offset = 350
                end_offset = -(self.height - 250) - 150
                wave_y_offset = start_offset + (end_offset - start_offset) * p
            else:
                                      
                self.screen.fill((10, 4, 6))
                
                                                                              
                p = (fade_progress - 0.4) / 0.6
                p = 1.0 - (1.0 - p)**3           
                start_offset = -(self.height - 250) - 150
                end_offset = 0
                wave_y_offset = start_offset + (end_offset - start_offset) * p
            
                                                                                
            for i in range(5):
                wave_pts = [(0, self.height)]
                base_y = self.height - 250 + i * 60 + wave_y_offset
                
                if i == 0:
                                                                                                      
                    self.screen.blit(wave_gradient, (0, int(base_y - gradient_h + 30)))
                    
                speed = 0.001 + i * 0.0002
                freq = 0.0015 + i * 0.0005
                amp = 20 + i * 10
                for x in range(0, self.width + 20, 10):
                                                                              
                    y = base_y                         + math.sin(time_ms * speed + x * freq) * amp                         + math.cos(time_ms * speed * 1.4 + x * freq * 2.3 + i) * (amp * 0.4)                         + math.sin(time_ms * speed * 0.8 + x * freq * 0.4 + i*2) * (amp * 0.2)
                    wave_pts.append((x, y))
                wave_pts.append((self.width, self.height))
                pygame.draw.polygon(self.screen, (20 + i*10, 2 + i*2, 4 + i*3), wave_pts)

                                                                                         
            if fade_progress > 0.4:
                ui_alpha_progress = min(1.0, (fade_progress - 0.4) / 0.6)
                
                                          
                pulse = (math.sin(time_ms * 0.003) + 1.0) * 0.5
                vignette_surf.set_alpha(int((100 + 55 * pulse) * ui_alpha_progress))
                self.screen.blit(vignette_surf, (0, 0))

                                                   
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

                                          
                pan_offset_y = int(math.sin(time_ms * 0.001) * 15)

                                      
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
        time_start = pygame.time.get_ticks()

        c300 = counts["perfect"]
        c100 = counts["great"]
        c50  = counts["good"]
        cmiss = counts["miss"]
        total = max(1, c300 + c100 + c50 + cmiss)

                                   
        accuracy = (300 * c300 + 100 * c100 + 50 * c50) / (300 * total)
        ratio_300 = c300 / total
        ratio_50  = c50  / total

                           
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

                                                  
        GRADE_COLORS = {
            "SS": (255, 215,  50),
            "S":  (255, 215,  50),
            "A":  ( 90, 230, 120),
            "B":  ( 80, 170, 255),
            "C":  (200, 120, 255),
            "D":  (255,  70,  70),
        }
        grade_color = GRADE_COLORS.get(grade, self.ACCENT_COLOR)

                                                      
        gc = grade_color
        glow_color = (gc[0], gc[1], gc[2])

                       
        song_data  = GlobalState.selected_song_data
        song_title = song_data.get("title", "Unknown Track")
        song_artist = song_data.get("artist", "")
        diff_name  = song_data.get("diff_name", "")
        bg_path    = song_data.get("background_path", "")

        mod_str = " + ".join(sorted(GlobalState.active_mods)) if GlobalState.active_mods else "No Mods"
        mult    = GlobalState.get_score_multiplier()

                                                                              
        W, H = self.width, self.height
        PANEL_TOP    = 72                              
        PANEL_BOTTOM = H - 80                          
        PANEL_H      = PANEL_BOTTOM - PANEL_TOP
        LEFT_W       = int(W * 0.46)                    
        RIGHT_X      = LEFT_W + 24
        RIGHT_W      = W - RIGHT_X - 20
        DIVIDER_X    = LEFT_W + 12

                                                                              
        bg_surf = None
        if bg_path:
            try:
                raw = pygame.image.load(bg_path).convert()
                bg_surf = pygame.transform.smoothscale(raw, (W, H))
            except Exception:
                bg_surf = None

                                     
        bg_dark = pygame.Surface((W, H), pygame.SRCALPHA)
        bg_dark.fill((8, 8, 14, 220))

                                                                              
        stars = []
        for _ in range(70):
            stars.append({
                "x":     random.uniform(0, W),
                "y":     random.uniform(0, H),
                "vy":    random.uniform(-25, -8),
                "vx":    random.uniform(-6, 6),
                "size":  random.uniform(1.2, 3.8),
                "alpha": random.randint(80, 200),
                "phase": random.uniform(0, math.pi * 2),
                "color": random.choice([
                    grade_color,
                    self.ACCENT_COLOR,
                    (255, 255, 255),
                ]),
            })

                                                                              
        font_grade   = self.font_res_grade
        font_score   = self.font_res_score
        font_stat    = self.font_res_stat
        font_label   = self.font_res_label
        font_header  = self.font_res_header
        font_title   = self.font_res_title
        font_artist  = self.font_res_artist
        font_hint    = self.font_res_hint

                                                                              
        def draw_glow_text(surf_dest, text, font, color, cx, cy, glow_radius=14, glow_passes=3):
            for r in range(glow_radius, 0, -glow_radius // glow_passes):
                alpha = int(120 * (1.0 - r / glow_radius))
                glow_s = font.render(text, True, color)
                glow_s.set_alpha(alpha)
                for dx in (-r, 0, r):
                    for dy in (-r, 0, r):
                        surf_dest.blit(glow_s, glow_s.get_rect(center=(cx + dx, cy + dy)))
            main_s = font.render(text, True, color)
            surf_dest.blit(main_s, main_s.get_rect(center=(cx, cy)))

                                                                              
        def draw_rounded_rect_alpha(surf_dest, rect, color_rgba, radius=12):
            s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, color_rgba, s.get_rect(), border_radius=radius)
            surf_dest.blit(s, rect.topleft)

        def draw_rounded_border(surf_dest, rect, color, width=2, radius=12):
            pygame.draw.rect(surf_dest, color, rect, width, border_radius=radius)

                                                                              
        CHIP_COLORS = {
            "PERFECT": ((0, 229, 255),   "300"),
            "GREAT":   ((100, 220, 255), "100"),
            "GOOD":    ((255, 190,  50), "50"),
            "MISS":    ((255,  70,  80), "0"),
        }

        def draw_judgment_card(surf_dest, rect, label, value, fg_color, ease_factor):
            draw_rounded_rect_alpha(surf_dest, rect, (18, 18, 28, int(220 * ease_factor)), radius=10)
            draw_rounded_border(surf_dest, rect, (*fg_color, int(80 * ease_factor)), width=1, radius=10)
                                        
            pill_rect = pygame.Rect(rect.x + 8, rect.y + 10, 5, rect.height - 20)
            pygame.draw.rect(surf_dest, (*fg_color, int(230 * ease_factor)), pill_rect, border_radius=3)
                                
            pts_tier = CHIP_COLORS.get(label, (fg_color, ""))[1]
            lbl_text = f"{label}  ({pts_tier})" if pts_tier else label
            lbl_s = font_label.render(lbl_text, True, fg_color)
            lbl_s.set_alpha(int(240 * ease_factor))
            surf_dest.blit(lbl_s, (rect.x + 22, rect.y + 11))
                   
            pct_s = font_hint.render(f"{value / total * 100:.1f}%", True, self.MUTED_COLOR)
            pct_s.set_alpha(int(180 * ease_factor))
            surf_dest.blit(pct_s, (rect.x + 22, rect.y + 30))
                              
            val_s = font_stat.render(f"{value:,}", True, (245, 245, 255))
            val_s.set_alpha(int(255 * ease_factor))
            surf_dest.blit(val_s, val_s.get_rect(midright=(rect.right - 16, rect.centery)))

                                                                              
        def draw_accuracy_arc(surf_dest, cx, cy, radius, pct, color, width=6):
            START_ANGLE = math.radians(220)
            ARC_SPAN    = math.radians(260)
            steps = 70
            end_step = int(steps * pct)
            for i in range(steps):
                a0 = START_ANGLE - (ARC_SPAN / steps) * i
                a1 = START_ANGLE - (ARC_SPAN / steps) * (i + 1)
                t  = i / max(1, steps - 1)
                r_c = int(color[0] * t + self.ACCENT_COLOR[0] * (1 - t))
                g_c = int(color[1] * t + self.ACCENT_COLOR[1] * (1 - t))
                b_c = int(color[2] * t + self.ACCENT_COLOR[2] * (1 - t))
                seg_color = (r_c, g_c, b_c) if i < end_step else (35, 35, 50)
                x0 = cx + math.cos(a0) * radius
                y0 = cy - math.sin(a0) * radius
                x1 = cx + math.cos(a1) * radius
                y1 = cy - math.sin(a1) * radius
                if abs(x1 - x0) > 0.5 or abs(y1 - y0) > 0.5:
                    pygame.draw.line(surf_dest, seg_color, (int(x0), int(y0)), (int(x1), int(y1)), width)

                                                                              
        is_new_pb = self._save_score(score, accuracy, grade, max_combo, counts)

                                                                              
        grade_bounce_vel = 0.0
        grade_bounce_pos = 0.0
        SPRING_K    = 280.0
        SPRING_DAMP = 14.0
        if last_frame and not hasattr(self, 'results_trans'):
            mx, my = pygame.mouse.get_pos()
            trans_tiles = []
            for ty in range(0, H, 40):
                for tx in range(0, W, 40):
                    cx2, cy2 = tx + 20, ty + 20
                    dist = math.hypot(cx2 - mx, cy2 - my)
                    trans_tiles.append({
                        'x': tx, 'y': ty, 'dist': dist,
                        'vx': (cx2 - mx) / (dist + 1) * random.uniform(200, 900),
                        'vy': (cy2 - my) / (dist + 1) * random.uniform(200, 900),
                        'delay': dist / 1800.0,
                    })
            self.results_trans = {'tiles': trans_tiles, 'mx': mx, 'my': my, 'time_start': time_start}

                                    
        BTN_Y    = H - 44
        BTN_H    = 42
        BTN_W    = 160
        retry_rect = pygame.Rect(W // 2 - BTN_W - 12, BTN_Y - BTN_H // 2, BTN_W, BTN_H)
        menu_rect  = pygame.Rect(W // 2 + 12,         BTN_Y - BTN_H // 2, BTN_W, BTN_H)

        dt_loop = 1.0 / 60.0
        display_score = 0.0

        mean_err = (sum(timing_errors) / len(timing_errors)) if timing_errors else 0.0

        while True:
            time_ms      = pygame.time.get_ticks() - time_start
            fade_progress = min(1.0, time_ms / 700.0)
            ease_p       = 1.0 - (1.0 - fade_progress) ** 3
            mouse_pos    = pygame.mouse.get_pos()
            mouse_clicked = False

                                    
            display_score += (score - display_score) * min(1.0, dt_loop * 6.0)

                                 
            if fade_progress < 1.0:
                target_pos = 0.0
                spring_force = -SPRING_K * (grade_bounce_pos - target_pos)
                damping_force = -SPRING_DAMP * grade_bounce_vel
                grade_bounce_vel += (spring_force + damping_force) * dt_loop
                grade_bounce_pos += grade_bounce_vel * dt_loop
                if time_ms < 50:
                    grade_bounce_pos = -50.0
                    grade_bounce_vel = 120.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_clicked = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and (event.mod & pygame.KMOD_CTRL):
                        if self.fail_ambient_sound:
                            self.fail_ambient_sound.stop()
                        return "retry"
                    if event.key in (pygame.K_ESCAPE, pygame.K_m, pygame.K_RETURN):
                        if self.fail_ambient_sound:
                            self.fail_ambient_sound.stop()
                        return "menu"

            if mouse_clicked:
                if retry_rect.collidepoint(mouse_pos):
                    return "retry"
                if menu_rect.collidepoint(mouse_pos):
                    return "menu"

                                                                              
            if bg_surf:
                self.screen.blit(bg_surf, (0, 0))
                self.screen.blit(bg_dark, (0, 0))
            else:
                self.screen.fill((10, 10, 16))

                                                                               
            if last_frame and fade_progress < 1.0 and hasattr(self, 'results_trans'):
                fp = fade_progress
                for t in self.results_trans['tiles']:
                    local_p = (fp - t['delay']) / 0.45
                    if local_p <= 0:
                        self.screen.blit(last_frame, (t['x'], t['y']),
                                         pygame.Rect(t['x'], t['y'], 40, 40))
                    elif local_p < 1:
                        ep = 1.0 - (1.0 - local_p) ** 3
                        nx = t['x'] + t['vx'] * ep
                        ny = t['y'] + t['vy'] * ep
                        s = int(40 * (1.0 - ep))
                        if s > 0:
                            self.screen.blit(last_frame,
                                             (int(nx + 20 - s/2), int(ny + 20 - s/2)),
                                             pygame.Rect(t['x'], t['y'], s, s))
                shock_surf = pygame.Surface((W, H), pygame.SRCALPHA)
                sr = fp * 2000
                st = int(max(1, 200 * (1.0 - fp)))
                if sr > 0:
                    pygame.draw.circle(shock_surf,
                                       (0, 229, 255, int(255 * (1.0 - fp))),
                                       (self.results_trans['mx'], self.results_trans['my']),
                                       int(sr), st)
                self.screen.blit(shock_surf, (0, 0))
            elif fade_progress >= 1.0:
                last_frame = None

                                                                               
            pulse_t = time_ms * 0.001
            for star in stars:
                star["x"] += star["vx"] * dt_loop
                star["y"] += star["vy"] * dt_loop
                if star["y"] < -10:
                    star["y"] = H + 10
                    star["x"] = random.uniform(0, W)
                pulse = (math.sin(pulse_t + star["phase"]) + 1.0) * 0.5
                a     = int(star["alpha"] * (0.5 + 0.5 * pulse) * ease_p)
                sz    = max(1, int(star["size"]))
                ss    = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(ss, (*star["color"], a), (sz, sz), sz)
                self.screen.blit(ss, (int(star["x"]) - sz, int(star["y"]) - sz))

                                                                              
            header_surf = pygame.Surface((W, 64), pygame.SRCALPHA)
            header_surf.fill((14, 14, 22, 220))
            pygame.draw.line(header_surf, (*self.ACCENT_COLOR, 100), (0, 63), (W, 63), 1)
            self.screen.blit(header_surf, (0, 0))

                                    
            res_lbl = font_header.render("RESULTS", True, self.ACCENT_COLOR)
            res_lbl.set_alpha(int(255 * ease_p))
            self.screen.blit(res_lbl, (35, 22))

                                                   
            if song_title:
                title_s  = font_title.render(song_title, True, self.TEXT_COLOR)
                title_s.set_alpha(int(255 * ease_p))
                self.screen.blit(title_s, title_s.get_rect(midright=(W - 25, 20)))
            if song_artist:
                artist_s = font_artist.render(song_artist, True, self.MUTED_COLOR)
                artist_s.set_alpha(int(200 * ease_p))
                self.screen.blit(artist_s, artist_s.get_rect(midright=(W - 25, 42)))

                                                                                
                                                                                
                                                                                
            slide_l = int((1.0 - ease_p) * -50)
            slide_r = int((1.0 - ease_p) * 50)

            card_l = pygame.Rect(35 + slide_l, 76, 490, 544)
            card_r = pygame.Rect(545 + slide_r, 76, 700, 544)

                              
            draw_rounded_rect_alpha(self.screen, card_l, (14, 14, 22, int(200 * ease_p)), radius=14)
            draw_rounded_border(self.screen, card_l, (45, 48, 65, int(150 * ease_p)), width=1, radius=14)

            draw_rounded_rect_alpha(self.screen, card_r, (14, 14, 22, int(200 * ease_p)), radius=14)
            draw_rounded_border(self.screen, card_r, (45, 48, 65, int(150 * ease_p)), width=1, radius=14)

                                                                                 
                                         
            grade_cx = card_l.x + 85
            grade_cy = 152 + int(grade_bounce_pos)
            glow_pulse = (math.sin(pulse_t * 2.0) + 1.0) * 0.5
            glow_alpha = int((80 + 50 * glow_pulse) * ease_p)
            for r in (38, 24, 12):
                g_s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(g_s, (*glow_color, glow_alpha // (38 // r + 1)), (r + 2, r + 2), r)
                self.screen.blit(g_s, (grade_cx - r - 2, grade_cy - r - 2))

            grade_s = font_grade.render(grade, True, grade_color)
            grade_s.set_alpha(int(255 * ease_p))
            self.screen.blit(grade_s, grade_s.get_rect(center=(grade_cx, grade_cy)))

                                             
            div_s = pygame.Surface((1, 90), pygame.SRCALPHA)
            div_s.fill((60, 60, 80, int(100 * ease_p)))
            self.screen.blit(div_s, (card_l.x + 165, 108))

                               
            score_x = card_l.x + 185
            sc_lbl = font_label.render("TOTAL SCORE", True, self.MUTED_COLOR)
            sc_lbl.set_alpha(int(220 * ease_p))
            self.screen.blit(sc_lbl, (score_x, 114))

            sc_val = font_score.render(f"{int(display_score):,}", True, self.TEXT_COLOR)
            sc_val.set_alpha(int(255 * ease_p))
            self.screen.blit(sc_val, (score_x, 136))

                                                  
            if is_new_pb:
                pb_box = pygame.Rect(score_x, 178, 150, 24)
                draw_rounded_rect_alpha(self.screen, pb_box, (55, 42, 10, int(220 * ease_p)), radius=6)
                draw_rounded_border(self.screen, pb_box, (255, 215, 50, int(220 * ease_p)), width=1, radius=6)
                pb_text = font_hint.render("NEW PERSONAL BEST", True, (255, 215, 50))
                pb_text.set_alpha(int(255 * ease_p))
                self.screen.blit(pb_text, pb_text.get_rect(center=pb_box.center))
            elif diff_name:
                diff_box = pygame.Rect(score_x, 178, 120, 24)
                draw_rounded_rect_alpha(self.screen, diff_box, (*self.ACCENT_COLOR, int(35 * ease_p)), radius=6)
                draw_rounded_border(self.screen, diff_box, (*self.ACCENT_COLOR, int(90 * ease_p)), width=1, radius=6)
                d_text = font_hint.render(diff_name, True, self.ACCENT_COLOR)
                d_text.set_alpha(int(220 * ease_p))
                self.screen.blit(d_text, d_text.get_rect(center=diff_box.center))

                               
            line1_s = pygame.Surface((card_l.width - 40, 1), pygame.SRCALPHA)
            line1_s.fill((45, 48, 65, int(120 * ease_p)))
            self.screen.blit(line1_s, (card_l.x + 20, 222))

                                                              
            sub_acc_rect = pygame.Rect(card_l.x + 20, 238, 215, 148)
            draw_rounded_rect_alpha(self.screen, sub_acc_rect, (18, 18, 28, int(190 * ease_p)), radius=10)
            draw_rounded_border(self.screen, sub_acc_rect, (40, 42, 58, int(120 * ease_p)), width=1, radius=10)

            arc_cx = sub_acc_rect.centerx
            arc_cy = sub_acc_rect.y + 70
            arc_r  = 44
            draw_accuracy_arc(self.screen, arc_cx, arc_cy, arc_r, 1.0, (35, 35, 50), width=6)
            animated_pct = min(accuracy, ease_p * accuracy)
            draw_accuracy_arc(self.screen, arc_cx, arc_cy, arc_r, animated_pct, grade_color, width=6)

            acc_lbl = font_hint.render("ACCURACY", True, self.MUTED_COLOR)
            acc_lbl.set_alpha(int(200 * ease_p))
            self.screen.blit(acc_lbl, acc_lbl.get_rect(center=(arc_cx, arc_cy - 10)))

            acc_val = font_stat.render(f"{accuracy * 100:.2f}%", True, grade_color)
            acc_val.set_alpha(int(255 * ease_p))
            self.screen.blit(acc_val, acc_val.get_rect(center=(arc_cx, arc_cy + 10)))

            sub_combo_rect = pygame.Rect(card_l.x + 255, 238, 215, 148)
            draw_rounded_rect_alpha(self.screen, sub_combo_rect, (18, 18, 28, int(190 * ease_p)), radius=10)
            draw_rounded_border(self.screen, sub_combo_rect, (40, 42, 58, int(120 * ease_p)), width=1, radius=10)

            cmb_lbl = font_hint.render("MAX COMBO", True, self.MUTED_COLOR)
            cmb_lbl.set_alpha(int(200 * ease_p))
            self.screen.blit(cmb_lbl, cmb_lbl.get_rect(center=(sub_combo_rect.centerx, sub_combo_rect.y + 36)))

            cmb_val = font_score.render(f"{max_combo}x", True, self.ACCENT_COLOR)
            cmb_val.set_alpha(int(255 * ease_p))
            self.screen.blit(cmb_val, cmb_val.get_rect(center=(sub_combo_rect.centerx, sub_combo_rect.y + 74)))

            fc_text = "PERFECT COMBO" if cmiss == 0 else f"{cmiss} MISS{'ES' if cmiss > 1 else ''}"
            fc_col = (255, 215, 50) if cmiss == 0 else (255, 80, 80)
            fc_s = font_hint.render(fc_text, True, fc_col)
            fc_s.set_alpha(int(220 * ease_p))
            self.screen.blit(fc_s, fc_s.get_rect(center=(sub_combo_rect.centerx, sub_combo_rect.y + 116)))

                               
            line2_s = pygame.Surface((card_l.width - 40, 1), pygame.SRCALPHA)
            line2_s.fill((45, 48, 65, int(120 * ease_p)))
            self.screen.blit(line2_s, (card_l.x + 20, 404))

                                                         
            sub_ur_rect = pygame.Rect(card_l.x + 20, 420, 215, 58)
            draw_rounded_rect_alpha(self.screen, sub_ur_rect, (18, 18, 28, int(190 * ease_p)), radius=8)
            draw_rounded_border(self.screen, sub_ur_rect, (40, 42, 58, int(120 * ease_p)), width=1, radius=8)

            ur_t = font_hint.render("UNSTABLE RATE", True, self.MUTED_COLOR)
            ur_t.set_alpha(int(200 * ease_p))
            self.screen.blit(ur_t, (sub_ur_rect.x + 14, sub_ur_rect.y + 10))

            ur_col = (0, 229, 255) if ur_value < 100 else (255, 255, 255)
            ur_v = font_stat.render(f"{ur_value:.1f} UR", True, ur_col)
            ur_v.set_alpha(int(255 * ease_p))
            self.screen.blit(ur_v, (sub_ur_rect.x + 14, sub_ur_rect.y + 28))

            sub_mod_rect = pygame.Rect(card_l.x + 255, 420, 215, 58)
            draw_rounded_rect_alpha(self.screen, sub_mod_rect, (18, 18, 28, int(190 * ease_p)), radius=8)
            draw_rounded_border(self.screen, sub_mod_rect, (40, 42, 58, int(120 * ease_p)), width=1, radius=8)

            mod_t = font_hint.render("ACTIVE MODS", True, self.MUTED_COLOR)
            mod_t.set_alpha(int(200 * ease_p))
            self.screen.blit(mod_t, (sub_mod_rect.x + 14, sub_mod_rect.y + 10))

            mod_v = font_stat.render(f"{mod_str} ({mult:.2f}x)", True, self.ACCENT_COLOR)
            mod_v.set_alpha(int(255 * ease_p))
            self.screen.blit(mod_v, (sub_mod_rect.x + 14, sub_mod_rect.y + 28))

                                    
            track_pill = pygame.Rect(card_l.x + 20, 494, card_l.width - 40, 36)
            draw_rounded_rect_alpha(self.screen, track_pill, (20, 20, 30, int(150 * ease_p)), radius=6)
            tr_text = f"{song_title}  •  {diff_name}" if diff_name else song_title
            tr_s = font_hint.render(tr_text, True, self.MUTED_COLOR)
            tr_s.set_alpha(int(200 * ease_p))
            self.screen.blit(tr_s, tr_s.get_rect(center=track_pill.center))

                                                                                
                   
            hr_lbl = font_header.render("HIT ACCURACY BREAKDOWN", True, self.ACCENT_COLOR)
            hr_lbl.set_alpha(int(230 * ease_p))
            self.screen.blit(hr_lbl, (card_r.x + 25, 96))

                                                             
            grid_w = 315
            grid_h = 56
            col1_x = card_r.x + 25
            col2_x = card_r.x + 360

            row1_y = 126
            row2_y = 194

                     
            draw_judgment_card(self.screen, pygame.Rect(col1_x, row1_y, grid_w, grid_h),
                               "PERFECT", c300, (0, 229, 255), ease_p)
                   
            draw_judgment_card(self.screen, pygame.Rect(col2_x, row1_y, grid_w, grid_h),
                               "GREAT", c100, (100, 220, 255), ease_p)
                  
            draw_judgment_card(self.screen, pygame.Rect(col1_x, row2_y, grid_w, grid_h),
                               "GOOD", c50, (255, 190, 50), ease_p)
                  
            draw_judgment_card(self.screen, pygame.Rect(col2_x, row2_y, grid_w, grid_h),
                               "MISS", cmiss, (255, 70, 80), ease_p)

                            
            line3_s = pygame.Surface((card_r.width - 50, 1), pygame.SRCALPHA)
            line3_s.fill((45, 48, 65, int(120 * ease_p)))
            self.screen.blit(line3_s, (card_r.x + 25, 270))

                                                                                
            tb_title = font_header.render("HIT TIMING DISTRIBUTION", True, self.ACCENT_COLOR)
            tb_title.set_alpha(int(220 * ease_p))
            self.screen.blit(tb_title, (card_r.x + 25, 288))

            tb_sub = font_hint.render(f"Mean Deviation: {mean_err:+.1f}ms   |   Total Hits: {total}", True, self.MUTED_COLOR)
            tb_sub.set_alpha(int(190 * ease_p))
            self.screen.blit(tb_sub, tb_sub.get_rect(midright=(card_r.right - 25, 298)))

                                   
            BAR_W = 650
            BAR_H = 18
            BAR_X = card_r.x + 25
            BAR_Y = 328
            bar_rect = pygame.Rect(BAR_X, BAR_Y, BAR_W, BAR_H)

                       
            draw_rounded_rect_alpha(self.screen, bar_rect, (22, 22, 34, int(220 * ease_p)), radius=6)
                          
            cx_bar = BAR_X + BAR_W // 2
                       
            gw_bar = int((BAR_W // 2) * (self.GOOD_WINDOW / self.MISS_WINDOW))
            pygame.draw.rect(self.screen, (100, 80, 20), (cx_bar - gw_bar, BAR_Y + 1, gw_bar * 2, BAR_H - 2), border_radius=4)
                        
            rw_bar = int((BAR_W // 2) * (self.GREAT_WINDOW / self.MISS_WINDOW))
            pygame.draw.rect(self.screen, (20, 70, 110), (cx_bar - rw_bar, BAR_Y + 1, rw_bar * 2, BAR_H - 2), border_radius=4)
                          
            pw_bar = int((BAR_W // 2) * (self.PERFECT_WINDOW / self.MISS_WINDOW))
            pygame.draw.rect(self.screen, (0, 140, 120), (cx_bar - pw_bar, BAR_Y + 1, pw_bar * 2, BAR_H - 2), border_radius=4)

            draw_rounded_border(self.screen, bar_rect, (50, 52, 72, int(180 * ease_p)), width=1, radius=6)
                          
            pygame.draw.line(self.screen, (255, 255, 255, int(200 * ease_p)), (cx_bar, BAR_Y - 3), (cx_bar, BAR_Y + BAR_H + 3), 2)

                                         
            if timing_errors:
                for err_ms in timing_errors:
                    norm = max(-1.0, min(1.0, err_ms / 150.0))
                    dot_x = int(cx_bar + norm * (BAR_W // 2))
                    dot_col = (100, 200, 255) if err_ms < 0 else (255, 140, 60)
                    dot_s = pygame.Surface((3, BAR_H - 4), pygame.SRCALPHA)
                    dot_s.fill((*dot_col, int(150 * ease_p)))
                    self.screen.blit(dot_s, (dot_x - 1, BAR_Y + 2))

                                       
            if len(timing_errors) > 0:
                mean_norm = max(-1.0, min(1.0, mean_err / 150.0))
                marker_x = int(cx_bar + mean_norm * (BAR_W // 2))
                tri_pts = [(marker_x, BAR_Y - 2), (marker_x - 4, BAR_Y - 7), (marker_x + 4, BAR_Y - 7)]
                pygame.draw.polygon(self.screen, (255, 255, 255), tri_pts)

                                     
            early_s = font_hint.render("-150ms  EARLY", True, (100, 200, 255))
            early_s.set_alpha(int(200 * ease_p))
            self.screen.blit(early_s, (BAR_X, BAR_Y + 24))

            center_s = font_hint.render("0ms", True, (180, 180, 200))
            center_s.set_alpha(int(180 * ease_p))
            self.screen.blit(center_s, center_s.get_rect(center=(cx_bar, BAR_Y + 30)))

            late_s = font_hint.render("LATE  +150ms", True, (255, 140, 60))
            late_s.set_alpha(int(200 * ease_p))
            self.screen.blit(late_s, late_s.get_rect(topright=(BAR_X + BAR_W, BAR_Y + 24)))

                            
            line4_s = pygame.Surface((card_r.width - 50, 1), pygame.SRCALPHA)
            line4_s.fill((45, 48, 65, int(120 * ease_p)))
            self.screen.blit(line4_s, (card_r.x + 25, 420))

                                                                                
            sum_rect = pygame.Rect(card_r.x + 25, 436, card_r.width - 50, 84)
            draw_rounded_rect_alpha(self.screen, sum_rect, (18, 18, 28, int(190 * ease_p)), radius=10)
            draw_rounded_border(self.screen, sum_rect, (40, 42, 58, int(120 * ease_p)), width=1, radius=10)

                                  
            sec_w = sum_rect.width // 3
                                
            c1_x = sum_rect.x + sec_w // 2
            t1 = font_hint.render("TOTAL NOTES", True, self.MUTED_COLOR)
            v1 = font_stat.render(f"{total:,}", True, self.TEXT_COLOR)
            self.screen.blit(t1, t1.get_rect(center=(c1_x, sum_rect.y + 24)))
            self.screen.blit(v1, v1.get_rect(center=(c1_x, sum_rect.y + 54)))

                       
            pygame.draw.line(self.screen, (40, 42, 58), (sum_rect.x + sec_w, sum_rect.y + 12),
                             (sum_rect.x + sec_w, sum_rect.bottom - 12), 1)

                               
            c2_x = sum_rect.x + sec_w + sec_w // 2
            t2 = font_hint.render("FINAL RANK", True, self.MUTED_COLOR)
            v2 = font_stat.render(f"GRADE {grade} ({accuracy*100:.1f}%)", True, grade_color)
            self.screen.blit(t2, t2.get_rect(center=(c2_x, sum_rect.y + 24)))
            self.screen.blit(v2, v2.get_rect(center=(c2_x, sum_rect.y + 54)))

                       
            pygame.draw.line(self.screen, (40, 42, 58), (sum_rect.x + sec_w * 2, sum_rect.y + 12),
                             (sum_rect.x + sec_w * 2, sum_rect.bottom - 12), 1)

                                
            c3_x = sum_rect.x + sec_w * 2 + sec_w // 2
            t3 = font_hint.render("CONSISTENCY", True, self.MUTED_COLOR)
            v3 = font_stat.render(f"{ur_value:.1f} UR", True, self.ACCENT_COLOR)
            self.screen.blit(t3, t3.get_rect(center=(c3_x, sum_rect.y + 24)))
            self.screen.blit(v3, v3.get_rect(center=(c3_x, sum_rect.y + 54)))

                                                                               
            strip_surf = pygame.Surface((W, 80), pygame.SRCALPHA)
            strip_surf.fill((10, 10, 18, 220))
            pygame.draw.line(strip_surf, (*self.ACCENT_COLOR, 60), (0, 0), (W, 0), 1)
            self.screen.blit(strip_surf, (0, H - 80))

                       
            hint_s = font_hint.render("CTRL+R  Retry   |   ENTER / ESC  Menu", True, (70, 70, 95))
            hint_s.set_alpha(int(160 * ease_p))
            self.screen.blit(hint_s, hint_s.get_rect(center=(W // 2, H - 16)))

                     
            if ease_p > 0.6:
                btn_alpha = min(1.0, (ease_p - 0.6) / 0.4)

                              
                r_hov = retry_rect.collidepoint(mouse_pos)
                r_bg  = (50, 30, 80, int(220 * btn_alpha)) if r_hov else (26, 26, 38, int(200 * btn_alpha))
                r_bdr = (*self.ACCENT_COLOR, int(200 * btn_alpha)) if r_hov else (70, 70, 100, int(150 * btn_alpha))
                draw_rounded_rect_alpha(self.screen, retry_rect, r_bg, radius=10)
                draw_rounded_border(self.screen, retry_rect, r_bdr[:3], width=2, radius=10)
                r_txt = font_header.render("RETRY", True,
                                           self.ACCENT_COLOR if r_hov else self.TEXT_COLOR)
                r_txt.set_alpha(int(255 * btn_alpha))
                self.screen.blit(r_txt, r_txt.get_rect(center=retry_rect.center))

                             
                m_hov = menu_rect.collidepoint(mouse_pos)
                m_bg  = (30, 50, 80, int(220 * btn_alpha)) if m_hov else (26, 26, 38, int(200 * btn_alpha))
                m_bdr = (*self.ACCENT_COLOR, int(200 * btn_alpha)) if m_hov else (70, 70, 100, int(150 * btn_alpha))
                draw_rounded_rect_alpha(self.screen, menu_rect, m_bg, radius=10)
                draw_rounded_border(self.screen, menu_rect, m_bdr[:3], width=2, radius=10)
                m_txt = font_header.render("MENU", True,
                                           self.ACCENT_COLOR if m_hov else self.TEXT_COLOR)
                m_txt.set_alpha(int(255 * btn_alpha))
                self.screen.blit(m_txt, m_txt.get_rect(center=menu_rect.center))

            pygame.display.flip()
            clock.tick(60)

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
        
                                                
        countdown_timer = 3.0
        countdown_active = True
        intro_skipped = False
        first_note_time = hit_times[0] if hit_times else 999.0

        score = 0
        combo = 0
        max_combo = 0
        hp = GlobalState.hp
        counts = {"perfect": 0, "great": 0, "good": 0, "miss": 0}

        current_note_idx = 0

                                 
        mod_score_mult = GlobalState.get_score_multiplier()
        is_hr = "HR" in GlobalState.active_mods
        is_sd = "SD" in GlobalState.active_mods
        is_pf = "PF" in GlobalState.active_mods
        is_nf = "NF" in GlobalState.active_mods
        hp_miss_drain = 12.0 if is_hr else 8.0
        hp_wrong_drain = 8.0 if is_hr else 5.0

                                              
        feedback_text = ""
        feedback_sub_text = ""                                 
        feedback_timer = 0.0
        feedback_max_time = 0.35
        feedback_y_offset = 0.0
        hit_ripples = []
        particles = []
        display_hp = float(hp)
        combo_pop_timer = 0.0
                                                                       
        wrong_flash_timer = 0.0
        wrong_flash_char = ""
                                  
        COMBO_MILESTONES = {50, 100, 200, 500, 1000}
        milestone_flash_timer = 0.0
        milestone_flash_combo = 0
                          
        HP_DRAIN_RATE = 1.5                               

                                                  
        timing_errors = []
        err_count = 0
        err_sum = 0.0
        err_sum_sq = 0.0
        ur_value = 0.0
        live_error_ticks = []                                                            

                                               
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
                    conductor.start_song(0.0)
            else:
                conductor.update()
                current_time = conductor.song_position

            can_skip_intro = (not countdown_active and not intro_skipped and current_time < intro_end_time and intro_end_time > 2.0)

                                                 
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

                            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    conductor.stop()
                    return "quit"
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    skip_rect = pygame.Rect(self.width // 2 - 130, self.height - 110, 260, 44)
                    if (countdown_active or can_skip_intro) and skip_rect.collidepoint(event.pos):
                        if countdown_active:
                            countdown_active = False
                            countdown_timer = 0.0
                            if intro_end_time > 2.0:
                                intro_skipped = True
                                conductor.start_song(intro_end_time)
                            else:
                                conductor.start_song(0.0)
                        elif can_skip_intro:
                            intro_skipped = True
                            can_skip_intro = False
                            conductor.seek(intro_end_time)
                elif event.type == pygame.KEYDOWN:
                                                      
                    if event.key == pygame.K_r and (event.mod & pygame.KMOD_CTRL):
                        conductor.stop()
                        return "play"

                                            
                    if event.key == pygame.K_F11:
                        flags = self.screen.get_flags()
                        if flags & pygame.FULLSCREEN:
                            self.screen = pygame.display.set_mode(
                                (self.width, self.height), pygame.RESIZABLE)
                        else:
                            self.screen = pygame.display.set_mode(
                                (0, 0), pygame.FULLSCREEN)
                            self.width, self.height = self.screen.get_size()

                    if event.key == pygame.K_ESCAPE:
                        pause_result = self._pause_screen(conductor, clock)
                        if pause_result != "resume":
                            conductor.stop()
                            return "quit" if pause_result == "quit" else "play" if pause_result == "retry" else "menu"
                        continue

                                                        
                    if event.key == pygame.K_SPACE:
                        if countdown_active:
                            countdown_active = False
                            countdown_timer = 0.0
                            if intro_end_time > 2.0:
                                intro_skipped = True
                                conductor.start_song(intro_end_time)
                            else:
                                conductor.start_song(0.0)
                        elif can_skip_intro:
                            intro_skipped = True
                            can_skip_intro = False
                            conductor.seek(intro_end_time)
                        continue

                                                         
                    if event.key in IGNORED_KEYS:
                        continue

                                                    
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

                                                                   
                                err_count += 1
                                err_sum += error_ms
                                err_sum_sq += error_ms * error_ms
                                if err_count > 1:
                                    mean_err = err_sum / err_count
                                    variance = max(0.0, (err_sum_sq / err_count) - (mean_err * mean_err))
                                    ur_value = math.sqrt(variance) * 10.0

                                                       
                                if time_error < -0.005:
                                    feedback_sub_text = "EARLY"
                                elif time_error > 0.005:
                                    feedback_sub_text = "LATE"
                                else:
                                    feedback_sub_text = ""

                                                                
                                norm_err = max(-1.0, min(1.0, time_error / self.MISS_WINDOW))
                                if abs_err <= self.PERFECT_WINDOW:
                                    tick_col = (0, 255, 180)
                                elif abs_err <= self.GREAT_WINDOW:
                                    tick_col = (100, 220, 255)
                                elif abs_err <= self.GOOD_WINDOW:
                                    tick_col = (255, 200, 0)
                                else:
                                    tick_col = (255, 70, 70)
                                live_error_ticks.append({"norm": norm_err, "life": 1.2, "col": tick_col})

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

                                                  
                                if combo in COMBO_MILESTONES:
                                    milestone_flash_timer = 1.2
                                    milestone_flash_combo = combo
                                    for _ in range(28):
                                        angle = random.uniform(0, math.pi * 2)
                                        spd = random.uniform(250, 600)
                                        particles.append({
                                            "x": self.width // 2,
                                            "y": self.lane_y - 80,
                                            "vx": math.cos(angle) * spd,
                                            "vy": math.sin(angle) * spd,
                                            "life": random.uniform(0.6, 1.1),
                                            "max_life": 1.1,
                                            "color": (255, 215, 0),
                                            "type": "glitter",
                                            "size": random.uniform(3, 7)
                                        })

                                self._play_hitsound()
                                active_note["hit"] = True
                                feedback_timer = feedback_max_time
                                feedback_y_offset = 0.0
                                combo_pop_timer = 0.15

                                if combo > max_combo:
                                    max_combo = combo

                                                            
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
                                feedback_sub_text = ""
                                self._play_miss_sound()
                                combo = 0
                                hp = max(0.0, hp - hp_wrong_drain)
                                if is_sd or is_pf:
                                    hp = 0.0
                                feedback_timer = feedback_max_time
                                feedback_y_offset = 0.0
                                                                       
                                wrong_flash_timer = 0.55
                                wrong_flash_char = active_note["char"]
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

                                                               
            if hp <= 0 and not is_nf:
                conductor.stop()
                last_frame = self.screen.copy()
                return self._show_fail_screen(score, max_combo, clock, last_frame)

                                  
            if current_note_idx >= len(notes):
                song_ended = True

            if song_ended:
                end_cooldown -= dt
                if end_cooldown <= 0.0:
                    conductor.stop()
                    last_frame = self.screen.copy()
                    return self._show_results(score, max_combo, timing_errors, counts, ur_value, clock, last_frame)

                                                                        
            if not countdown_active and not song_ended:
                hp = max(0.0, hp - HP_DRAIN_RATE * dt)

                         
            if wrong_flash_timer > 0:
                wrong_flash_timer -= dt
            if milestone_flash_timer > 0:
                milestone_flash_timer -= dt

                                            
            live_error_ticks = [t for t in live_error_ticks if t["life"] > 0]
            for t in live_error_ticks:
                t["life"] -= dt

                               
            if bg_surface:
                self.screen.blit(bg_surface, (0, 0))
            else:
                self.screen.fill(self.BG_COLOR)

                                              
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

                                             
            if GlobalState.active_mods:
                badge_x = self.width - 50
                for mod_name in sorted(GlobalState.active_mods):
                    badge_rect = pygame.Rect(badge_x - 38, 65, 38, 22)
                    pygame.draw.rect(self.screen, (40, 40, 60), badge_rect, border_radius=4)
                    pygame.draw.rect(self.screen, self.ACCENT_COLOR, badge_rect, 1, border_radius=4)
                    b_txt = self.font_small.render(mod_name, True, self.ACCENT_COLOR)
                    self.screen.blit(b_txt, b_txt.get_rect(center=badge_rect.center))
                    badge_x -= 44

                                                    
            pygame.draw.line(self.screen, (0, 100, 120), (0, self.lane_y), (self.width, self.lane_y), 8)
            pygame.draw.line(self.screen, self.ACCENT_COLOR, (0, self.lane_y), (self.width, self.lane_y), 2)
            
            beat_progress = (conductor.song_position / (60.0 / conductor.bpm)) % 1.0 if conductor.bpm > 0 else 0
            pulse_radius = 45 + 5 * (1.0 - beat_progress)
            
            pygame.draw.circle(self.screen, (25, 25, 38), (self.target_x, self.lane_y), int(pulse_radius))
            pygame.draw.circle(self.screen, self.ACCENT_COLOR, (self.target_x, self.lane_y), int(pulse_radius), 3)
            pygame.draw.circle(self.screen, (0, 100, 120), (self.target_x, self.lane_y), int(pulse_radius) + 3, 2)

                                                   
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

                                                                    
            hud_y = self.lane_y + 200
            
            panel_w = 700
            panel_rect = pygame.Rect(self.width // 2 - panel_w // 2, hud_y - 25, panel_w, 95)
            panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (15, 15, 22, 190), panel_surf.get_rect(), border_radius=12)
            pygame.draw.rect(panel_surf, (45, 48, 65, 220), panel_surf.get_rect(), 2, border_radius=12)
            self.screen.blit(panel_surf, panel_rect)

            guide_label = self.font_small.render("UPCOMING WORDS", True, self.MUTED_COLOR)
            self.screen.blit(guide_label, (self.width // 2 - guide_label.get_width() // 2, hud_y - 15))
            
                                           
            mc_lbl = self.font_small.render("MAX COMBO: ", True, self.MUTED_COLOR)
            mc_val = self.font_small.render(f"{max_combo}x", True, self.TEXT_COLOR)
            self.screen.blit(mc_lbl, (panel_rect.left + 25, hud_y - 15))
            self.screen.blit(mc_val, (panel_rect.left + 25 + mc_lbl.get_width(), hud_y - 15))
            
                                                     
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
                                                                   
                if current_note_idx != cached_hud_idx:
                    cached_hud_idx = current_note_idx
                    cached_hud_surfs = []
                    cached_hud_total_w = 0

                    active_note = notes[current_note_idx]
                    cur_w_idx = active_note["word_index"]
                    cur_c_idx = active_note["char_index"]
                    cur_word = words_list[cur_w_idx] if cur_w_idx < len(words_list) else ""

                                                  
                    if cur_c_idx > 0:
                        s = self.font_guide.render(cur_word[:cur_c_idx], True, self.GREEN_COLOR)
                        cached_hud_surfs.append(s)
                        cached_hud_total_w += s.get_width()

                                                    
                    s = self.font_guide.render(cur_word[cur_c_idx], True, self.ACCENT_COLOR)
                    cached_hud_surfs.append(s)
                    cached_hud_total_w += s.get_width()

                                                                  
                    if cur_c_idx + 1 < len(cur_word):
                        s = self.font_guide.render(cur_word[cur_c_idx + 1:], True, self.TEXT_COLOR)
                        cached_hud_surfs.append(s)
                        cached_hud_total_w += s.get_width()

                                                            
                    subsequent_words = words_list[cur_w_idx + 1: cur_w_idx + 5]
                    for sub_w in subsequent_words:
                        s = self.font_guide.render("  " + sub_w, True, self.MUTED_COLOR)
                        cached_hud_surfs.append(s)
                        cached_hud_total_w += s.get_width()

                cur_x = self.width // 2 - cached_hud_total_w // 2
                for surf in cached_hud_surfs:
                    self.screen.blit(surf, (cur_x, hud_y + 30))
                    cur_x += surf.get_width()

                                                              
            score_surf = self.font_score.render(f"{int(score):06d}", True, self.TEXT_COLOR)
            self.screen.blit(score_surf, (50, 24))

            total_hits = counts["perfect"] + counts["great"] + counts["good"] + counts["miss"]
            current_acc = (300 * counts["perfect"] + 100 * counts["great"] + 50 * counts["good"]) / (300 * total_hits) if total_hits > 0 else 1.0
            acc_surf = self.font_small.render(f"ACC  {current_acc * 100:.2f}%", True, self.ACCENT_COLOR)
            self.screen.blit(acc_surf, (52, 68))
            if mod_score_mult != 1.0:
                mult_surf = self.font_small.render(f"MULT  {mod_score_mult:.2f}x", True, (255, 215, 60))
                self.screen.blit(mult_surf, (52, 88))

            if combo > 1:
                combo_surf = self.font_combo.render(f"{combo}x", True, self.ACCENT_COLOR)
                combo_rect = combo_surf.get_rect(center=(self.width // 2, self.lane_y - 75))
                self.screen.blit(combo_surf, combo_rect)

                                                                    
            if wrong_flash_timer > 0 and wrong_flash_char:
                flash_alpha = int(255 * (wrong_flash_timer / 0.55))
                flash_surf = pygame.Surface((70, 70), pygame.SRCALPHA)
                pygame.draw.rect(flash_surf, (255, 60, 60, min(180, flash_alpha)), (0, 0, 70, 70), border_radius=15)
                pygame.draw.rect(flash_surf, (255, 100, 100, flash_alpha), (0, 0, 70, 70), 3, border_radius=15)
                char_surf = self.font_med.render(wrong_flash_char, True, (255, 230, 230))
                char_surf.set_alpha(flash_alpha)
                flash_surf.blit(char_surf, char_surf.get_rect(center=(35, 35)))
                self.screen.blit(flash_surf, (notes[current_note_idx]["x"] - 35 if current_note_idx < len(notes) else self.target_x - 35, self.lane_y - 35))

                                           
            if milestone_flash_timer > 0:
                mf_alpha = int(min(255, milestone_flash_timer * 180))
                mf_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                mf_surf.fill((255, 215, 0, min(30, mf_alpha // 4)))
                self.screen.blit(mf_surf, (0, 0))
                pulse = abs(math.sin(milestone_flash_timer * 8))
                mc_font = self.font_large
                mc_text = f"{milestone_flash_combo}x COMBO!"
                mc_surf = mc_font.render(mc_text, True, (255, 215, 0))
                mc_surf.set_alpha(min(255, int(mf_alpha * 1.5)))
                self.screen.blit(mc_surf, mc_surf.get_rect(center=(self.width // 2, self.lane_y - 150 - int(pulse * 12))))

                                                              
            if feedback_timer > 0:
                feedback_timer -= dt
                feedback_y_offset -= 30.0 * dt

                progress_ratio = feedback_timer / feedback_max_time
                current_alpha = max(0, min(255, int(255 * progress_ratio)))

                base_judgement = self.judgement_surfaces.get(feedback_text)
                if base_judgement:
                    base_judgement.set_alpha(current_alpha)
                    self.screen.blit(base_judgement, base_judgement.get_rect(center=(self.target_x, self.lane_y - 90 + feedback_y_offset)))

                                        
                if feedback_sub_text:
                    sub_col = (100, 180, 255) if feedback_sub_text == "EARLY" else (255, 150, 80)
                    sub_surf = self.font_small.render(feedback_sub_text, True, sub_col)
                    sub_surf.set_alpha(current_alpha)
                    self.screen.blit(sub_surf, sub_surf.get_rect(center=(self.target_x, self.lane_y - 60 + feedback_y_offset)))

                                       
            if countdown_active and countdown_timer > 0:
                count_num = math.ceil(countdown_timer)
                count_str = str(count_num) if count_num > 0 else "GO!"

                cnt_font = pygame.font.SysFont("Arial", 110, bold=True)
                cnt_surf = cnt_font.render(count_str, True, self.ACCENT_COLOR)
                cnt_rect = cnt_surf.get_rect(center=(self.width // 2, self.height // 2 - 20))
                self.screen.blit(cnt_surf, cnt_rect)

                cnt_sub = self.font_small.render("GET READY!   |   Press SPACE or Click to Skip", True, self.TEXT_COLOR)
                self.screen.blit(cnt_sub, cnt_sub.get_rect(center=(self.width // 2, self.height // 2 + 50)))

                                       
            elif can_skip_intro:
                skip_rect = pygame.Rect(self.width // 2 - 130, self.height - 110, 260, 44)
                is_skip_hovered = skip_rect.collidepoint(mouse_pos)

                skip_pulse = (math.sin(pygame.time.get_ticks() * 0.006) + 1.0) * 0.5
                s_bg = self.ACCENT_COLOR if is_skip_hovered else (24, 24, 34)
                s_border = (120, 240, 255) if is_skip_hovered else (0, int(150 + 79 * skip_pulse), int(180 + 75 * skip_pulse))
                s_fg = (10, 10, 15) if is_skip_hovered else self.ACCENT_COLOR

                s_surf = pygame.Surface((260, 44), pygame.SRCALPHA)
                pygame.draw.rect(s_surf, (*s_bg, 230), (0, 0, 260, 44), border_radius=10)
                self.screen.blit(s_surf, skip_rect)
                pygame.draw.rect(self.screen, s_border, skip_rect, 2, border_radius=10)

                txt = self.font_guide.render("SKIP INTRO  [SPACE]", True, s_fg)
                self.screen.blit(txt, txt.get_rect(center=skip_rect.center))

                                                          
            heb_w = 260
            heb_h = 6
            heb_x = self.width // 2 - heb_w // 2
            heb_y = self.height - 24

                            
            pygame.draw.rect(self.screen, (20, 20, 30), (heb_x, heb_y, heb_w, heb_h), border_radius=3)
                                  
            good_pct = min(1.0, self.GOOD_WINDOW / self.MISS_WINDOW)
            great_pct = min(1.0, self.GREAT_WINDOW / self.MISS_WINDOW)
            perf_pct = min(1.0, self.PERFECT_WINDOW / self.MISS_WINDOW)

            cx = heb_x + heb_w // 2
            gw = int((heb_w // 2) * good_pct)
            pygame.draw.rect(self.screen, (100, 80, 20), (cx - gw, heb_y, gw * 2, heb_h), border_radius=2)
            rw = int((heb_w // 2) * great_pct)
            pygame.draw.rect(self.screen, (20, 70, 100), (cx - rw, heb_y, rw * 2, heb_h), border_radius=2)
            pw = int((heb_w // 2) * perf_pct)
            pygame.draw.rect(self.screen, (0, 120, 100), (cx - pw, heb_y, pw * 2, heb_h), border_radius=2)
            pygame.draw.rect(self.screen, (50, 50, 70), (heb_x, heb_y, heb_w, heb_h), 1, border_radius=3)
            pygame.draw.line(self.screen, (255, 255, 255), (cx, heb_y - 2), (cx, heb_y + heb_h + 2), 2)

            for t in live_error_ticks:
                tx = int(cx + t["norm"] * (heb_w // 2))
                alpha = int(255 * (t["life"] / 1.2))
                ts = pygame.Surface((3, heb_h + 4), pygame.SRCALPHA)
                ts.fill((*t["col"], alpha))
                self.screen.blit(ts, (tx - 1, heb_y - 2))

            if err_count > 0:
                mean_norm = max(-1.0, min(1.0, (err_sum / err_count) / (self.MISS_WINDOW * 1000.0)))
                avg_x = int(cx + mean_norm * (heb_w // 2))
                tri_pts = [(avg_x, heb_y - 3), (avg_x - 3, heb_y - 7), (avg_x + 3, heb_y - 7)]
                pygame.draw.polygon(self.screen, (255, 255, 255), tri_pts)

            lbl_early = self.font_mono.render("EARLY", True, (100, 180, 255))
            lbl_late = self.font_mono.render("LATE", True, (255, 150, 80))
            self.screen.blit(lbl_early, (heb_x - lbl_early.get_width() - 8, heb_y - 4))
            self.screen.blit(lbl_late, (heb_x + heb_w + 8, heb_y - 4))


            if last_frame:
                fade_progress = min(1.0, (pygame.time.get_ticks() - time_start) / 600.0)
                if fade_progress < 1.0:
                    if not hasattr(self, 'run_trans') or self.run_trans['time_start'] != time_start:
                        mx, my = pygame.mouse.get_pos()
                        trans_tiles = []
                        for y in range(0, self.height, 40):
                            for x in range(0, self.width, 40):
                                tile_cx = x + 20
                                tile_cy = y + 20
                                dist = math.hypot(tile_cx - mx, tile_cy - my)
                                trans_tiles.append({
                                    'x': x, 'y': y, 'dist': dist,
                                    'vx': (tile_cx - mx) / (dist + 1) * random.uniform(200, 900),
                                    'vy': (tile_cy - my) / (dist + 1) * random.uniform(200, 900),
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

    def _save_score(self, score, accuracy, grade, max_combo, counts):
        """Save personal best for the currently selected song/diff."""
        song_data = GlobalState.selected_song_data
        title = song_data.get("title", "Unknown")
        diff  = song_data.get("diff_name", "")
        mod_str = " + ".join(sorted(GlobalState.active_mods)) if GlobalState.active_mods else "None"
        return score_db.submit(
            song_title=title,
            diff_name=diff,
            score=score,
            accuracy=accuracy,
            grade=grade,
            max_combo=max_combo,
            mods=mod_str,
            counts=counts,
        )