from urllib.parse import urlparse, parse_qs


def parse_url_info(url):
    parsed = urlparse(url)
    return {
        "query": parse_qs(parsed.query),
        "path": parsed.path,
        "netloc": parsed.netloc,
        "scheme": parsed.scheme
    }
