from shared.data_manager import DataManager
from shared.time_utils import get_est_iso_date
import logging
from discord import Member

class MemoryTools:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    async def save_memory(self, memory_string: str, username: str):
        """
        Saves a memory to the chat_memories table in the database.

        :param memory_text: The memory text to save
        :param username: The name of the user saving the memory
        :return: Text stating whether the memory was saved or not
        """
        successfully_added = self.db_manager.add_table_data(
            table_name="chat_memories",
            json_data={
                "memory": memory_string,
                "created": get_est_iso_date(),
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
            for memory in self.db_manager.data.get("chat_memories", [])
        ]
