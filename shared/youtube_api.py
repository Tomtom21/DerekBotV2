"""
youtube_api.py

This module provides a basic wrapper for initializing the YoutubeAPI.
Though this isn't necessary at the moment, it provides consistency and room for growth.
"""

import os
from googleapiclient.discovery import build

class YoutubeAPIStartError(Exception):
    """Exception raised for errors relating to the startup of the YouTube API"""
    pass

class YoutubeAPI:
    def __init__(self):
        # Logging into the YouTube api
        if (youtube_api_key := os.getenv("YOUTUBE_API_KEY")) is not None:
            self.youtube_api = build("youtube", "v3", developerKey=youtube_api_key)
        else:
            raise YoutubeAPIStartError("Failed to load/build youtube api")
