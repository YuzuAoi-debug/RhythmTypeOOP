import os
from typing import List, Dict, Any, Optional

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
        """Extracts title, artist, version, audio filename, bpm, and background image if present."""
        metadata = {
            "title": "",
            "artist": "",
            "version": "",
            "background": "",
            "audio_filename": "",
            "bpm": 130.0,
            "note_count": 0
        }
        if not os.path.exists(file_path):
            return metadata

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                current_section = ""
                hit_count = 0
                found_bpm = False
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("[") and line.endswith("]"):
                        current_section = line
                        continue

                    if current_section == "[General]":
                        if line.startswith("AudioFilename:"):
                            metadata["audio_filename"] = line.split("AudioFilename:", 1)[1].strip()
                    elif current_section == "[Metadata]":
                        if line.startswith("Title:"):
                            metadata["title"] = line.split("Title:", 1)[1].strip()
                        elif line.startswith("Artist:"):
                            metadata["artist"] = line.split("Artist:", 1)[1].strip()
                        elif line.startswith("Version:"):
                            metadata["version"] = line.split("Version:", 1)[1].strip()
                    elif current_section == "[TimingPoints]" and not found_bpm:
                        # Format: time,beatLength,meter,sampleSet,sampleIndex,volume,uninherited,effects
                        parts = line.split(",")
                        if len(parts) >= 2:
                            try:
                                beat_length = float(parts[1])
                                is_uninherited = True
                                if len(parts) >= 7:
                                    is_uninherited = (parts[6].strip() == "1")
                                if is_uninherited and beat_length > 0:
                                    metadata["bpm"] = round(60000.0 / beat_length, 1)
                                    found_bpm = True
                            except ValueError:
                                pass
                    elif current_section == "[Events]":
                        # Video or Background: 0,0,"bg.jpg",0,0
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

    @staticmethod
    def scan_song_directory(song_dir: str) -> Optional[Dict[str, Any]]:
        """Scans a single directory for .osu or .txt beatmap charts, audio, and background art."""
        if not os.path.isdir(song_dir):
            return None

        osu_files = []
        audio_files = []
        image_files = []

        for entry in os.listdir(song_dir):
            full_path = os.path.join(song_dir, entry)
            if not os.path.isfile(full_path):
                continue
            lower = entry.lower()
            if lower.endswith((".osu", ".txt")) and not lower.endswith(".import"):
                osu_files.append(full_path)
            elif lower.endswith((".mp3", ".ogg", ".wav")) and not lower.endswith(".import"):
                audio_files.append(full_path)
            elif lower.endswith((".jpg", ".jpeg", ".png")) and not lower.endswith(".import"):
                image_files.append(full_path)

        if not osu_files:
            return None

        difficulties = []
        main_title = ""
        main_artist = ""
        expected_audio = ""
        expected_bg = ""
        bpm = 130.0

        for osu_path in osu_files:
            meta = BeatmapParser.get_beatmap_metadata(osu_path)
            if meta["note_count"] > 0 or len(osu_files) == 1:
                diff_name = meta["version"] or os.path.splitext(os.path.basename(osu_path))[0]
                difficulties.append({
                    "name": diff_name,
                    "osu_path": osu_path,
                    "note_count": meta["note_count"]
                })
                if not main_title and meta["title"]:
                    main_title = meta["title"]
                if not main_artist and meta["artist"]:
                    main_artist = meta["artist"]
                if not expected_audio and meta["audio_filename"]:
                    expected_audio = meta["audio_filename"]
                if not expected_bg and meta["background"]:
                    expected_bg = meta["background"]
                if meta.get("bpm") and meta["bpm"] > 0:
                    bpm = meta["bpm"]

        if not difficulties:
            return None

        # Resolve Audio Path
        audio_path = ""
        if expected_audio:
            candidate = os.path.join(song_dir, expected_audio)
            if os.path.exists(candidate):
                audio_path = candidate
        if not audio_path and audio_files:
            audio_path = audio_files[0]

        # Resolve Background Path
        bg_path = ""
        if expected_bg:
            candidate = os.path.join(song_dir, expected_bg)
            if os.path.exists(candidate):
                bg_path = candidate
        if not bg_path and image_files:
            bg_path = image_files[0]

        # Title Formatting
        if not main_title:
            main_title = os.path.basename(song_dir)
        full_title = f"{main_artist} - {main_title}" if (main_artist and main_artist not in main_title) else main_title

        return {
            "title": full_title,
            "artist": main_artist or "Unknown Artist",
            "audio_path": audio_path,
            "background_path": bg_path,
            "bpm": bpm,
            "difficulties": difficulties,
            "folder_path": song_dir
        }