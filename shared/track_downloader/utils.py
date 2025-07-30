"""
For some of the assorted utils we might need
"""
from urllib.parse import urlparse, parse_qs


def parse_url_info(url):
    parsed = urlparse(url)
    return {
        "query": parse_qs(parsed.query),
        "path": parsed.path,
        "netloc": parsed.netloc,
        "scheme": parsed.scheme
    }


def extract_yt_playlist_id(url):
    return parse_url_info(url)["query"].get("list", [None])[0]


def extract_yt_video_id(url):
    return parse_url_info(url)["query"].get("v", [None])[0]
