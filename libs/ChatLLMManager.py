import random

from discord import Message
from libs.discord_utils import get_message_history

import logging


class CachedMessage:
    def __init__(self, message_id, author, content):
        self.message_id = message_id  # Need this incase we have a middle of cache lookup
        self.author = author
        self.message = content

    def __str__(self):
        return (f"('message_id': {self.message_id}, "
                f"'author': {self.author}, "
                f"'message': {self.message})")
    

class ConversationCache:
    def __init__(self):
        """
        message_chains: stores each chain, with all conversation info
        message_to_chain: stores each individual message and the chain it is found in
        Authors listed as None are the bot and are system messages
        Bot user id is the id of the bot so we can identify which messages are from the bot
        """
        self.message_chains = {}
        self.message_to_chain = {}
        self.bot_user_id = None

    def update_bot_user_id(self, user_id):
        """
        Sets the bot user id for determining who the bot is in the conversation
        Mostly necessary because the user id isn't available immediate upon discord bot init
        """
        self.bot_user_id = user_id

    async def _new_chain_id(self):
        """Gets a random chain id that is not already used"""
        current_ids = self.message_chains.keys()
        available_ids = set(range(1, 999999)) - current_ids
        return random.choice(tuple(available_ids))

    def convert_messages_to_cache_chain(self, message_list: [Message]):
        """Converts a list of discord messages to a list of cache messages"""
        return [
            CachedMessage(message_id=msg.id,
                          author=self.remove_author_name_if_bot(msg),
                          content=msg.content)
            for msg in message_list
        ]

    def remove_author_name_if_bot(self, message: Message):
        """If the message author is the bot, return None, otherwise return the name"""
        return None if message.author.id == self.bot_user_id else message.author.name

    async def add_message(self, message: Message):
        """Adds a message to the cache using discord.Message, returns the chain id"""
        # Checking if a message is already cached
        if message.id in self.message_to_chain:
            return None

        # Getting the chain, making a new one if it doesn't exist
        chain_id = await self._find_message_chain_id(message)
        if chain_id:
            chain = self.message_chains[chain_id]

            # Getting the current list of message ids in the chain
            chain_message_ids = [chain_msg.message_id for chain_msg in chain]

            # If the parent message is not at the end of the cache, create a new chain id/chain
            if message.reference.message_id in chain_message_ids[:-1]:
                chain = chain[:chain_message_ids.index(message.reference.message_id) + 1]
                chain_id = await self._new_chain_id()
                self.message_chains[chain_id] = chain
        else:
            # Making the new chain
            chain_id = await self._new_chain_id()
            chain = self.message_chains.setdefault(chain_id, [])

        # Checking to see if we have a bot message, treating it as such if we do, otherwise just add the name
        author_name = self.remove_author_name_if_bot(message)
        self.message_chains[chain_id].append(
            CachedMessage(message.id, author_name, message.content)
        )
        self.message_to_chain[message.id] = chain_id

    async def _find_message_chain_id(self, child_message: Message):
        """
        Using the child message, returns the id of the chain, none if one isn't found.
        For internal use only, more friendly functions should be available for getting chain without list interactions
        """
        if child_message.reference:
            # Get the reference from the cache, if not there, then we need to download it from discord
            if child_message.reference.message_id in self.message_to_chain.keys():
                chain_id = self.message_to_chain[child_message.reference.message_id]
                return chain_id
            else:
                message_chain: [Message] = await get_message_history(child_message)
                chain = self.convert_messages_to_cache_chain(message_chain)

                # Assuming we got some messages from the history, add everything back to the cache
                if chain:
                    chain_id = await self._new_chain_id()
                    for chain_msg in chain:
                        self.message_to_chain[chain_msg.message_id] = chain_id

                    self.message_chains[chain_id] = chain
                    return chain_id
                else:
                    # Defaulting to none if for whatever reason an empty list is returned
                    return None
        else:
            return None

    def get_message_chain(self, message: Message) -> list:
        """Returns a message chain for the given message if one exists"""
        # Getting the chain id/chain if one is available
        if message.id in self.message_to_chain.keys():
            chain_id = self.message_to_chain[message.id]
            return self.message_chains[chain_id]
        else:
            logging.warning(f"Failed to find message with id {message.id} in cache")
            return []


class ChatLLMManager:
    def __init__(self, system_prompt, get_message_history=None, model_name="gpt-4o-mini"):
        # Model settings
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.max_tokens = 1000
        self.temperature = 0.04

        # Getting message data later (If none, we don't use process, only process_text())
        self.get_message_history = get_message_history

        # For queueing message history

    def process(self, message: Message):
        if self.get_message_history is not None:
            pass
        else:
            logging.error("No get_message_history function defined")

    def process_text(self, text):
        pass

    def clear_message_history_cache(self):
        pass

    def get_cache_history(self):
        pass
