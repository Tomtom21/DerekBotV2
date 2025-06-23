import aiohttp
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup


SHORT_TERM_OUTLOOKS = {
    1: ("https://www.spc.noaa.gov/products/outlook/day1otlk.html", "https://www.spc.noaa.gov/products/outlook/day1otlk_1200.gif"),
    2: ("https://www.spc.noaa.gov/products/outlook/day2otlk.html", "https://www.spc.noaa.gov/products/outlook/day2otlk_0600.gif"),
    3: ("https://www.spc.noaa.gov/products/outlook/day3otlk.html", "https://www.spc.noaa.gov/products/outlook/day3otlk_1930.gif")
}
LONGER_TERM_OUTLOOK = ("https://www.spc.noaa.gov/products/exper/day4-8/", "https://www.spc.noaa.gov/products/exper/day4-8/day48prob.gif")

async def fetch_spc_outlook_text(outlook_url):
    """
    Fetches the SPC outlook text from the provided URL.

    :param outlook_url: The URL of the SPC outlook page to fetch
    :return: Tuple containing the outlook text (or error message) and None
    """
    async with aiohttp.ClientSession() as session:
        # Fetch the outlook HTML
        async with session.get(outlook_url) as resp:
            if resp.status != 200:
                return "Failed to retrieve SPC outlook text.", None
            html = await resp.text()

        # Parse the outlook text from the HTML
        soup = BeautifulSoup(html, "html.parser")
        
        # Try to find the main outlook text (inside <pre> or <textarea>)
        outlook_text = None
        pre = soup.find("pre")
        if pre:
            outlook_text = pre.get_text(strip=True)
        else:
            textarea = soup.find("textarea")
            if textarea:
                outlook_text = textarea.get_text(strip=True)
        if not outlook_text:
            outlook_text = "SPC outlook text not found."

    return outlook_text, None

async def fetch_spc_outlook_image(image_url):
    """
    Fetches the SPC outlook image from the provided image URL.

    :param image_url: The URL of the SPC outlook image to fetch
    :return: Tuple containing a status message and the PIL.Image object (or None if retrieval failed)
    """
    async with aiohttp.ClientSession() as session:
        # Fetch the outlook image
        async with session.get(image_url) as img_resp:
            if img_resp.status != 200:
                return "Failed to retrieve the SPC outlook image", None
            img_bytes = await img_resp.read()
            try:
                image = Image.open(BytesIO(img_bytes))
                return "Successfully fetched the SPC outlook image", image
            except Exception:
                return "Failed to process the SPC outlook image", None

async def get_spc_outlook_text(day: int):
    """
    Retrieves the SPC outlook text for the requested day.

    :param day: The day for which to retrieve the outlook text (1, 2, 3 for short-term, 4-8 for longer-term)
    :return: Tuple containing the outlook text (or error message) and None
    """
    if day in SHORT_TERM_OUTLOOKS:
        outlook_url, _ = SHORT_TERM_OUTLOOKS[day]
    elif 4 <= day <= 8:
        outlook_url, _ = LONGER_TERM_OUTLOOK
    else:
        return "Unable to get an outlook for that date range.", None
    
    return await fetch_spc_outlook_text(outlook_url)

async def get_spc_outlook_image(day: int):
    """
    Retrieves the SPC outlook image for the requested day.

    :param day: The day for which to retrieve the outlook image (1, 2, 3 for short-term, 4-8 for longer-term)
    :return: Tuple containing a status message and the PIL.Image object (or None if retrieval failed)
    """
    if day in SHORT_TERM_OUTLOOKS:
        _, image_url = SHORT_TERM_OUTLOOKS[day]
    elif 4 <= day <= 8:
        _, image_url = LONGER_TERM_OUTLOOK
    else:
        return "Unable to get an outlook image for that date range.", None
    
    return await fetch_spc_outlook_image(image_url)
