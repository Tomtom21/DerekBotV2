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
    }
]
