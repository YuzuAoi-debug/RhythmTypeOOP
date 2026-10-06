import random
import urllib.request
import json
import re

API_WORD_URL = "https://api.datamuse.com/words"
EMERGENCY_FALLBACK_WORDS = ["ALPHA", "BETA", "GAMMA", "DELTA", "EPSILON", "ZETA", "THETA", "IOTA"]
COMMON_WORDS = {
    "ALPHA", "APPLE", "BETA", "BLOOM", "BREAD", "BRAVE", "BRIGHT", "COOL",
    "DELTA", "EARTH", "FLAME", "GAMMA", "GHOST", "GLOW", "GRACE", "HELLO",
    "LIGHT", "MUSIC", "PLANE", "SHINE", "SMILE", "SOLAR", "SOUND", "SPACE",
    "SPARK", "STONE", "STREAM", "TREE", "UNITY", "VIBES", "WATER", "WAVES",
    "WORLD", "ZEBRA"
}


class WordGenerator:
    """Provides gameplay words sourced from the dictionary API with a minimal fallback."""

    _cached_api_words = []

    @staticmethod
    def _is_game_friendly_word(word: str) -> bool:
        if len(word) < 3 or len(word) > 6 or not re.fullmatch(r"[A-Z]+", word):
            return False
        if word in COMMON_WORDS:
            return True
        vowel_count = sum(ch in "AEIOU" for ch in word)
        if vowel_count == 0:
            return False
        return not word.endswith(("X", "Q", "JZ"))

    @classmethod
    def fetch_api_words(cls, count: int = 40, max_len: int = 6) -> list:
        if cls._cached_api_words:
            return cls._cached_api_words[:count]

        candidates = []
        seen = set()

        try:
            for length in range(3, max_len + 1):
                url = f"{API_WORD_URL}?sp={'?' * length}&md=f&max=200"
                with urllib.request.urlopen(url, timeout=4) as response:
                    payload = json.loads(response.read().decode("utf-8"))

                for entry in payload:
                    if not isinstance(entry, dict):
                        continue
                    word = str(entry.get("word", "")).upper()
                    if not cls._is_game_friendly_word(word):
                        continue
                    score = entry.get("score")
                    if isinstance(score, (int, float)) and score < 1000 and word not in COMMON_WORDS:
                        continue
                    if word in seen:
                        continue
                    seen.add(word)
                    candidates.append(word)
        except Exception:
            candidates = []

        if not candidates:
            cls._cached_api_words = EMERGENCY_FALLBACK_WORDS[:count]
            return cls._cached_api_words

        if len(candidates) > count:
            random.shuffle(candidates)
            cls._cached_api_words = candidates[:count]
        else:
            cls._cached_api_words = candidates

        return cls._cached_api_words

    @classmethod
    def get_word_sequence(cls, total_notes: int) -> list:
        """Generates a non-repeating sequence of easy 3-6 letter words whose
        cumulative character count meets or exceeds total_notes.
        """
        if total_notes <= 0:
            return ["START"]

        api_words = cls.fetch_api_words(count=40, max_len=6)
        combined_pool = list(dict.fromkeys(api_words + EMERGENCY_FALLBACK_WORDS))
        random.shuffle(combined_pool)

        sequence = []
        char_count = 0
        pool_index = 0

        while char_count < total_notes:
            remaining = total_notes - char_count
            if pool_index >= len(combined_pool):
                random.shuffle(combined_pool)
                if sequence and combined_pool[0] == sequence[-1] and len(combined_pool) > 1:
                    combined_pool[0], combined_pool[1] = combined_pool[1], combined_pool[0]
                pool_index = 0

            if 3 <= remaining <= 6:
                exact_matches = [w for w in combined_pool if len(w) == remaining and (not sequence or w != sequence[-1])]
                if exact_matches:
                    chosen_word = random.choice(exact_matches)
                    sequence.append(chosen_word)
                    char_count += len(chosen_word)
                    break

            chosen_word = combined_pool[pool_index]
            pool_index += 1
            sequence.append(chosen_word)
            char_count += len(chosen_word)

        return sequence
