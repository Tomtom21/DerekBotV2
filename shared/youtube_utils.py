from url_utils import parse_url_info


def extract_yt_playlist_id(url):
    return parse_url_info(url).get("list", [None])[0]


def extract_yt_video_id(url):
    return parse_url_info(url).get("v", [None])[0]
