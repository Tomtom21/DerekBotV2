"""
For some of the assorted utils we might need
"""
from urllib.parse import urlparse, parse_qs


def parse_url_info(url):
    """
    Parses a URL and returns its components.

    :param url: The URL to parse.
    :returns: Dictionary containing 'query', 'path', 'netloc', and 'scheme'.
    """
    parsed = urlparse(url)
    return {
        "query": parse_qs(parsed.query),
        "path": parsed.path,
        "netloc": parsed.netloc,
        "scheme": parsed.scheme
    }


def extract_yt_playlist_id(url):
    """
    Extracts the YouTube playlist ID from a URL.

    :param url: The YouTube URL.
    :returns: The playlist ID if present, otherwise None.
    """
    return parse_url_info(url)["query"].get("list", [None])[0]


def extract_yt_video_id(url):
    """
    Extracts the YouTube video ID from a URL.

    :param url: The YouTube URL.
    :returns: The video ID if present, otherwise None.
    """
    return parse_url_info(url)["query"].get("v", [None])[0]
