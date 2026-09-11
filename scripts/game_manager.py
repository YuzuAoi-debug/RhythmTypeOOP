import pygame
import sys
import math
from global_state import GlobalState
from conductor import Conductor
from beatmap_parser import BeatmapParser

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
        
        # Fonts
        self.font_large = pygame.font.SysFont("Arial", 44, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 16)
        
        # Gameplay Constants (From letter_note.gd)
        self.SCROLL_SPEED = 400.0
        self.SPAWN_DISTANCE = 900.0
        
        self.PERFECT_WINDOW = 0.04  # 40ms
        self.GREAT_WINDOW = 0.08    # 80ms
        self.GOOD_WINDOW = 0.12     # 120ms
        self.MISS_WINDOW = 0.15     # 150ms
        
        # Horizontal layout coordinates
        self.target_x = 200
        self.lane_y = self.height // 2 - 50

    def _draw_centered(self, text, font, color, y):
        surface = font.render(text, True, color)
        self.screen.blit(surface, surface.get_rect(center=(self.width // 2, y)))

    def _pause_screen(self, clock):
        pygame.mixer.music.pause()
        panel_rect = pygame.Rect(self.width // 2 - 260, self.height // 2 - 180, 520, 360)
        resume_rect = pygame.Rect(panel_rect.x + 40, panel_rect.y + 150, 130, 50)
        checkpoint_rect = pygame.Rect(panel_rect.x + 195, panel_rect.y + 150, 130, 50)
        menu_rect = pygame.Rect(panel_rect.x + 350, panel_rect.y + 150, 130, 50)
        while True:
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.mixer.music.stop()
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_clicked = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.mixer.music.unpause()
                        return "resume"
                    if event.key == pygame.K_r and event.mod & pygame.KMOD_CTRL:
                        pygame.mixer.music.stop()
                        return "retry"

            if mouse_clicked:
                if resume_rect.collidepoint(mouse_pos):
                    pygame.mixer.music.unpause()
                    return "resume"
                if checkpoint_rect.collidepoint(mouse_pos):
                    pygame.mixer.music.stop()
                    return "retry"
                if menu_rect.collidepoint(mouse_pos):
                    pygame.mixer.music.stop()
                    return "menu"

            pygame.draw.rect(self.screen, self.BG_COLOR, (0, 0, self.width, self.height))
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 210))
            self.screen.blit(overlay, (0, 0))
            pygame.draw.rect(self.screen, (22, 22, 30), panel_rect, border_radius=12)
            self._draw_centered("PAUSED", self.font_large, self.TEXT_COLOR, self.height // 2 - 90)
            self._draw_centered("ESC  Resume     CTRL+R  Restore Checkpoint", self.font_small, self.MUTED_COLOR, self.height // 2 - 35)
            self._draw_centered("Use the buttons below", self.font_small, self.MUTED_COLOR, self.height // 2 + 5)
            self._draw_button("RESUME", resume_rect, resume_rect.collidepoint(mouse_pos))
            self._draw_button("RESTORE", checkpoint_rect, checkpoint_rect.collidepoint(mouse_pos))
            self._draw_button("MENU", menu_rect, menu_rect.collidepoint(mouse_pos))
            pygame.display.flip()
            clock.tick(30)

    def _draw_button(self, text, rect, hovered):
        color = (40, 40, 56) if hovered else (28, 28, 38)
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, self.ACCENT_COLOR if hovered else (70, 70, 90), rect, 2, border_radius=8)
        surface = self.font_small.render(text, True, self.TEXT_COLOR)
        self.screen.blit(surface, surface.get_rect(center=rect.center))

    def _show_fail_screen(self, score, max_combo, clock):
        pygame.mixer.music.stop()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and event.mod & pygame.KMOD_CTRL:
                        return "retry"
                    if event.key in (pygame.K_ESCAPE, pygame.K_m):
                        return "menu"

            self.screen.fill(self.BG_COLOR)
            self._draw_centered("FAILED", self.font_large, (255, 70, 70), 180)
            self._draw_centered(f"Score  {int(score):06d}", self.font_med, self.TEXT_COLOR, 280)
            self._draw_centered(f"Max combo  {max_combo}x", self.font_med, self.TEXT_COLOR, 325)
            self._draw_centered("CTRL+R  Retry     ESC  Menu", self.font_small, self.MUTED_COLOR, 500)
            pygame.display.flip()
            clock.tick(30)

    def _show_results(self, score, max_combo, timing_errors, counts, clock):
        pygame.mixer.music.stop()
        total = max(1, sum(counts.values()))
        weighted = counts["perfect"] * 1.0 + counts["great"] * 0.8 + counts["good"] * 0.5
        accuracy = weighted / total
        if counts["miss"] == 0 and accuracy >= 0.98:
            grade = "SS"
        elif accuracy >= 0.90:
            grade = "S"
        elif accuracy >= 0.80:
            grade = "A"
        elif accuracy >= 0.70:
            grade = "B"
        elif accuracy >= 0.60:
            grade = "C"
        else:
            grade = "D"

        ur_value = 0.0
        if len(timing_errors) > 1:
            mean_error = sum(timing_errors) / len(timing_errors)
            variance = sum((error - mean_error) ** 2 for error in timing_errors) / len(timing_errors)
            ur_value = math.sqrt(variance) * 10.0

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and event.mod & pygame.KMOD_CTRL:
                        return "retry"
                    if event.key in (pygame.K_ESCAPE, pygame.K_m, pygame.K_RETURN):
                        return "menu"

            self.screen.fill(self.BG_COLOR)
            self._draw_centered("RESULTS", self.font_med, self.TEXT_COLOR, 90)
            self._draw_centered(grade, pygame.font.SysFont("Arial", 100, bold=True), self.ACCENT_COLOR, 205)
            self._draw_centered(f"Accuracy  {accuracy * 100:.2f}%", self.font_med, self.TEXT_COLOR, 310)
            self._draw_centered(f"Score  {int(score):06d}    Max combo  {max_combo}x", self.font_small, self.TEXT_COLOR, 355)
            self._draw_centered(f"PERFECT {counts['perfect']}   GREAT {counts['great']}   GOOD {counts['good']}   MISS {counts['miss']}", self.font_small, self.MUTED_COLOR, 395)
            self._draw_centered(f"UR  {ur_value:.1f}ms", self.font_small, self.MUTED_COLOR, 430)
            self._draw_centered("CTRL+R  Retry     ENTER / ESC / M  Menu", self.font_small, self.MUTED_COLOR, 535)
            pygame.display.flip()
            clock.tick(30)

    def run(self):
        pygame.mixer.init()
        
        song_data = GlobalState.selected_song_data
        try:
            pygame.mixer.music.load(song_data.get("audio_path", ""))
            pygame.mixer.music.set_volume(GlobalState.game_volume)
        except Exception:
            print("Audio file missing, running silent simulation.")
            
        hit_times = BeatmapParser.load_osu_beatmap(song_data.get("osu_path", ""))
        word_bank = ["LETTERS", "RHYTHM", "PYTHON", "KEYBOARD", "SPEED", "ACCURACY", "DYNAMIC", "CODE", "FLOW", "MUSIC"]
        
        notes = []
        word_index = 0
        char_counter = 0
        current_word = word_bank[0]
        
        for t in hit_times:
            char = current_word[char_counter]
            notes.append({
                "target_time": t,
                "char": char,
                "word": current_word,
                "x": self.target_x + self.SPAWN_DISTANCE,
                "visible": False,
                "hit": False,
                "missed": False
            })
            char_counter += 1
            if char_counter >= len(current_word):
                word_index = (word_index + 1) % len(word_bank)
                current_word = word_bank[word_index]
                char_counter = 0

        conductor = Conductor(bpm=130.0)
        conductor.start_song()
        
        score = 0
        combo = 0
        max_combo = 0
        hp = GlobalState.hp
        counts = {"perfect": 0, "great": 0, "good": 0, "miss": 0}
        
        # Animation & Juice State Variables
        feedback_text = ""
        feedback_timer = 0.0
        feedback_max_time = 0.4
        feedback_color = self.TEXT_COLOR
        feedback_y_offset = 0.0
        hit_ripples = [] 
        
        timing_errors = []
        clock = pygame.time.Clock()
        if GlobalState.fps_mode == "unlimited":
            target_fps = 0
        elif GlobalState.fps_mode == "refresh_rate":
            target_fps = 60
        else:
            target_fps = 60
        running = True
        
        while running:
            dt = clock.tick(target_fps) / 1000.0
            conductor.update()
            
            # Speed scaling logic from letter_note.gd
            speed_multiplier = GlobalState.note_speed / 9.0
            current_speed = self.SCROLL_SPEED * speed_multiplier
            max_travel_time = self.SPAWN_DISTANCE / current_speed
            
            current_time = conductor.song_position
            
            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.mixer.music.stop()
                    return "quit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pause_result = self._pause_screen(clock)
                        if pause_result != "resume":
                            return "quit" if pause_result == "quit" else "play" if pause_result == "retry" else "menu"
                        
                    key_char = pygame.key.name(event.key).upper()
                    active_notes = [n for n in notes if not n["hit"] and not n["missed"]]
                    
                    if active_notes:
                        oldest = active_notes[0]
                        time_error = current_time - oldest["target_time"]
                        
                        if abs(time_error) <= self.MISS_WINDOW:
                            if key_char == oldest["char"]:
                                error_ms = time_error * 1000.0
                                timing_errors.append(error_ms)
                                
                                abs_err = abs(time_error)
                                if abs_err <= self.PERFECT_WINDOW:
                                    feedback_text = "PERFECT!"
                                    feedback_color = (0, 255, 180)
                                    score += 300 * (1 + combo * 0.1)
                                    combo += 1
                                    counts["perfect"] += 1
                                    hp = min(100.0, hp + 1.0)
                                elif abs_err <= self.GREAT_WINDOW:
                                    feedback_text = "GREAT!"
                                    feedback_color = (100, 220, 255)
                                    score += 150 * (1 + combo * 0.1)
                                    combo += 1
                                    counts["great"] += 1
                                    hp = min(100.0, hp + 0.5)
                                else:
                                    feedback_text = "GOOD"
                                    feedback_color = (255, 200, 0)
                                    score += 50 * (1 + combo * 0.1)
                                    combo += 1
                                    counts["good"] += 1
                                    
                                oldest["hit"] = True
                                feedback_timer = feedback_max_time
                                feedback_y_offset = 0.0
                                
                                # Spawn lazer-style expanding hit ripple ring
                                hit_ripples.append({
                                    "x": self.target_x,
                                    "y": self.lane_y,
                                    "radius": 35.0,
                                    "alpha": 255.0,
                                    "color": feedback_color
                                })
                                
                                if combo > max_combo: max_combo = combo
                            else:
                                feedback_text = "WRONG"
                                feedback_color = (255, 70, 70)
                                combo = 0
                                hp = max(0.0, hp - 5.0)
                                feedback_timer = feedback_max_time
                                feedback_y_offset = 0.0

            # Check missed notes
            for n in notes:
                if not n["hit"] and not n["missed"]:
                    if current_time > n["target_time"] + self.MISS_WINDOW:
                        n["missed"] = True
                        counts["miss"] += 1
                        hp = max(0.0, hp - 8.0)
                        feedback_text = "MISS"
                        feedback_color = (255, 60, 60)
                        combo = 0
                        feedback_timer = feedback_max_time
                        feedback_y_offset = 0.0

            if hp <= 0:
                return self._show_fail_screen(score, max_combo, clock)

            if notes and all(n["hit"] or n["missed"] for n in notes):
                return self._show_results(score, max_combo, timing_errors, counts, clock)

            # --- RENDERING ---
            self.screen.fill(self.BG_COLOR)

            # HP bar
            hp_bar_rect = pygame.Rect(350, 35, self.width - 450, 18)
            pygame.draw.rect(self.screen, (55, 30, 38), hp_bar_rect, border_radius=6)
            hp_fill = pygame.Rect(hp_bar_rect.x, hp_bar_rect.y, int(hp_bar_rect.width * hp / 100.0), hp_bar_rect.height)
            pygame.draw.rect(self.screen, (70, 220, 150) if hp > 30 else (255, 80, 80), hp_fill, border_radius=6)
            hp_label = self.font_small.render(f"HP {hp:.0f}%", True, self.TEXT_COLOR)
            self.screen.blit(hp_label, (self.width - 90, 34))
            
            # Draw Horizontal Target Lane & Ambient Rings
            pygame.draw.line(self.screen, self.LINE_COLOR, (0, self.lane_y), (self.width, self.lane_y), 4)
            pygame.draw.circle(self.screen, (25, 25, 38), (self.target_x, self.lane_y), 45)
            pygame.draw.circle(self.screen, self.ACCENT_COLOR, (self.target_x, self.lane_y), 45, 3)
            
            # Update & Render Smooth Expanding Hit Ripples
            for ripple in hit_ripples[:]:
                ripple["radius"] += 120.0 * dt
                ripple["alpha"] -= 450.0 * dt
                if ripple["alpha"] <= 0:
                    hit_ripples.remove(ripple)
                else:
                    surface = pygame.Surface((150, 150), pygame.SRCALPHA)
                    pygame.draw.circle(surface, (*ripple["color"], int(max(0, ripple["alpha"]))), (75, 75), int(ripple["radius"]), 3)
                    self.screen.blit(surface, (ripple["x"] - 75, ripple["y"] - 75))

            # Update and Draw Scrolling Notes (Right to Left)
            for n in notes:
                if n["hit"] or n["missed"]:
                    continue
                    
                time_left = n["target_time"] - current_time
                
                # letter_note.gd visibility logic
                if time_left > max_travel_time:
                    n["visible"] = False
                    n["x"] = self.target_x + self.SPAWN_DISTANCE
                else:
                    n["visible"] = True
                    n["x"] = self.target_x + (time_left * current_speed)
                
                if n["visible"] and n["x"] >= -50:
                    # Calculate smooth fade-in alpha near spawn boundary
                    dist_from_spawn = (self.target_x + self.SPAWN_DISTANCE) - n["x"]
                    alpha_factor = min(1.0, dist_from_spawn / 100.0) if dist_from_spawn < 100 else 1.0
                    
                    note_surface = pygame.Surface((70, 70), pygame.SRCALPHA)
                    pygame.draw.rect(note_surface, (30, 30, 45, int(220 * alpha_factor)), (0, 0, 70, 70), border_radius=15)
                    pygame.draw.rect(note_surface, (*self.ACCENT_COLOR, int(255 * alpha_factor)), (0, 0, 70, 70), 3, border_radius=15)
                    
                    char_surf = self.font_med.render(n["char"], True, self.TEXT_COLOR)
                    note_surface.blit(char_surf, char_surf.get_rect(center=(35, 35)))
                    
                    self.screen.blit(note_surface, (n["x"] - 35, self.lane_y - 35))

            # --- MONKEYTYPE UI GUIDE ---
            hud_y = self.lane_y + 120
            pygame.draw.line(self.screen, self.LINE_COLOR, (350, hud_y - 15), (self.width - 350, hud_y - 15), 1)
            
            upcoming_notes = [n for n in notes if not n["hit"] and not n["missed"]][:8]
            if upcoming_notes:
                guide_label = self.font_small.render("UPCOMING WORDS GUIDE", True, self.MUTED_COLOR)
                self.screen.blit(guide_label, (self.width // 2 - guide_label.get_width() // 2, hud_y))
                
                full_sequence = " ".join([n["word"] for n in upcoming_notes])
                seq_surf = self.font_med.render(full_sequence[:32], True, self.TEXT_COLOR)
                self.screen.blit(seq_surf, (self.width // 2 - seq_surf.get_width() // 2, hud_y + 25))

            # --- HUD: Score & Combo ---
            score_surf = self.font_med.render(f"{int(score):06d}", True, self.TEXT_COLOR)
            self.screen.blit(score_surf, (50, 40))
            
            if combo > 1:
                combo_surf = self.font_large.render(f"{combo}x", True, self.ACCENT_COLOR)
                self.screen.blit(combo_surf, (50, 80))

            # Smooth Animated Judgement Popups
            if feedback_timer > 0:
                feedback_timer -= dt
                feedback_y_offset -= 30.0 * dt
                
                progress_ratio = feedback_timer / feedback_max_time
                current_alpha = max(0, min(255, int(255 * progress_ratio)))
                
                fb_surface = self.font_large.render(feedback_text, True, feedback_color)
                alpha_fb = pygame.Surface(fb_surface.get_size(), pygame.SRCALPHA)
                alpha_fb.fill((255, 255, 255, current_alpha))
                fb_surface.blit(alpha_fb, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                self.screen.blit(fb_surface, fb_surface.get_rect(center=(self.target_x, self.lane_y - 90 + feedback_y_offset)))

            # --- UNSTABLE RATE (UR) WINDOW ---
            ur_value = 0.0
            if len(timing_errors) > 1:
                mean_err = sum(timing_errors) / len(timing_errors)
                variance = sum((x - mean_err) ** 2 for x in timing_errors) / len(timing_errors)
                ur_value = math.sqrt(variance) * 10.0
                
            ur_surf = self.font_small.render(f"UR: {ur_value:.1f}ms  |  MAX COMBO: {max_combo}", True, self.MUTED_COLOR)
            self.screen.blit(ur_surf, (self.width // 2 - ur_surf.get_width() // 2, self.height - 35))

            pygame.display.flip()