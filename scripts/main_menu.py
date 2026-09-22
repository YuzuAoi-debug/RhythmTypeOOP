import os
import math
import random
from bisect import bisect_right
from typing import Any, Optional
import pygame
from global_state import GlobalState, get_asset_path, get_fps_target
from beatmap_parser import BeatmapParser


def draw_equalizer_ring(
    surface,
    center_pos,
    dynamic_data_source: Any = None,
    *,
    base_radius=205,
    bar_count=64,
    max_bar_length=42,
    bar_width=3,
    color=(0, 229, 255),
    normalize_data=True,
):
    """Draw an osu!-style radial equalizer around a logo center.

    ``dynamic_data_source`` may be a sequence of amplitudes, a callable that
    receives the current tick count and returns a sequence, or ``None``. When
    it is ``None``, a sine-wave animation keeps the ring moving without audio
    input. Sequence values are normalized to 0..1 by default; set
    ``normalize_data`` to ``False`` when supplying already-normalized values.
    """
    time_ms = pygame.time.get_ticks()
    data: Any = dynamic_data_source(time_ms) if callable(dynamic_data_source) else dynamic_data_source
    data = list(data) if data is not None else []

    peak = max((abs(float(value)) for value in data), default=0.0)
    center_x, center_y = center_pos

    for index in range(bar_count):
        angle = (math.tau * index) / bar_count
        if data and peak > 0:
            sample_index = int(index * len(data) / bar_count) % len(data)
            value = abs(float(data[sample_index]))
            amplitude = min(1.0, value / peak) if normalize_data else min(1.0, value)
        else:
            wave = math.sin(time_ms * 0.006 + angle * 5.0)
            amplitude = 0.18 + 0.82 * ((wave + 1.0) * 0.5)

        inner_x = center_x + math.cos(angle) * base_radius
        inner_y = center_y + math.sin(angle) * base_radius
        outer_radius = base_radius + amplitude * max_bar_length
        outer_x = center_x + math.cos(angle) * outer_radius
        outer_y = center_y + math.sin(angle) * outer_radius
        pygame.draw.line(
            surface,
            color,
            (round(inner_x), round(inner_y)),
            (round(outer_x), round(outer_y)),
            bar_width,
        )


class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        self.BG_COLOR = (14, 14, 18)
        self.PANEL_COLOR = (22, 22, 30)
        self.HOVER_COLOR = (40, 40, 56)
        self.ACCENT_COLOR = (0, 229, 255)
        self.TEXT_COLOR = (245, 245, 255)
        self.MUTED_COLOR = (110, 110, 140)
        self.BORDER_COLOR = (45, 48, 65)
        
        self.font_title = pygame.font.Font(get_asset_path("assets/font/RETROTECH.ttf"), 58)
        self.font_btn = pygame.font.Font(get_asset_path("assets/font/Comfortaa-Bold.ttf"), 24)
        self.font_btn_small = pygame.font.Font(get_asset_path("assets/font/Comfortaa-Bold.ttf"), 18)
        self.font_small = pygame.font.Font(get_asset_path("assets/font/RETROTECH.ttf"), 16)
        self.font_mono = pygame.font.Font(get_asset_path("assets/font/Comfortaa-Bold.ttf"), 12)
        
        self.playlist = []
        self.now_playing = ""
        self.menu_beats = []
        self.menu_started_at = None
        self.current_bg = None
        self.bg_cache = {}
        self.options_open = False
        self.active_slider = None  # 'music', 'sfx', 'offset'
        self.buttons = ["PLAY", "OPTIONS", "EXIT"]
        self.btn_hover_progress = [0.0, 0.0, 0.0]
        self.keyboard_focus_idx: Optional[int] = 0
        self.hovered_btn = None
        self.logo_press_progress = 0.0
        
        # Load logo assets
        self.logo_hero = None
        self.logo_small = None
        if os.path.exists(GlobalState.LOGO_PATH):
            try:
                raw_logo = pygame.image.load(GlobalState.LOGO_PATH).convert_alpha()
                self.logo_hero = pygame.transform.smoothscale(raw_logo, (390, 390))
                self.logo_small = pygame.transform.smoothscale(raw_logo, (76, 76))
            except Exception:
                pass
            
        self.visualizer_bars = [random.uniform(4, 18) for _ in range(8)]
        
        # Temporary settings buffer for options menu
        self.temp_speed = GlobalState.note_speed
        self.temp_music_volume = GlobalState.music_volume
        self.temp_sfx_volume = GlobalState.sfx_volume
        self.temp_audio_offset = GlobalState.audio_offset_ms
        self.temp_bg_brightness = GlobalState.bg_brightness
        self.fps_modes = ["60fps", "refresh_rate", "unlimited"]
        self.temp_fps_mode = GlobalState.fps_mode

        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        # Preview sound for effects volume
        self.preview_sound = None
        try:
            self.preview_sound = pygame.mixer.Sound(GlobalState.HITSOUND_PATH)
        except Exception:
            pass

        # Hover sound effect and state tracker
        self.hover_sound = None
        self.hovered_btn = None
        if os.path.exists(GlobalState.HOVER_SOUND_PATH):
            try:
                self.hover_sound = pygame.mixer.Sound(GlobalState.HOVER_SOUND_PATH)
            except Exception:
                pass

        # Click sound effect
        self.click_sound = None
        if os.path.exists(GlobalState.CLICK_SOUND_PATH):
            try:
                self.click_sound = pygame.mixer.Sound(GlobalState.CLICK_SOUND_PATH)
            except Exception:
                pass

        # Track end of song for playlist looping
        self.SONG_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.SONG_END)
        if not pygame.mixer.music.get_busy():
            self._play_next_song()
        else:
            self.now_playing = "Now Playing ♫ : Menu Track"
            self.menu_started_at = pygame.time.get_ticks()
            if GlobalState.song_list:
                song = GlobalState.song_list[0]
                self._load_bg(str(song.get("background_path") or ""))
                self._load_menu_beats(song)

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

    def _play_key_press(self):
        if self.preview_sound:
            try:
                self.preview_sound.set_volume(GlobalState.sfx_volume)
                self.preview_sound.play()
            except Exception:
                pass

    def _load_bg(self, path: Optional[str]):
        if not path:
            self.current_bg = None
            return
        if path in self.bg_cache:
            self.current_bg = self.bg_cache[path]
            return
        try:
            raw = pygame.image.load(path).convert()
            scaled = pygame.transform.smoothscale(raw, (self.width, self.height))
            # Dark stylish vignette for readibility
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            for x in range(self.width):
                ratio = x / self.width
                alpha = int(220 * max(0.0, 1.0 - ratio * 1.35)) + 25
                pygame.draw.line(overlay, (10, 11, 16, min(240, alpha)), (x, 0), (x, self.height))
            scaled.blit(overlay, (0, 0))
            self.bg_cache[path] = scaled
            self.current_bg = scaled
        except Exception:
            self.current_bg = None

    def _play_next_song(self):
        if not self.playlist:
            self.playlist = GlobalState.song_list.copy()
            random.shuffle(self.playlist)
        
        if self.playlist:
            song = self.playlist.pop(0)
            self.now_playing = f"NOW PLAYING ♫ : {song['title']}"
            self._load_menu_beats(song)
            self._load_bg(str(song.get("background_path") or ""))
            try:
                pygame.mixer.music.load(song["audio_path"])
                pygame.mixer.music.set_volume(GlobalState.music_volume)
                pygame.mixer.music.play()
                self.menu_started_at = pygame.time.get_ticks()
            except Exception:
                self.now_playing = "NOW PLAYING ♫ : (Audio file missing)"

    def _load_menu_beats(self, song):
        difficulties = song.get("difficulties") or []
        last_difficulty = difficulties[-1] if difficulties else {}
        beatmap_path = last_difficulty.get("osu_path", "")
        self.menu_beats = BeatmapParser.load_osu_beatmap(beatmap_path) if beatmap_path else []

    def _save_options(self):
        GlobalState.note_speed = self.temp_speed
        GlobalState.music_volume = self.temp_music_volume
        GlobalState.sfx_volume = self.temp_sfx_volume
        GlobalState.menu_volume = self.temp_music_volume
        GlobalState.game_volume = self.temp_sfx_volume
        GlobalState.fps_mode = self.temp_fps_mode
        GlobalState.audio_offset_ms = self.temp_audio_offset
        GlobalState.bg_brightness = self.temp_bg_brightness
        pygame.mixer.music.set_volume(GlobalState.music_volume)
        GlobalState.save_settings()

    def draw_skew_button(self, text, rect, progress, time_ms, skew=14):
        slide_offset = progress * 10
        x = rect.x + slide_offset
        y = rect.y
        w, h = rect.width, rect.height

        pts = [
            (x + skew, y),
            (x + w, y),
            (x + w - skew, y + h),
            (x, y + h)
        ]

        if progress > 0.01:
            pulse = (math.sin(time_ms * 0.007) + 1.0) * 0.5
            glow_layers = [
                (12, int((15 + 20 * pulse) * progress)),
                (7,  int((40 + 30 * pulse) * progress)),
                (3,  int((100 + 40 * pulse) * progress)),
            ]

            max_pad = 14
            glow_surf = pygame.Surface((w + max_pad * 2, h + max_pad * 2), pygame.SRCALPHA)

            for pad, alpha in glow_layers:
                if alpha <= 0:
                    continue
                g_pts = [
                    (max_pad + skew - pad, max_pad - pad),
                    (max_pad + w + pad, max_pad - pad),
                    (max_pad + w - skew + pad, max_pad + h + pad),
                    (max_pad - pad, max_pad + h + pad)
                ]
                pygame.draw.polygon(glow_surf, (*self.ACCENT_COLOR, alpha), g_pts)

            self.screen.blit(glow_surf, (x - max_pad, y - max_pad))

        depth_pts = [
            (x, y + h),
            (x + w - skew, y + h),
            (x + w - skew, y + h + 4),
            (x, y + h + 4)
        ]
        pygame.draw.polygon(self.screen, (10, 10, 15), depth_pts)

        body_color = (
            int(self.PANEL_COLOR[0] + (self.HOVER_COLOR[0] - self.PANEL_COLOR[0]) * progress),
            int(self.PANEL_COLOR[1] + (self.HOVER_COLOR[1] - self.PANEL_COLOR[1]) * progress),
            int(self.PANEL_COLOR[2] + (self.HOVER_COLOR[2] - self.PANEL_COLOR[2]) * progress),
        )
        pygame.draw.polygon(self.screen, body_color, pts)

        border_col = (
            int(self.BORDER_COLOR[0] + (self.ACCENT_COLOR[0] - self.BORDER_COLOR[0]) * progress),
            int(self.BORDER_COLOR[1] + (self.ACCENT_COLOR[1] - self.BORDER_COLOR[1]) * progress),
            int(self.BORDER_COLOR[2] + (self.ACCENT_COLOR[2] - self.BORDER_COLOR[2]) * progress),
        )
        pygame.draw.polygon(self.screen, border_col, pts, 2)

        if progress > 0.05:
            accent_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            tab_pts = [(skew, 0), (skew + 6, 0), (6, h), (0, h)]
            pygame.draw.polygon(accent_surf, (*self.ACCENT_COLOR, int(255 * progress)), tab_pts)
            self.screen.blit(accent_surf, (x, y))

        display_label = f"[  {text}  ]" if progress > 0.5 else text
        font_col = (
            int(self.TEXT_COLOR[0] + (self.ACCENT_COLOR[0] - self.TEXT_COLOR[0]) * progress),
            int(self.TEXT_COLOR[1] + (self.ACCENT_COLOR[1] - self.TEXT_COLOR[1]) * progress),
            int(self.TEXT_COLOR[2] + (self.ACCENT_COLOR[2] - self.TEXT_COLOR[2]) * progress),
        )

        if progress > 0.3:
            shadow_surf = self.font_btn.render(display_label, True, self.ACCENT_COLOR)
            shadow_surf.set_alpha(int(180 * progress))
            self.screen.blit(shadow_surf, shadow_surf.get_rect(center=(x + w // 2 + 5, y + h // 2 + 1)))

        surf = self.font_btn.render(display_label, True, font_col)
        self.screen.blit(surf, surf.get_rect(center=(x + w // 2 + 4, y + h // 2)))

    def draw_button(self, text, rect, is_hovered, small=False):
        color = self.HOVER_COLOR if is_hovered else self.PANEL_COLOR
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, self.ACCENT_COLOR if is_hovered else (50, 50, 70), rect, 2, border_radius=8)
        
        font = self.font_btn_small if small else self.font_btn
        surf = font.render(text, True, self.ACCENT_COLOR if is_hovered else self.TEXT_COLOR)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def draw_slider(self, label, value_norm, display_text, rect):
        label_surface = self.font_small.render(f"{label}  {display_text}", True, self.TEXT_COLOR)
        self.screen.blit(label_surface, (rect.x, rect.y - 23))
        pygame.draw.rect(self.screen, (45, 45, 60), rect, border_radius=6)
        fill_width = int(rect.width * max(0.0, min(1.0, value_norm)))
        fill_rect = pygame.Rect(rect.x, rect.y, fill_width, rect.height)
        pygame.draw.rect(self.screen, self.ACCENT_COLOR, fill_rect, border_radius=6)
        knob_x = rect.x + fill_width
        pygame.draw.circle(self.screen, self.TEXT_COLOR, (knob_x, rect.centery), 8)

    def draw_audio_visualizer(self, x, y):
        bar_w, gap = 3, 2
        for i in range(len(self.visualizer_bars)):
            target = random.uniform(3, 18)
            self.visualizer_bars[i] += (target - self.visualizer_bars[i]) * 0.25
            h = int(self.visualizer_bars[i])
            bx = x + i * (bar_w + gap)
            pygame.draw.rect(self.screen, self.ACCENT_COLOR, (bx, y - h, bar_w, h))

    def run(self, last_frame=None):
        clock = pygame.time.Clock()
        time_start = pygame.time.get_ticks()
        
        btn_width, btn_height = 280, 56
        start_y = self.height // 2 - 20
        
        play_rect = pygame.Rect(100, start_y, btn_width, btn_height)
        options_rect = pygame.Rect(100, start_y + 75, btn_width, btn_height)
        exit_rect = pygame.Rect(100, start_y + 150, btn_width, btn_height)
        menu_rects = [play_rect, options_rect, exit_rect]

        panel_rect = pygame.Rect(self.width // 2 - 270, self.height // 2 - 280, 540, 560)
        speed_minus_hundredth = pygame.Rect(panel_rect.x + 35, panel_rect.y + 110, 100, 36)
        speed_minus_tenth = pygame.Rect(panel_rect.x + 145, panel_rect.y + 110, 100, 36)
        speed_plus_hundredth = pygame.Rect(panel_rect.x + 295, panel_rect.y + 110, 100, 36)
        speed_plus_tenth = pygame.Rect(panel_rect.x + 405, panel_rect.y + 110, 100, 36)
        
        music_slider_rect = pygame.Rect(panel_rect.x + 35, panel_rect.y + 180, 470, 12)
        sfx_slider_rect = pygame.Rect(panel_rect.x + 35, panel_rect.y + 235, 470, 12)
        bg_slider_rect = pygame.Rect(panel_rect.x + 35, panel_rect.y + 290, 470, 12)
        offset_slider_rect = pygame.Rect(panel_rect.x + 35, panel_rect.y + 345, 470, 12)
        
        fps_rect = pygame.Rect(panel_rect.x + 35, panel_rect.y + 395, 470, 40)
        close_opt_rect = pygame.Rect(panel_rect.x + 35, panel_rect.y + 450, 470, 44)
        logo_hit_rect = pygame.Rect(100, 75, 76, 76)

        running = True
        while running:
            target_fps = get_fps_target(GlobalState.fps_mode)
            current_time = pygame.time.get_ticks()
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == self.SONG_END:
                    self._play_next_song()
                if event.type == pygame.DROPFILE:
                    from beatmap_importer import BeatmapImporter
                    imported = BeatmapImporter.import_file(event.file)
                    if imported:
                        pygame.mixer.music.stop()
                        return "song_select" 
                    
                if event.type == pygame.MOUSEMOTION and not self.options_open:
                    for rect in menu_rects:
                        if rect.collidepoint(event.pos):
                            self.keyboard_focus_idx = None
                            break
                                  
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.options_open:
                            self._save_options()
                            self.options_open = False
                            self.hovered_btn = None
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_clicked = True
                    if self.logo_small and logo_hit_rect.collidepoint(event.pos):
                        self.logo_press_progress = 1.0
                        self._play_key_press()
                    elif self.options_open:
                        if music_slider_rect.inflate(0, 18).collidepoint(mouse_pos):
                            self.active_slider = "music"
                        elif sfx_slider_rect.inflate(0, 18).collidepoint(mouse_pos):
                            self.active_slider = "sfx"
                        elif bg_slider_rect.inflate(0, 18).collidepoint(mouse_pos):
                            self.active_slider = "bg"
                        elif offset_slider_rect.inflate(0, 18).collidepoint(mouse_pos):
                            self.active_slider = "offset"
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.active_slider == "sfx" and self.preview_sound:
                        self.preview_sound.set_volume(self.temp_sfx_volume)
                        self.preview_sound.play()
                    self.active_slider = None
                    
            # Handle live slider dragging
            if self.active_slider == "music":
                self.temp_music_volume = max(0.0, min(1.0, (mouse_pos[0] - music_slider_rect.x) / music_slider_rect.width))
                pygame.mixer.music.set_volume(self.temp_music_volume)
            elif self.active_slider == "sfx":
                self.temp_sfx_volume = max(0.0, min(1.0, (mouse_pos[0] - sfx_slider_rect.x) / sfx_slider_rect.width))
            elif self.active_slider == "bg":
                self.temp_bg_brightness = max(0.0, min(1.0, (mouse_pos[0] - bg_slider_rect.x) / bg_slider_rect.width))
            elif self.active_slider == "offset":
                ratio = max(0.0, min(1.0, (mouse_pos[0] - offset_slider_rect.x) / offset_slider_rect.width))
                # Map 0..1 to -100ms..+100ms stepped to 5ms
                raw_ms = -100.0 + ratio * 200.0
                self.temp_audio_offset = round(raw_ms / 5.0) * 5.0

            # Render Background
            if self.current_bg:
                self.screen.blit(self.current_bg, (0, 0))
            else:
                self.screen.fill(self.BG_COLOR)

            # Left Branding & Track Info
            if self.logo_small:
                self.logo_press_progress = max(0.0, self.logo_press_progress - 0.12)
                logo_scale = 1.0 - self.logo_press_progress * 0.14
                logo_size = max(1, int(self.logo_small.get_width() * logo_scale))
                logo_image = self.logo_small
                if logo_size != self.logo_small.get_width():
                    logo_image = pygame.transform.smoothscale(self.logo_small, (logo_size, logo_size))
                logo_rect = logo_image.get_rect(center=logo_hit_rect.center)
                self.screen.blit(logo_image, logo_rect)
                click_me = self.font_mono.render("CLICK ME", True, self.ACCENT_COLOR)
                click_me = pygame.transform.rotate(click_me, 45)
                click_me_rect = click_me.get_rect(
                    bottomright=(logo_rect.left + 18, logo_rect.top + 20)
                )
                self.screen.blit(click_me, click_me_rect)
                logo_x, logo_y = 190, 76
            else:
                logo_x, logo_y = 100, 100

            # Dual-tone Brand Title (Shadows)
            title_font = pygame.font.Font(get_asset_path("assets/font/RETROTECH.ttf"), 72)
            surf_rhythm = title_font.render("RHYTHM", True, self.TEXT_COLOR)
            surf_type = title_font.render("TYPE", True, self.ACCENT_COLOR)
            total_brand_width = surf_rhythm.get_width() + surf_type.get_width() + 2
            brand_x = logo_x + max(0, (76 - total_brand_width) // 2)
            brand_y = logo_y

            shadow_rhythm = title_font.render("RHYTHM", True, (0, 0, 0))
            shadow_type = title_font.render("TYPE", True, (0, 0, 0))
            self.screen.blit(shadow_rhythm, (brand_x + 3, brand_y + 3))
            self.screen.blit(shadow_type, (brand_x + shadow_rhythm.get_width() + 2 + 3, brand_y + 3))

            self.screen.blit(surf_rhythm, (brand_x, brand_y))
            self.screen.blit(surf_type, (brand_x + surf_rhythm.get_width() + 2, brand_y))

            # Subtitles & Visualizer positions based on logo presence
            if self.logo_small:
                sub_surf = self.font_mono.render("PURE PYTHON RHYTHM-TYPING HYBRID", True, self.MUTED_COLOR)
                self.screen.blit(sub_surf, (190, 135))

                self.draw_audio_visualizer(100, 200)
                now_playing_surf = self.font_small.render(self.now_playing, True, self.ACCENT_COLOR)
                self.screen.blit(now_playing_surf, (145, 189))
            else:
                sub_surf = self.font_mono.render("PURE PYTHON RHYTHM-TYPING HYBRID", True, self.MUTED_COLOR)
                self.screen.blit(sub_surf, (190, 130))

                self.draw_audio_visualizer(105, 220)
                now_playing_surf = self.font_small.render(self.now_playing, True, self.ACCENT_COLOR)
                self.screen.blit(now_playing_surf, (150, 205))
                            
            # Right Hero Showcase
            if self.logo_hero and not self.options_open:
                hero_x = self.width - 470
                hero_y = self.height // 2 - 215

                music_pos = pygame.mixer.music.get_pos()
                if music_pos < 0 and self.menu_started_at is not None:
                    music_pos = pygame.time.get_ticks() - self.menu_started_at
                beat_pulse = 0.0
                beat_age = None
                if music_pos >= 0 and self.menu_beats:
                    song_position = music_pos / 1000.0
                    current_beat = bisect_right(self.menu_beats, song_position) - 1
                    if current_beat >= 0:
                        beat_age = song_position - self.menu_beats[current_beat]
                        if beat_age < 0.24:
                            beat_pulse = 1.0 - beat_age / 0.24
                            beat_pulse = beat_pulse * beat_pulse * (3.0 - 2.0 * beat_pulse)

                hero_scale = 1.0 + beat_pulse * 0.08
                hero_size = int(self.logo_hero.get_width() * hero_scale)
                hero_image = self.logo_hero
                if hero_size != self.logo_hero.get_width():
                    hero_image = pygame.transform.smoothscale(self.logo_hero, (hero_size, hero_size))
                hero_rect = hero_image.get_rect(center=(hero_x + self.logo_hero.get_width() // 2, hero_y + self.logo_hero.get_height() // 2))

                ring_bar_count = 128
                ring_data = []
                for index in range(ring_bar_count):
                    angle = (math.tau * index) / ring_bar_count
                    wave = (math.sin(current_time * 0.012 + angle * 4.0) + 1.0) * 0.5
                    ring_data.append(0.12 + wave * 0.12 + beat_pulse * (0.58 + wave * 0.30))

                draw_equalizer_ring(
                    self.screen,
                    hero_rect.center,
                    dynamic_data_source=ring_data,
                    base_radius=hero_image.get_width() // 2 + 10,
                    bar_count=ring_bar_count,
                    max_bar_length=42,
                    bar_width=3,
                    color=self.ACCENT_COLOR,
                    normalize_data=False,
                )
                self.screen.blit(hero_image, hero_rect)

            if self.options_open:
                # Dim background
                overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 185))
                self.screen.blit(overlay, (0, 0))
                
                # Options Box
                pygame.draw.rect(self.screen, self.PANEL_COLOR, panel_rect, border_radius=12)
                pygame.draw.rect(self.screen, (50, 50, 70), panel_rect, 2, border_radius=12)
                
                opt_title = self.font_btn.render("OPTIONS", True, self.TEXT_COLOR)
                self.screen.blit(opt_title, opt_title.get_rect(center=(self.width // 2, panel_rect.y + 40)))
                
                # Speed Adjuster UI
                speed_label = self.font_small.render("Note Speed", True, self.MUTED_COLOR)
                self.screen.blit(speed_label, speed_label.get_rect(center=(self.width // 2, panel_rect.y + 75)))
                
                speed_val = self.font_btn.render(f"{self.temp_speed:.2f}", True, self.ACCENT_COLOR)
                self.screen.blit(speed_val, speed_val.get_rect(center=(self.width // 2, panel_rect.y + 98)))
                
                self.draw_button("-0.01", speed_minus_hundredth, speed_minus_hundredth.collidepoint(mouse_pos), small=True)
                self.draw_button("-0.1", speed_minus_tenth, speed_minus_tenth.collidepoint(mouse_pos), small=True)
                self.draw_button("+0.01", speed_plus_hundredth, speed_plus_hundredth.collidepoint(mouse_pos), small=True)
                self.draw_button("+0.1", speed_plus_tenth, speed_plus_tenth.collidepoint(mouse_pos), small=True)
                
                self.draw_slider("Music Volume", self.temp_music_volume, f"{int(self.temp_music_volume * 100)}%", music_slider_rect)
                self.draw_slider("Sound Effects", self.temp_sfx_volume, f"{int(self.temp_sfx_volume * 100)}%", sfx_slider_rect)
                self.draw_slider("Background Brightness", self.temp_bg_brightness, f"{int(self.temp_bg_brightness * 100)}%", bg_slider_rect)
                
                offset_norm = (self.temp_audio_offset + 100.0) / 200.0
                self.draw_slider("Audio Offset", offset_norm, f"{int(self.temp_audio_offset):+d} ms", offset_slider_rect)
                
                fps_display = f"Frame Rate: {self.temp_fps_mode}"
                if self.temp_fps_mode == "refresh_rate":
                    fps_display += f" ({get_fps_target('refresh_rate')}Hz)"
                self.draw_button(fps_display, fps_rect, fps_rect.collidepoint(mouse_pos), small=True)
                self.draw_button("Save & Close (ESC)", close_opt_rect, close_opt_rect.collidepoint(mouse_pos), small=True)
                
                # Hover tracking for options menu buttons
                curr_opt_hover = None
                if speed_minus_hundredth.collidepoint(mouse_pos):
                    curr_opt_hover = "spd_-001"
                elif speed_minus_tenth.collidepoint(mouse_pos):
                    curr_opt_hover = "spd_-01"
                elif speed_plus_hundredth.collidepoint(mouse_pos):
                    curr_opt_hover = "spd_+001"
                elif speed_plus_tenth.collidepoint(mouse_pos):
                    curr_opt_hover = "spd_+01"
                elif fps_rect.collidepoint(mouse_pos):
                    curr_opt_hover = "fps"
                elif close_opt_rect.collidepoint(mouse_pos):
                    curr_opt_hover = "close"

                if curr_opt_hover != self.hovered_btn:
                    if curr_opt_hover is not None:
                        self._play_hover()
                    self.hovered_btn = curr_opt_hover

                if mouse_clicked:
                    if speed_minus_hundredth.collidepoint(mouse_pos):
                        self._play_click()
                        self.temp_speed = max(0.01, round(self.temp_speed - 0.01, 2))
                    elif speed_minus_tenth.collidepoint(mouse_pos):
                        self._play_click()
                        self.temp_speed = max(0.01, round(self.temp_speed - 0.1, 2))
                    elif speed_plus_hundredth.collidepoint(mouse_pos):
                        self._play_click()
                        self.temp_speed = min(20.0, round(self.temp_speed + 0.01, 2))
                    elif speed_plus_tenth.collidepoint(mouse_pos):
                        self._play_click()
                        self.temp_speed = min(20.0, round(self.temp_speed + 0.1, 2))
                    elif fps_rect.collidepoint(mouse_pos):
                        self._play_click()
                        current_index = self.fps_modes.index(self.temp_fps_mode) if self.temp_fps_mode in self.fps_modes else 0
                        self.temp_fps_mode = self.fps_modes[(current_index + 1) % len(self.fps_modes)]
                    elif close_opt_rect.collidepoint(mouse_pos):
                        self._play_click()
                        self._save_options()
                        self.options_open = False
                        self.hovered_btn = None
            else:
                curr_hover = None
                for i, (name, rect) in enumerate(zip(self.buttons, menu_rects)):
                    mouse_over = rect.collidepoint(mouse_pos)
                    key_over = (self.keyboard_focus_idx == i)
                    if mouse_over or key_over:
                        curr_hover = name.lower()

                if curr_hover != self.hovered_btn:
                    if curr_hover is not None:
                        self._play_hover()
                    self.hovered_btn = curr_hover

                # Smoothly update animation progress per button (lerp)
                for i, rect in enumerate(menu_rects):
                    is_active = (rect.collidepoint(mouse_pos) or self.keyboard_focus_idx == i)
                    target = 1.0 if is_active else 0.0
                    self.btn_hover_progress[i] += (target - self.btn_hover_progress[i]) * 0.2
                    if abs(self.btn_hover_progress[i] - target) < 0.005:
                        self.btn_hover_progress[i] = target

                # Render Main Buttons with smooth slanted animation and zero-residual glow
                for i, (name, rect) in enumerate(zip(self.buttons, menu_rects)):
                    self.draw_skew_button(name, rect, self.btn_hover_progress[i], current_time)

                # Arcade Keybinds Footer
                footer_y = self.height - 35
                pygame.draw.line(self.screen, (30, 32, 45), (0, footer_y - 10), (self.width, footer_y - 10), 1)
                hud_text = self.font_mono.render("[ ENTER / CLICK ] SELECT     [ DRAG & DROP ] BEATMAP FILE", True, self.MUTED_COLOR)
                self.screen.blit(hud_text, (100, footer_y))
                                
                if mouse_clicked:
                    if play_rect.collidepoint(mouse_pos):
                        self._play_click()
                        return "song_select"
                    elif options_rect.collidepoint(mouse_pos):
                        self._play_click()
                        self.temp_speed = GlobalState.note_speed
                        self.temp_music_volume = GlobalState.music_volume
                        self.temp_sfx_volume = GlobalState.sfx_volume
                        self.temp_audio_offset = GlobalState.audio_offset_ms
                        self.temp_bg_brightness = GlobalState.bg_brightness
                        self.temp_fps_mode = GlobalState.fps_mode
                        self.options_open = True
                        self.hovered_btn = None
                    elif exit_rect.collidepoint(mouse_pos):
                        self._play_click()
                        return "quit"

            if last_frame:
                fade_progress = min(1.0, (pygame.time.get_ticks() - time_start) / 600.0)
                if fade_progress < 1.0:
                    if not hasattr(self, 'trans_data') or self.trans_data['time_start'] != time_start:
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
                        self.trans_data = {'tiles': trans_tiles, 'mx': mx, 'my': my, 'time_start': time_start}
                    
                    for t in self.trans_data['tiles']:
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
                        pygame.draw.circle(shock_surf, (0, 229, 255, int(255 * (1.0 - fade_progress))), (self.trans_data['mx'], self.trans_data['my']), int(shockwave_radius), shockwave_thickness)
                        for _ in range(40):
                            angle = random.uniform(0, math.pi * 2)
                            r_offset = random.uniform(-shockwave_thickness, shockwave_thickness * 1.5)
                            px = self.trans_data['mx'] + math.cos(angle) * (shockwave_radius + r_offset)
                            py = self.trans_data['my'] + math.sin(angle) * (shockwave_radius + r_offset)
                            psize = random.randint(2, 8)
                            palpha = int(255 * (1.0 - fade_progress) * random.uniform(0.5, 1.0))
                            pygame.draw.circle(shock_surf, (0, 255, 255, palpha), (int(px), int(py)), psize)
                    self.screen.blit(shock_surf, (0, 0))

            pygame.display.flip()
            clock.tick(target_fps)