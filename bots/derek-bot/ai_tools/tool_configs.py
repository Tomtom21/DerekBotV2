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
                        "description": "The descriptive memory to save. Include the user's username in the memory."
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
