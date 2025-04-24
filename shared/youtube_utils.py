from urllib.parse import urlparse, parse_qs


def _extract_yt_url_query_params(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params


def extract_yt_playlist_id(url):
    query_params = _extract_yt_url_query_params(url)
    return query_params.get("list", [None])[0]


def extract_yt_video_id(url):
    query_params = _extract_yt_url_query_params(url)
    return query_params.get("v", [None])[0]
