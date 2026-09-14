import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any

from global_state import GlobalState
from beatmap_parser import BeatmapParser

class BeatmapImporter:
    @staticmethod
    def sanitize_name(name: str) -> str:
        """Removes characters invalid in Windows directory names."""
        clean = re.sub(r'[\\/*?:"<>|]', "", name).strip()
        # Collapse multiple spaces or dashes
        clean = re.sub(r'\s+', ' ', clean)
        return clean or "imported_song"

    @classmethod
    def import_osz(cls, osz_path: str) -> Optional[Dict[str, Any]]:
        """Imports an .osz (or .zip) osu! beatmap package into the music library."""
        if not os.path.exists(osz_path):
            print(f"Error: File not found: {osz_path}")
            return None

        if not zipfile.is_zipfile(osz_path):
            print(f"Error: {osz_path} is not a valid zip / osz archive.")
            return None

        try:
            with zipfile.ZipFile(osz_path, 'r') as archive:
                namelist = archive.namelist()
                osu_members = [n for n in namelist if n.lower().endswith((".osu", ".txt"))]
                
                detected_title = ""
                detected_artist = ""
                
                # Inspect internal .osu files to find proper Title & Artist
                for osu_name in osu_members:
                    try:
                        with archive.open(osu_name) as f:
                            content = f.read().decode('utf-8', errors='replace')
                            for line in content.splitlines():
                                line = line.strip()
                                if line.startswith("Title:"):
                                    detected_title = line.split("Title:", 1)[1].strip()
                                elif line.startswith("Artist:"):
                                    detected_artist = line.split("Artist:", 1)[1].strip()
                                if detected_title and detected_artist:
                                    break
                    except Exception:
                        pass
                    if detected_title:
                        break

                # Fallback to filename if metadata wasn't detected
                if not detected_title:
                    base_name = os.path.splitext(os.path.basename(osz_path))[0]
                    detected_title = base_name

                folder_candidate = f"{detected_artist} - {detected_title}" if (detected_artist and detected_artist not in detected_title) else detected_title
                folder_name = cls.sanitize_name(folder_candidate)

                target_dir = GlobalState.MUSIC_DIR / folder_name
                target_dir.mkdir(parents=True, exist_ok=True)

                # Extract all files
                archive.extractall(target_dir)
                print(f"Successfully extracted beatmap to {target_dir}")

                # Rescan song library to pick up the new map
                GlobalState.scan_songs()

                # Find the imported song in the active library
                resolved_target_dir = str(target_dir.resolve())
                for idx, song in enumerate(GlobalState.song_list):
                    if os.path.abspath(song.get("folder_path", "")) == resolved_target_dir:
                        GlobalState.selected_song_index = idx
                        GlobalState.expanded_song_index = idx
                        return song

                # If exact folder match didn't trigger, select last song in list
                if GlobalState.song_list:
                    idx = len(GlobalState.song_list) - 1
                    GlobalState.selected_song_index = idx
                    GlobalState.expanded_song_index = idx
                    return GlobalState.song_list[idx]

        except Exception as e:
            print(f"Error importing osz archive: {e}")

        return None

    @classmethod
    def import_osu(cls, osu_path: str) -> Optional[Dict[str, Any]]:
        """Imports an individual .osu beatmap file and its associated media."""
        if not os.path.exists(osu_path):
            print(f"Error: File not found: {osu_path}")
            return None

        src_dir = os.path.dirname(os.path.abspath(osu_path))
        music_root = str(GlobalState.MUSIC_DIR.resolve())

        # If already located inside the music folder, simply rescan
        if os.path.abspath(src_dir).startswith(music_root):
            GlobalState.scan_songs()
            for idx, song in enumerate(GlobalState.song_list):
                if os.path.abspath(song.get("folder_path", "")) == os.path.abspath(src_dir):
                    GlobalState.selected_song_index = idx
                    GlobalState.expanded_song_index = idx
                    return song

        # Otherwise copy chart and media to assets/audio/music/
        try:
            meta = BeatmapParser.get_beatmap_metadata(osu_path)
            title = meta.get("title") or os.path.splitext(os.path.basename(osu_path))[0]
            artist = meta.get("artist") or ""
            folder_candidate = f"{artist} - {title}" if (artist and artist not in title) else title
            folder_name = cls.sanitize_name(folder_candidate)

            target_dir = GlobalState.MUSIC_DIR / folder_name
            target_dir.mkdir(parents=True, exist_ok=True)

            dest_osu = target_dir / os.path.basename(osu_path)
            shutil.copy2(osu_path, dest_osu)

            # Copy audio file if present in the source folder
            if meta.get("audio_filename"):
                src_audio = os.path.join(src_dir, meta["audio_filename"])
                if os.path.exists(src_audio):
                    shutil.copy2(src_audio, target_dir / meta["audio_filename"])

            # Copy background if present
            if meta.get("background"):
                src_bg = os.path.join(src_dir, meta["background"])
                if os.path.exists(src_bg):
                    shutil.copy2(src_bg, target_dir / meta["background"])

            GlobalState.scan_songs()

            resolved_target = str(target_dir.resolve())
            for idx, song in enumerate(GlobalState.song_list):
                if os.path.abspath(song.get("folder_path", "")) == resolved_target:
                    GlobalState.selected_song_index = idx
                    GlobalState.expanded_song_index = idx
                    return song

        except Exception as e:
            print(f"Error importing .osu file: {e}")

        return None

    @classmethod
    def import_file(cls, file_path: str) -> Optional[Dict[str, Any]]:
        """Determines file type and routes to appropriate import handler."""
        if not file_path or not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return None

        lower = file_path.lower()
        if lower.endswith((".osz", ".zip")):
            return cls.import_osz(file_path)
        elif lower.endswith((".osu", ".txt")):
            return cls.import_osu(file_path)
        elif lower.endswith(".osr"):
            print("Notice: .osr is an osu! replay file containing user input data, not a beatmap.")
            print("Please open or drag in a .osz beatmap package to import a new song.")
            return None
        else:
            print(f"Unsupported file format: {file_path}")
            return None
