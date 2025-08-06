from shared.spotify_api import SpotifyAPI
from shared.youtube_api import YoutubeAPI
from song_downloader import SongDownloader

class PlaylistDownloader:
    def __init__(self, spotify_api: SpotifyAPI, youtube_api: YoutubeAPI, song_downloader: SongDownloader):
        self.song_downloader = song_downloader

    async def download_playlist_by_url(self, playlist_url, callback_func, **kwargs):
        """
        User-callable function that downloads a playlist using a URL
        
        :param playlist_url: The playlist url
        :param callback_func: The callback function to call when each song is downloaded successfully
        :param kwargs: Additional keyword arguments
        """

    def _route_playlist_download(self, playlist_url, callback_func, **kwargs):
        """
        Routes a playlist url to one of the playlist downloading methods, calls callback for each download

        :param playlist_url: The playlist url
        :param callback: The callback function to call when each song is downloaded successfully
        :param kwargs: Additional keyword arguments
        :return:
        """
        pass

    def _download_spotify_playlist(self, spotify_playlist_url, callback_func, **kwargs):
        """
        Downloads a Spotify playlist, calls callback

        :param spotify_playlist_url: The Spotify playlist url
        :param callback: The callback function to call when each song is downloaded successfully
        :param kwargs: Additional keyword arguments
        :return:
        """
        # Ensuring we're authed. We auth each call to

        # This needs to accept a list of song requests??
        # essentially we need the list of songs to be pulled first

        pass

    def _download_youtube_playlist(self, youtube_playlist_url, callback_func, **kwargs):
        """
        Downloads a YouTube playlist, calls callback

        :param youtube_playlist_url: The YouTube playlist url
        :param callback: The callback function to call when the song is downloaded
        :param kwargs: Additional keyword arguments
        :return:
        """
        pass
