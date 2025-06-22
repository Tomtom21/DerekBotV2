from shared.data_manager import DataManager
from shared.time_utils import get_est_iso_date
import logging
from discord import Member

class MemoryTools:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def save_memory(self, memory_text: str, user: Member):
        """
        Saves a memory to the chat_memories table in the database.

        :param memory_text: The memory text to save
        :param user_id: The ID of the user saving the memory
        :return: Text stating whether the memory was saved or not
        """
        self.db_manager.ensure_user_exists(user)
        successfully_added = self.db_manager.add_table_data(
            table_name="chat_memories",
            json_data={
                "memory": memory_text,
                "created": get_est_iso_date(),
                "added_by": user.id
            }
        )
        if successfully_added:
            logging.info(f"User {user.name} saved memory: {memory_text}")
            return "Memory successfully saved.", None
        else:
            return "Failed to save memory.", None
