from .errors import URLValidationError, URLClassificationError, MediaTypeMismatchError
from .utils import parse_url_info

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
        Determines whether a link is a track, playlist, or album. Provides a list of all detected types in the URL

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
                detected_types.add("track")
        elif source == "spotify":
            url_path = parsed_url["path"].strip("/").split("/")
            if len(url_path) >= 2:
                resource_type = url_path[0]
                if resource_type in {"track", "playlist", "album"}:
                    detected_types.add(resource_type)

        # Catching if we got a basic link with no information
        if not detected_types:
            raise URLClassificationError("Failed to detect any valid link types in the URL")

        return detected_types


class PlaylistItem:
    """
    Represents an item in a playlist, but not specifically a read-to-download track yet.
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


class SongRequest:
    """
    Represents a request for a song/track, including its URL and metadata.
    """
    def __init__(self, song_url):
        """
        Initializes a SongRequest.

        :param song_url: The URL of the song
        :raise MediaTypeMismatchError: If the media type is not a track
        """
        # Url info
        self.url = song_url
        self.title = None
        self.source = None
        self.media_type = None

        # These are for scoring of the request when necessary
        self.relevance_score = None
        self.source_publish_date = None
        self.content_duration = None

        # Verifying/Sanitizing the link, updating the source
        self.source = LinkValidator.validate_url(song_url)
        LinkValidator.sanitize_url(song_url)

        # Getting the media type
        media_type_list = LinkValidator.classify_link_type(self.source, song_url)
        if "song" in media_type_list:
            self.media_type = next(iter(media_type_list))
        else:
            raise MediaTypeMismatchError("The provided media type does not match what is required for the a track")
