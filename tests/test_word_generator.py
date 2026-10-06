import unittest
from unittest.mock import patch

from scripts.word_generator import WordGenerator


class WordGeneratorApiTests(unittest.TestCase):
    def setUp(self):
        WordGenerator._cached_api_words = []

    @patch("scripts.word_generator.urllib.request.urlopen")
    def test_fetch_api_words_uses_dictionary_api_data(self, mock_urlopen):
        class DummyResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b'[{"word": "apple", "score": 3000}, {"word": "plane", "score": 2400}, {"word": "tree", "score": 2600}, {"word": "zebra", "score": 1200}, {"word": "moxie", "score": 10}]'

        mock_urlopen.return_value = DummyResponse()

        words = WordGenerator.fetch_api_words(count=4, max_len=5)

        self.assertTrue(len(words) == 4)
        self.assertTrue(set(words).issubset({"APPLE", "PLANE", "TREE", "ZEBRA"}))
        self.assertTrue(all(len(word) >= 3 and len(word) <= 5 for word in words))

    def test_get_word_sequence_uses_api_words_when_available(self):
        WordGenerator._cached_api_words = ["alpha", "bravo", "charlie", "delta"]

        words = WordGenerator.get_word_sequence(10)

        self.assertTrue(len(words) > 0)
        self.assertTrue(all(len(word) >= 3 and len(word) <= 6 for word in words))


if __name__ == "__main__":
    unittest.main()
