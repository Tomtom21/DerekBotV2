class PlaylistDownloader:
    def __init__(self, spotify_api, youtube_api, song_downloader):
        self.song_downloader = song_downloader

    def _route_playlist_download(self, playlist_url, callback):
        """
        Routes a playlist url to one of the playlist downloading methods, calls callback for each download

        :param playlist_url: The playlist url
        :param callback: The callback function to call when each song is downloaded successfully
        :return:
        """
        pass

    def _download_spotify_playlist(self, spotify_playlist_url, callback):
        """
        Downloads a Spotify playlist, calls callback

        :param spotify_playlist_url: The Spotify playlist url
        :param callback: The callback function to call when each song is downloaded successfully
        :return:
        """
        # Ensuring we're authed. We auth each call to

        # This needs to accept a list of song requests??
        # essentially we need the list of songs to be pulled first

        pass

    def _download_youtube_playlist(self, youtube_playlist_url, callback):
        """
        Downloads a YouTube playlist, calls callback

        :param youtube_playlist_url: The YouTube playlist url
        :param callback: The callback function to call when the song is downloaded
        :return:
        """
        pass
