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
    },
    {
        "type": "function",
        "function": {
            "name": "play_song_search",
            "description": "Queues a song to play based on a search query. "
                           "The song will be added to the front of the queue. ",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": "The search query to find the song. This should be a general search term, not a specific URL. "
                                       "If the user provides an author and title, format it as 'title - author'. Otherwise, use a reasonable search query."
                    },
                    "user_display_name": {
                        "type": "string",
                        "description": "The exact display name of the user requesting the song."
                    }
                },
                "required": ["search_query", "user_display_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "skip_song",
            "description": "Skips the currently playing song in the voice channel.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]
