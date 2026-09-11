import os

class BeatmapParser:
    @staticmethod
    def load_osu_beatmap(file_path: str) -> list:
        hit_times = []
        if not os.path.exists(file_path):
            print(f"Warning: Beatmap not found at {file_path}. Generating dummy notes.")
            # Fallback dummy notes every 0.6 seconds if file is missing
            return [i * 0.6 for i in range(50)]

        with open(file_path, 'r', encoding='utf-8') as f:
            reading_hit_objects = False
            for line in f:
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                if line == "[HitObjects]":
                    reading_hit_objects = True
                    continue
                if line.startswith("[") and line != "[HitObjects]":
                    reading_hit_objects = False
                
                if reading_hit_objects:
                    tokens = line.split(",")
                    if len(tokens) >= 3:
                        time_in_ms = float(tokens[2])
                        hit_times.append(time_in_ms / 1000.0)
                        
        return hit_times