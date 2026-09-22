import time
import pygame
from global_state import GlobalState

class Conductor:
    """Accurate audio synchronization engine utilizing monotonic high-precision time
    with audio buffer latency compensation and smooth pause handling.
    """
    def __init__(self, bpm: float = 120.0):
        self.time_multiplier = 1.5 if "DT" in GlobalState.active_mods else 1.0
        self.bpm = bpm * self.time_multiplier
        self.sec_per_beat = 60.0 / self.bpm if self.bpm > 0 else 0.5
        self.song_position = 0.0
        self.song_position_in_beats = 0.0
        
        self.start_time = 0.0
        self.audio_start_pos = 0.0
        self.total_paused_time = 0.0
        self.pause_start_time = 0.0
        
        self.is_playing = False
        self.is_paused = False
        self.audio_synced = False
        self.audio_sync_offset = 0.0

    def start_song(self, start_sec: float = 0.0):
        """Starts song playback from start_sec (in seconds) and resets synchronization timers."""
        self.audio_start_pos = max(0.0, start_sec)
        self.start_time = time.perf_counter()
        self.total_paused_time = 0.0
        self.song_position = self.audio_start_pos
        self.song_position_in_beats = self.song_position / self.sec_per_beat
        self.is_playing = True
        self.is_paused = False
        self.audio_synced = False
        self.audio_sync_offset = 0.0

        try:
            audio_start = max(0.0, self.audio_start_pos / self.time_multiplier)
            pygame.mixer.music.play(start=audio_start)
        except pygame.error as e:
            print(f"Warning: Failed to play music: {e}")

    def pause(self):
        """Pauses audio playback and tracks pause timestamp."""
        if self.is_playing and not self.is_paused:
            self.is_paused = True
            self.pause_start_time = time.perf_counter()
            try:
                pygame.mixer.music.pause()
            except pygame.error:
                pass

    def unpause(self):
        """Resumes audio playback and compensates for pause duration."""
        if self.is_playing and self.is_paused:
            pause_duration = time.perf_counter() - self.pause_start_time
            self.total_paused_time += max(0.0, pause_duration)
            self.is_paused = False
            try:
                pygame.mixer.music.unpause()
            except pygame.error:
                pass

    def stop(self):
        """Stops audio and resets states."""
        self.is_playing = False
        self.is_paused = False
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass

    def seek(self, target_sec: float):
        """Seeks music playback and conductor clock to target_sec in seconds."""
        if not self.is_playing:
            return

        self.audio_start_pos = max(0.0, target_sec)
        self.start_time = time.perf_counter()
        self.total_paused_time = 0.0
        self.audio_synced = False
        self.audio_sync_offset = 0.0
        self.song_position = self.audio_start_pos
        self.song_position_in_beats = self.song_position / self.sec_per_beat

        try:
            audio_pos = max(0.0, self.audio_start_pos / self.time_multiplier)
            pygame.mixer.music.play(start=audio_pos)
        except Exception as e:
            print(f"Warning: Seek failed: {e}")

    def update(self):
        """Updates song position using high-precision monotonic clock with
        audio offset calibration and zero-jump smoothing.
        """
        if not self.is_playing or self.is_paused:
            return

        now = time.perf_counter()
        elapsed = max(0.0, now - self.start_time - self.total_paused_time)
        song_elapsed = self.audio_start_pos + (elapsed * self.time_multiplier)
        
        # Check Pygame mixer position to calibrate initial buffer delay
        raw_pos_ms = pygame.mixer.music.get_pos()
        if raw_pos_ms > 0 and not self.audio_synced:
            hardware_pos = self.audio_start_pos + (raw_pos_ms / 1000.0) * self.time_multiplier
            self.audio_sync_offset = song_elapsed - hardware_pos
            self.audio_synced = True

        # Apply calibrated audio offset + user custom audio offset setting
        user_offset_sec = GlobalState.audio_offset_ms / 1000.0
        calibrated_time = song_elapsed - self.audio_sync_offset + user_offset_sec
        
        self.song_position = max(0.0, calibrated_time)
        self.song_position_in_beats = self.song_position / self.sec_per_beat