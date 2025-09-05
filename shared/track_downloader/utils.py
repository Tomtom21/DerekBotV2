"""
For some of the assorted utils we might need
"""
from urllib.parse import urlparse, parse_qs
from difflib import SequenceMatcher

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
        "scheme": parsed.scheme,
        "parsed": parsed
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

def extract_spotify_resource_info(url):
    """
    Extracts the Spotify resource type and ID from a URL.

    :param url: The Spotify URL.
    :returns: A tuple containing the resource type and ID, or (None, None) if not found.
    """
    # Extracting the path segments from the URL
    parsed = parse_url_info(url)
    url_path = parsed["path"].strip("/").split("/")

    # Pulling the info if in the URL, otherwise return None, None
    if len(url_path) >= 2:
        resource_type = url_path[0]
        resource_id = url_path[1]
        return resource_type, resource_id
    return None, None

def get_text_similarity(a, b):
    """
    Determines the percentage similarity between two strings

    :param a: The first string
    :param b: The second string
    :return: The percentage similarity of the two strings
    """
    return SequenceMatcher(None, a, b).ratio()
