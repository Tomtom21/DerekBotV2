import logging
from difflib import SequenceMatcher


class SongDownloader:
    def __init__(self, output_dir="."):
        self.output_dir = output_dir

    @staticmethod
    def get_text_similarity(a, b):
        """Determines the percentage similarity between two strings"""
        return SequenceMatcher(None, a, b).ratio()

    def download_song(self, song_url):
        pass

    def download_playlist(self, playlist_url):
        pass

    def _download_youtube_song(self, youtube_song_url):
        pass

    def _download_spotify_song(self, spotify_song_url):
        pass


