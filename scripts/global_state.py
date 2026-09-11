class GlobalState:
    menu_volume: float = 1.0
    game_volume: float = 1.0
    note_speed: float = 9.0
    hp: float = 100.0
    fps_mode: str = "refresh_rate" # "unlimited", "60fps", "refresh_rate"
    
    # Payload for the active song to play
    selected_song_data = {}
    
    # Master Song Library Database
    song_list = [
        {
            "title": "Fennel - confess",
            "audio_path": "assets/audio/music/fennel_confess/audio.mp3",
            "difficulties": [
                {"name": "Normal", "osu_path": "assets/audio/music/fennel_confess/normal.txt"},
                {"name": "Hard", "osu_path": "assets/audio/music/fennel_confess/hard.txt"},
                {"name": "Insane", "osu_path": "assets/audio/music/fennel_confess/insane.txt"}
            ]
        },
        {
            "title": "Hoshimachi Suisei - Moonshot",
            "audio_path": "assets/audio/music/moonshot/audio.ogg",
            "difficulties": [
                {"name": "Normal", "osu_path": "assets/audio/music/moonshot/Hoshimachi Suisei - Moonshot [Normal].txt"},
                {"name": "Hard", "osu_path": "assets/audio/music/moonshot/Hoshimachi Suisei - Moonshot [Hard].txt"},
                {"name": "Insane", "osu_path": "assets/audio/music/moonshot/Hoshimachi Suisei - Moonshot [Insane].txt"}
            ]
        }
    ]