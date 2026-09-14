import os
from typing import List, Dict, Any

class BeatmapParser:
    @staticmethod
    def load_osu_beatmap(file_path: str) -> List[float]:
        """Loads hit object timestamps from an osu! beatmap file in seconds."""
        hit_times = []
        if not os.path.exists(file_path):
            print(f"Warning: Beatmap not found at {file_path}. Generating dummy notes.")
            return [1.0 + i * 0.6 for i in range(50)]

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
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
                            try:
                                time_in_ms = float(tokens[2])
                                hit_times.append(time_in_ms / 1000.0)
                            except (ValueError, IndexError):
                                continue
        except Exception as e:
            print(f"Error reading beatmap file {file_path}: {e}")
            return [1.0 + i * 0.6 for i in range(50)]

        # Ensure timestamps are strictly sorted
        hit_times.sort()
        return hit_times

    @staticmethod
    def get_beatmap_metadata(file_path: str) -> Dict[str, Any]:
        """Extracts title, artist, version, and background image if present."""
        metadata = {
            "title": "",
            "artist": "",
            "version": "",
            "background": "",
            "note_count": 0
        }
        if not os.path.exists(file_path):
            return metadata

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                current_section = ""
                hit_count = 0
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("[") and line.endswith("]"):
                        current_section = line
                        continue

                    if current_section == "[Metadata]":
                        if line.startswith("Title:"):
                            metadata["title"] = line.split("Title:", 1)[1].strip()
                        elif line.startswith("Artist:"):
                            metadata["artist"] = line.split("Artist:", 1)[1].strip()
                        elif line.startswith("Version:"):
                            metadata["version"] = line.split("Version:", 1)[1].strip()
                    elif current_section == "[Events]":
                        # 0,0,"bg.jpg",0,0
                        if line.startswith("0,0,"):
                            parts = line.split(",")
                            if len(parts) >= 3:
                                bg = parts[2].strip().strip('"')
                                if bg:
                                    metadata["background"] = bg
                    elif current_section == "[HitObjects]":
                        if not line.startswith("//"):
                            hit_count += 1

                metadata["note_count"] = hit_count
        except Exception:
            pass

        return metadata