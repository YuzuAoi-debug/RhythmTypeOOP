import pygame

class Conductor:
    def __init__(self, bpm: float = 120.0):
        self.bpm = bpm
        self.sec_per_beat = 60.0 / bpm
        self.song_position = 0.0
        self.song_position_in_beats = 0.0
        self.start_ticks = 0
        self.is_playing = False

    def start_song(self):
        self.start_ticks = pygame.time.get_ticks()
        self.is_playing = True
        try:
            pygame.mixer.music.play()
        except pygame.error:
            print("Warning: No audio loaded to play.")

    def update(self):
        if not self.is_playing:
            return
            
        # Calculate precise song position in seconds from pygame mixer playback time
        raw_pos = pygame.mixer.music.get_pos() / 1000.0
        
        if raw_pos < 0:
            # Fallback to system timer delta if mixer position is uninitialized
            self.song_position = (pygame.time.get_ticks() - self.start_ticks) / 1000.0
        else:
            self.song_position = raw_pos
            
        self.song_position_in_beats = self.song_position / self.sec_per_beat