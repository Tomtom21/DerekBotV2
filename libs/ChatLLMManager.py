import random

from discord import Message

import logging


class CachedMessage:
    def __init__(self, message_id, author, content, chain_id):
        self.message_id = message_id  # Need this incase we have a middle of cache lookup
        self.author = author
        self.message = content
        self.chain_id = chain_id


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
        if message.id in self.message_to_chain:
            return None

        # Getting the chain, chain-id
        chain = self.get_message_chain(message)
        if chain:
            chain_id = chain[0].chain_id
        else:
            chain_id = self._new_chain_id()
            chain = self.message_chains.setdefault(chain_id, [])



        if message.id not in self.message_chains.keys():
            # Finding the chain that the message would belong in
            chain = self.get_message_chain(message)
            chain_id = chain[0].chain_id

            # If a chain exists
            if chain is not None:
                # If the index of our parent id isn't the last item
                if message.reference.message_id in chain[:-1]:
                    # Saving the new chain info and
                    chain = chain[:chain.index(message.reference.message_id)]
                    chain_id = self._new_chain_id()
                    self.message_chains[chain_id] = chain
            else:
                chain_id = self._new_chain_id()
                self.message_chains[chain_id] = []
                chain = self.message_chains[chain_id]

            # Creating a new cached message
            cached_message = CachedMessage(message.id, message.author, message.content, chain_id)

            chain.append(cached_message)

    def get_message_chain(self, child_message: Message) -> [CachedMessage]:
        """Using the child message, get the message chain (if one exists)"""
        if child_message.reference in self.message_to_chain.keys():
            chain_id = self.message_to_chain[child_message.reference.message_id]

            return self.message_chains[chain_id]
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
