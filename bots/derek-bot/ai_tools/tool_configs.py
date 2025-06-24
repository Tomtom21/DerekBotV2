tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Suggest saving important or relevant information the model might need later. If something seems worth remembering, say something like 'This might be useful later — want me to remember it?' Only call this tool if the user agrees or explicitly asks to save something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_string": {
                        "type": "string",
                        "description": "The memory to save. "
                                       "If about a user, use their username (e.g., 'alice likes crayons'). "
                                       "If about the bot or something else, do not use a username."
                    },
                    "username": {
                        "type": "string",
                        "description": "The username of the user who requested to save the information."
                    }
                },
                "required": ["memory_string", "username"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_color_swatch",
            "description": "Generates a color swatch image from a given hex color code. "
                           "Should be used when a user would like to see color samples.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hex_code": {
                        "type": "string",
                        "description": "The hex color code to generate a swatch for (e.g., '#ff0000' or 'ff0000')."
                    }
                },
                "required": ["hex_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_spc_outlook_text",
            "description": (
                "Retrieves the Storm Prediction Center (SPC) outlook text for the specified day. "
                "Use this to provide users with the latest severe weather outlook summary."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "day": {
                        "type": "integer",
                        "description": (
                            "The outlook day (1-8). Use 1 for Day 1, 2 for Day 2, 3 for Day 3. "
                            "Any value from 4 to 8 will return the same Day 4-8 combined outlook."
                        )
                    }
                },
                "required": ["day"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_spc_outlook_image",
            "description": (
                "Retrieves the Storm Prediction Center (SPC) outlook risk image for the specified day. "
                "Use this to provide users with the latest severe weather risk map."
                "If using this, do not attempt to embed an image via a text response."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "day": {
                        "type": "integer",
                        "description": (
                            "The outlook day (1-8). Use 1 for Day 1, 2 for Day 2, 3 for Day 3. "
                            "Any value from 4 to 8 will return the same Day 4-8 combined outlook."
                        )
                    }
                },
                "required": ["day"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_local_forecast",
            "description": (
                "Retrieves the local weather forecast for a specified latitude and longitude, "
                "but only for locations within the United States. "
                "Use this to provide users with detailed weather forecasts for a specific U.S. location. "
                "This tool does not work for locations outside the United States."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {
                        "type": "number",
                        "description": "Latitude of the location (e.g., 40.7128)"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Longitude of the location (e.g., -74.0060)"
                    }
                },
                "required": ["lat", "lon"]
            }
        }
    }
]
