import aiohttp
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
import logging

SHORT_TERM_OUTLOOKS = {
    1: ("https://www.spc.noaa.gov/products/outlook/day1otlk.html", "https://www.spc.noaa.gov/products/outlook/day1otlk_1200.gif"),
    2: ("https://www.spc.noaa.gov/products/outlook/day2otlk.html", "https://www.spc.noaa.gov/products/outlook/day2otlk_0600.gif"),
    3: ("https://www.spc.noaa.gov/products/outlook/day3otlk.html", "https://www.spc.noaa.gov/products/outlook/day3otlk_1930.gif")
}
LONGER_TERM_OUTLOOK = ("https://www.spc.noaa.gov/products/exper/day4-8/", "https://www.spc.noaa.gov/products/exper/day4-8/day48prob.gif")

async def _fetch_spc_outlook_text(outlook_url):
    """
    Fetches the SPC outlook text from the provided URL.

    :param outlook_url: The URL of the SPC outlook page to fetch
    :return: Tuple containing the outlook text (or error message) and None
    """
    async with aiohttp.ClientSession() as session:
        # Fetch the outlook HTML
        async with session.get(outlook_url) as resp:
            if resp.status != 200:
                logging.error(f"Failed to retrieve SPC outlook text. Status: {resp.status}")
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
            logging.error("SPC outlook text not found in HTML.")
            outlook_text = "SPC outlook text not found."

    return outlook_text, None

async def _fetch_spc_outlook_image(image_url):
    """
    Fetches the SPC outlook image from the provided image URL.

    :param image_url: The URL of the SPC outlook image to fetch
    :return: Tuple containing a status message and the PIL.Image object (or None if retrieval failed)
    """
    async with aiohttp.ClientSession() as session:
        # Fetch the outlook image
        async with session.get(image_url) as img_resp:
            if img_resp.status != 200:
                logging.error(f"Failed to retrieve the SPC outlook image. Status: {img_resp.status}")
                return "Failed to retrieve the SPC outlook image", None
            img_bytes = await img_resp.read()
            try:
                image = Image.open(BytesIO(img_bytes))
                return "Successfully fetched the SPC outlook image", image
            except Exception as e:
                logging.error(f"Failed to process the SPC outlook image: {e}")
                return "Failed to process the SPC outlook image", None

async def get_spc_outlook_text(day: int):
    """
    Retrieves the SPC outlook text for the requested day.

    :param day: The day for which to retrieve the outlook text (1, 2, 3 for short-term, 4-8 for longer-term)
    :return: Tuple containing the outlook text (or error message) and None
    """
    logging.info(f"Running get_spc_outlook_text tool function for day {day}")
    if day in SHORT_TERM_OUTLOOKS:
        outlook_url, _ = SHORT_TERM_OUTLOOKS[day]
    elif 4 <= day <= 8:
        outlook_url, _ = LONGER_TERM_OUTLOOK
    else:
        logging.error(f"Invalid day value for SPC outlook text: {day}")
        return "Unable to get an outlook for that date range.", None
    
    return await _fetch_spc_outlook_text(outlook_url)

async def get_spc_outlook_image(day: int):
    """
    Retrieves the SPC outlook image for the requested day.

    :param day: The day for which to retrieve the outlook image (1, 2, 3 for short-term, 4-8 for longer-term)
    :return: Tuple containing a status message and the PIL.Image object (or None if retrieval failed)
    """
    logging.info(f"Running get_spc_outlook_image tool function for day {day}")
    if day in SHORT_TERM_OUTLOOKS:
        _, image_url = SHORT_TERM_OUTLOOKS[day]
    elif 4 <= day <= 8:
        _, image_url = LONGER_TERM_OUTLOOK
    else:
        logging.error(f"Invalid day value for SPC outlook image: {day}")
        return "Unable to get an outlook image for that date range.", None
    
    return await _fetch_spc_outlook_image(image_url)

async def get_local_forecast(lat: float, lon: float):
    """
    Retrieves the local weather forecast for the specified latitude and longitude.

    :param lat: Latitude of the location
    :param lon: Longitude of the location
    :return: String containing the detailed local weather forecast or an error message
    """
    logging.info(f"Running get_local_forecast tool function for lat={lat}, lon={lon}")
    url = f"https://forecast.weather.gov/MapClick.php?lat={lat}&lon={lon}&FcstType=text"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                logging.error(f"Error fetching forecast data. Status: {response.status}")
                return "Error fetching forecast data.", None
            html = await response.text()
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find detailed forecast div
    detailed_div = soup.find('div', id='detailed-forecast-body')
    if not detailed_div:
        logging.error("Detailed forecast not found in HTML.")
        return "Detailed forecast not found.", None

    # Extract label and text pairs and combine into one string with line breaks
    lines = []
    for row in detailed_div.find_all('div', class_='row-forecast'):
        label = row.find('div', class_='forecast-label').get_text(strip=True)
        text = row.find('div', class_='forecast-text').get_text(strip=True)
        lines.append(f"{label}: {text}")
    
    return '\n'.join(lines), None
