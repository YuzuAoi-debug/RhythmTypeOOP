import os
import wave
import math
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
        
        # Fonts
        self.font_large = pygame.font.SysFont("Arial", 44, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 16)
        self.font_guide = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_score = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_combo = pygame.font.SysFont("Arial", 52, bold=True)
        
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

    def _draw_button(self, text, rect, hovered):
        color = (45, 45, 62) if hovered else (26, 26, 36)
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, self.ACCENT_COLOR if hovered else (65, 65, 85), rect, 2, border_radius=8)
        surface = self.font_small.render(text, True, self.ACCENT_COLOR if hovered else self.TEXT_COLOR)
        self.screen.blit(surface, surface.get_rect(center=rect.center))

    def _pause_screen(self, conductor, clock):
        conductor.pause()
        panel_rect = pygame.Rect(self.width // 2 - 260, self.height // 2 - 180, 520, 360)
        resume_rect = pygame.Rect(panel_rect.x + 40, panel_rect.y + 240, 130, 50)
        retry_rect = pygame.Rect(panel_rect.x + 195, panel_rect.y + 240, 130, 50)
        menu_rect = pygame.Rect(panel_rect.x + 350, panel_rect.y + 240, 130, 50)

        # Snapshot background frame once so repeated frames do NOT compound into pitch black
        frozen_frame = self.screen.copy()
        dim_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim_overlay.fill((0, 0, 0, 175))

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

            # Render frozen gameplay frame with single dimming overlay
            self.screen.blit(frozen_frame, (0, 0))
            self.screen.blit(dim_overlay, (0, 0))

            pygame.draw.rect(self.screen, (22, 22, 30), panel_rect, border_radius=12)
            pygame.draw.rect(self.screen, (50, 50, 70), panel_rect, 2, border_radius=12)

            self._draw_centered("PAUSED", self.font_large, self.TEXT_COLOR, self.height // 2 - 90)
            self._draw_centered("ESC: Resume   |   CTRL + R: Restart Track", self.font_small, self.MUTED_COLOR, self.height // 2 - 30)
            self._draw_centered("Use buttons below to navigate", self.font_small, self.MUTED_COLOR, self.height // 2 + 10)

            self._draw_button("RESUME", resume_rect, resume_rect.collidepoint(mouse_pos))
            self._draw_button("RETRY", retry_rect, retry_rect.collidepoint(mouse_pos))
            self._draw_button("MENU", menu_rect, menu_rect.collidepoint(mouse_pos))

            pygame.display.flip()
            clock.tick(30)

    def _show_fail_screen(self, score, max_combo, clock):
        pygame.mixer.music.stop()
        retry_rect = pygame.Rect(self.width // 2 - 160, 420, 140, 48)
        menu_rect = pygame.Rect(self.width // 2 + 20, 420, 140, 48)

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
                    if event.key in (pygame.K_ESCAPE, pygame.K_m):
                        return "menu"

            if mouse_clicked:
                if retry_rect.collidepoint(mouse_pos):
                    return "retry"
                if menu_rect.collidepoint(mouse_pos):
                    return "menu"

            self.screen.fill(self.BG_COLOR)
            self._draw_centered("FAILED", self.font_large, (255, 70, 70), 160)
            self._draw_centered(f"Score  {int(score):06d}", self.font_med, self.TEXT_COLOR, 250)
            self._draw_centered(f"Max Combo  {max_combo}x", self.font_med, self.TEXT_COLOR, 300)
            self._draw_centered("Press CTRL+R or click buttons below", self.font_small, self.MUTED_COLOR, 365)

            self._draw_button("RETRY", retry_rect, retry_rect.collidepoint(mouse_pos))
            self._draw_button("MENU", menu_rect, menu_rect.collidepoint(mouse_pos))

            pygame.display.flip()
            clock.tick(30)

    def _show_results(self, score, max_combo, timing_errors, counts, ur_value, clock):
        pygame.mixer.music.stop()
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

    def run(self):
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
        conductor.start_song()

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

        # O(1) Running Unstable Rate (UR) tracking
        timing_errors = []
        err_count = 0
        err_sum = 0.0
        err_sum_sq = 0.0
        ur_value = 0.0
        ur_text_surf = self.font_small.render(f"UR: 0.0  |  MAX COMBO: 0", True, self.MUTED_COLOR)

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

        running = True
        while running:
            dt = clock.tick(target_fps) / 1000.0
            conductor.update()

            speed_multiplier = GlobalState.note_speed / 9.0
            current_speed = self.SCROLL_SPEED * speed_multiplier
            max_travel_time = self.SPAWN_DISTANCE / current_speed

            current_time = conductor.song_position

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
                    current_note_idx += 1
                else:
                    break

            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    conductor.stop()
                    return "quit"
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

                                if combo > max_combo:
                                    max_combo = combo
                                ur_text_surf = self.font_small.render(f"UR: {ur_value:.1f}  |  MAX COMBO: {max_combo}", True, self.MUTED_COLOR)

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

            # Fail condition (ignored if No Fail mod is active)
            if hp <= 0 and not is_nf:
                conductor.stop()
                return self._show_fail_screen(score, max_combo, clock)

            # Completion condition
            if current_note_idx >= len(notes):
                song_ended = True

            if song_ended:
                end_cooldown -= dt
                if end_cooldown <= 0.0:
                    conductor.stop()
                    return self._show_results(score, max_combo, timing_errors, counts, ur_value, clock)

            # --- RENDERING ---
            if bg_surface:
                self.screen.blit(bg_surface, (0, 0))
            else:
                self.screen.fill(self.BG_COLOR)

            # HP bar
            hp_bar_rect = pygame.Rect(350, 35, self.width - 450, 18)
            pygame.draw.rect(self.screen, (55, 30, 38), hp_bar_rect, border_radius=6)
            hp_fill = pygame.Rect(hp_bar_rect.x, hp_bar_rect.y, int(hp_bar_rect.width * hp / 100.0), hp_bar_rect.height)
            pygame.draw.rect(self.screen, (70, 220, 150) if hp > 30 else (255, 80, 80), hp_fill, border_radius=6)
            hp_label = self.font_small.render(f"HP {hp:.0f}%", True, self.TEXT_COLOR)
            self.screen.blit(hp_label, (self.width - 90, 34))

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
            pygame.draw.line(self.screen, self.LINE_COLOR, (0, self.lane_y), (self.width, self.lane_y), 4)
            pygame.draw.circle(self.screen, (25, 25, 38), (self.target_x, self.lane_y), 45)
            pygame.draw.circle(self.screen, self.ACCENT_COLOR, (self.target_x, self.lane_y), 45, 3)

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
            pygame.draw.line(self.screen, self.LINE_COLOR, (300, hud_y - 15), (self.width - 300, hud_y - 15), 1)

            guide_label = self.font_small.render("UPCOMING WORDS", True, self.MUTED_COLOR)
            self.screen.blit(guide_label, (self.width // 2 - guide_label.get_width() // 2, hud_y))

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

            # --- UNSTABLE RATE (UR) WINDOW ---
            self.screen.blit(ur_text_surf, (self.width // 2 - ur_text_surf.get_width() // 2, self.height - 35))

            pygame.display.flip()

        conductor.stop()
        return "menu"