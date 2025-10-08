from shared.data_manager import DataManager
import logging
from discord import Member

class MemoryTools:
    def __init__(self, db_manager, memory_table_name):
        self.db_manager = db_manager
        self.memory_table_name = memory_table_name

    async def save_memory(self, memory_string: str, username: str):
        """
        Saves a memory to the chat_memories table in the database.

        :param memory_text: The memory text to save
        :param username: The name of the user saving the memory
        :return: Text stating whether the memory was saved or not
        """
        successfully_added = self.db_manager.add_table_data(
            table_name=self.memory_table_name,
            json_data={
                "memory": memory_string,
                "added_by": None
            }
        )
        if successfully_added:
            logging.info(f"User {username} saved memory: {memory_string}")
            return "Memory successfully saved.", None
        else:
            return "Failed to save memory.", None

    def get_memories(self):
        """
        Retrieves all memories from the chat_memories table in the database for bot consumption.

        :return: A list of memory strings
        """
        return [
            memory["memory"]
            for memory in self.db_manager.data.get(self.memory_table_name, [])
        ]
