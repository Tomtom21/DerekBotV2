import logging
from urllib.parse import urlunparse, urlencode

from shared.track_downloader.errors import URLValidationError, URLClassificationError, MediaTypeMismatchError, SpotifyListFetchError
from shared.track_downloader.utils import parse_url_info, extract_yt_playlist_id
from shared.spotify_api import SpotifyAPI
from shared.youtube_api import YoutubeAPI
from shared.constants import SPOTIFY_TRACK_URL_PREFIX, YOUTUBE_VIDEO_URL_PREFIX

class LinkValidator:
    """
    Provides utilities for validating, sanitizing, and classifying music/media URLs.
    """
    VALID_DOMAINS = {
        "youtube.com": "youtube",
        "youtu.be": "youtube",
        "open.spotify.com": "spotify"
    }
    SANITIZATION_MAX_LENGTH = 120

    @staticmethod
    def normalize_domain(domain):
        """
        Normalizes the domain by converting to lowercase and removing 'www.' prefix if present.

        :param domain: The domain string to normalize
        :return: Normalized domain string
        """
        domain = domain.lower()
        if domain.startswith("www."):
            return domain[4:]
        return domain

    @classmethod
    def validate_url(cls, url: str):
        """
        Checks to ensure that the user-provided URL is real and valid
        
        :raise URLValidationError: If the URL is not valid
        :return: The source for the URL
        """
        parsed = parse_url_info(url)

        # Checking if we have a https link. No http here
        if parsed["scheme"] not in {"https"}:
            raise URLValidationError("The provided URL does not use HTTPS")

        # Normalizing and checking the url domains
        normalized_domain = cls.normalize_domain(parsed["netloc"])
        if normalized_domain not in cls.VALID_DOMAINS.keys():
            raise URLValidationError("The URL domain is not valid")

        # It seems we have a valid domain, mark it
        return cls.VALID_DOMAINS[normalized_domain]

    @classmethod
    def sanitize_url(cls, url: str):
        """
        Sanitizes the URL

        :param url: The URL to sanitize
        :raise URLValidationError: If the URL is too long
        """
        if len(url) > cls.SANITIZATION_MAX_LENGTH:
            raise URLValidationError("The URL seems to be too long")

    @staticmethod
    def classify_link_type(source: str, url: str):
        """
        Determines whether a link is a song, playlist, or album. Provides a list of all detected types in the URL

        :param source: The source of the link, e.g. 'spotify' or 'youtube'
        :param url: The URL to classify
        :return: A list of all detected types in the URL
        :raise URLClassificationError: If no valid link types are detected
        """
        # Parsing the URL
        parsed_url = parse_url_info(url)
        detected_types = set()

        # Adding detected types based on what we find in the url
        if source == "youtube":
            if "list" in parsed_url["query"]:
                detected_types.add("playlist")

            if "v" in parsed_url["query"]:
                detected_types.add("song")
        elif source == "spotify":
            url_path = parsed_url["path"].strip("/").split("/")
            if len(url_path) >= 2:
                resource_type = url_path[0]
                # Accept "track" as "song" for Spotify
                if resource_type == "track":
                    detected_types.add("song")
                elif resource_type in {"song", "playlist", "album"}:
                    detected_types.add(resource_type)

        # Catching if we got a basic link with no information
        if not detected_types:
            raise URLClassificationError("Failed to detect any valid link types in the URL")

        return detected_types


class PlaylistItem:
    """
    Represents an item in a playlist, but not specifically a ready-to-download song yet.
    """
    def __init__(self, url=None, title=None, artist=None):
        """
        Initializes a PlaylistItem.

        :param url: The URL of the item
        :param title: The title of the item
        :param artist: The artist of the item
        """
        self.url = url
        self.title = title
        self.artist = artist

    def __str__(self):
        """
        Called when the object is printed to the console

        :return: The new format of the printed message
        """
        return (f"('url': {self.url}, "
                f"'title': {self.title}, "
                f"'artist': {self.artist})")


class PlaylistRequest:
    """
    Represents a request for a playlist, including its URL and items.
    """
    def __init__(self, playlist_url):
        """
        Initializes a PlaylistRequest.

        :param playlist_url: The URL of the playlist
        :raise MediaTypeMismatchError: If the media type is not a playlist or album
        """
        # Url info
        self.url = playlist_url
        self.title = None
        self.source = None
        self.media_type = None

        # Playlist info
        self.items: list[PlaylistItem] = []

        # Verifying/Sanitizing the link, updating the source
        self.source = LinkValidator.validate_url(playlist_url)
        LinkValidator.sanitize_url(playlist_url)

        # Getting the media type
        media_type_list = LinkValidator.classify_link_type(self.source, playlist_url)
        intersecting_types = {"playlist", "album"} & media_type_list
        if intersecting_types:
            self.media_type = next(iter(intersecting_types))
        else:
            raise MediaTypeMismatchError("The provided media type does not match what is required for a playlist")

    async def fetch_items(self, spotify_api: SpotifyAPI, youtube_api: YoutubeAPI):
        if self.source == "youtube":
            # Get playlist ID from URL
            playlist_id = extract_yt_playlist_id(self.url)
            if not playlist_id:
                return

            # Fetch playlist items using YouTube API
            results = youtube_api.youtube_api.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50
            ).execute()
            for item in results.get("items", []):
                video_id = item["snippet"]["resourceId"]["videoId"]
                title = item["snippet"]["title"]
                url = f"{YOUTUBE_VIDEO_URL_PREFIX}{video_id}"
                self.items.append(PlaylistItem(url=url, title=title))
        elif self.source == "spotify":
            # Get playlist or album ID from URL
            parsed = parse_url_info(self.url)
            url_path = parsed["path"].strip("/").split("/")
            resource_id = url_path[1] if len(url_path) > 1 else None
            logging.info(f"Resource ID: {resource_id}")
            if not resource_id:
                return

            if self.media_type == "playlist":
                try:
                    # Fetch playlist tracks
                    results = spotify_api.api_call(
                        endpoint_template="playlists/{playlist_id}/tracks",
                        placeholder_values={"playlist_id": resource_id},
                        limit=50
                    )
                except Exception as e:
                    logging.error(f"Error fetching Spotify playlist: {e}")
                    raise SpotifyListFetchError("Failed to fetch Spotify playlist") from e
                
                # Looping through and getting the data we need
                for item in results.get("items", []):
                    track = item.get("track")

                    # Skipping items if no track info
                    if not track:
                        continue

                    title = track.get("name")
                    artists = ", ".join(a["name"] for a in track.get("artists", []))
                    url = f"{SPOTIFY_TRACK_URL_PREFIX}{track.get('id')}"
                    self.items.append(PlaylistItem(url=url, title=title, artist=artists))
            elif self.media_type == "album":
                try:
                    # Fetch album tracks
                    results = spotify_api.api_call(
                        endpoint_template="albums/{album_id}/tracks",
                        placeholder_values={"album_id": resource_id},
                        limit=50
                    )
                except Exception as e:
                    logging.error(f"Error fetching Spotify album: {e}")
                    raise SpotifyListFetchError("Failed to fetch Spotify album") from e
                
                
                # Looping through and getting the data we need
                for track in results.get("items", []):
                    title = track.get("name")
                    artists = ", ".join(a["name"] for a in track.get("artists", []))
                    url = f"{SPOTIFY_TRACK_URL_PREFIX}{track.get('id')}"
                    self.items.append(PlaylistItem(url=url, title=title, artist=artists))


class SongRequest:
    """
    Represents a request for a song, including its URL and metadata.
    """
    def __init__(self, song_url):
        """
        Initializes a SongRequest.

        :param song_url: The URL of the song
        :raise MediaTypeMismatchError: If the media type is not a song
        """
        # Content info
        self.url = song_url
        self.title = None
        self.source = None
        self.media_type = None

        # These are for scoring of the request when necessary
        self.relevance_score = None
        self.source_publish_date = None
        self.content_duration = None

        # The file path to the downloaded song, if downloaded
        self.file_path = None

        # Verifying/Sanitizing the link, updating the source
        self.source = LinkValidator.validate_url(song_url)
        LinkValidator.sanitize_url(song_url)

        # Getting the media type
        media_type_list = LinkValidator.classify_link_type(self.source, song_url)
        if "song" in media_type_list:
            self.media_type = "song"  # Always set to "song" if present

            # Clean &list= from YouTube URLs if both song and playlist detected
            if "playlist" in media_type_list and self.source == "youtube":
                parsed = parse_url_info(song_url)
                
                if "list" in parsed["query"]:
                    parsed["query"].pop("list")
                    new_query = urlencode(parsed["query"], doseq=True)
                    cleaned_url = urlunparse(parsed["parsed"]._replace(query=new_query))
                    self.url = cleaned_url
        else:
            raise MediaTypeMismatchError(
                "The provided media type does not match what is required for a song"
            )
