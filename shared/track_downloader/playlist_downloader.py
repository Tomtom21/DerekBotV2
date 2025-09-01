from shared.spotify_api import SpotifyAPI
from shared.youtube_api import YoutubeAPI
from shared.track_downloader.song_downloader import SongDownloader

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
        pass
