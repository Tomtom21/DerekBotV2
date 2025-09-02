"""
A collection of potential errors that we can pass back to bot so it is aware of an issues and what to report to the user
"""

class URLValidationError(Exception):
    pass


class URLSanitizationError(Exception):
    pass


# class SongRouterError(Exception):
#     pass


class DownloadError(Exception):
    pass


class YouTubeSearchError(Exception):
    pass


class AudioProcessingError(Exception):
    pass


class URLClassificationError(Exception):
    pass


class MediaTypeMismatchError(Exception):
    pass


class MediaSourceMismatchError(Exception):
    pass

class SpotifyAPIError(Exception):
    pass

class SpotifyListFetchError(Exception):
    pass

class YoutubePlaylistFetchError(Exception):
    pass
