tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Saves a string for the model to reference later in it's system message as a memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_string": {
                        "type": "string",
                        "description": "The string to save as a memory. Should be short but descriptive."
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
    }
]
