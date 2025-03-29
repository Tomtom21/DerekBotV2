import random

from discord import Message

import logging


class CachedMessage:
    def __init__(self, message_id, author, content):
        self.message_id = message_id  # Need this incase we have a middle of cache lookup
        self.author = author
        self.message = content

    def __str__(self):
        return (f"('message_id': {self.message_id}, "
                f"'author': {self.author}, "
                f"'message: {self.message}'")
    

class ConversationCache:
    def __init__(self):
        """
        message_chains: stores each chain, with all conversation info
        message_to_chain: stores each individual message and the chain it is found in
        Authors listed as None are the bot and are system messages
        """
        self.message_chains = {}
        self.message_to_chain = {}

    def _new_chain_id(self):
        """Gets a random chain id that is not already used"""
        current_ids = self.message_chains.keys()
        available_ids = set(range(1, 999999)) - current_ids
        return random.choice(tuple(available_ids))

    def add_message(self, message: Message):
        """Adds a message to the cache using discord.Message, returns the chain id"""
        # Checking if a message is already cached
        print(message.content)
        if message.id in self.message_to_chain:
            print("Returning because we already have this message")
            return None

        # Getting the chain, making a new one if it doesn't exist
        chain_id = self.get_message_chain(message)
        if chain_id:
            chain = self.message_chains[chain_id]

            # Getting the current list of message ids in the chain
            chain_message_ids = [chain_msg.message_id for chain_msg in chain]

            # If the parent message is not at the end of the cache, create a new chain id/chain
            if message.reference.message_id in chain_message_ids[:-1]:
                chain = chain[:chain_message_ids.index(message.reference.message_id) + 1]
                chain_id = self._new_chain_id()
                self.message_chains[chain_id] = chain
        else:
            # Making the new chain
            chain_id = self._new_chain_id()
            chain = self.message_chains.setdefault(chain_id, [])

        # Adding the new item to the chain
        self.message_chains[chain_id].append(
            CachedMessage(message.id, message.author.name, message.content)
        )
        self.message_to_chain[message.id] = chain_id

    def get_message_chain(self, child_message: Message):
        """Using the child message, returns the id of the chain, none if one isn't found"""
        if child_message.reference:
            # Get the reference from the cache, if not there, then we need to download it from discord
            if child_message.reference.message_id in self.message_to_chain.keys():
                chain_id = self.message_to_chain[child_message.reference.message_id]
                return chain_id
            else:
                print("Downloading")
                pass
        else:
            return None


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
