tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "play_song_url",
            "description": "Queues a song to play based on a provided URL. "
                           "The song will be added to the front of the queue. ",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the song to play. Must be a valid Youtube video or Spotify track link. No other URLs should be accepted."
                    },
                    "user_display_name": {
                        "type": "string",
                        "description": "The exact display name of the user requesting the song."
                    }
                },
                "required": ["url", "user_display_name"]
            }
        }
    }
]
