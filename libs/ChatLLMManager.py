import json
import random
from typing import List

from discord import Message
import openai
from libs.discord_utils import get_message_history
import logging
from PIL import Image


class CachedMessage:
    def __init__(self, message_id, author, content, image_url):
        self.message_id = message_id  # Need this incase we have a middle of cache lookup
        self.author = author
        self.message = content
        self.image_url = image_url

    def __str__(self):
        return (f"('message_id': {self.message_id}, "
                f"'author': {self.author}, "
                f"'message': {self.message}, "
                f"'image_url': {self.image_url})")


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
                          content=msg.content,
                          image_url=self.get_image_from_message(msg))
            for msg in message_list
        ]

    def remove_author_name_if_bot(self, message: Message):
        """If the message author is the bot, return None, otherwise return the name"""
        return None if message.author.id == self.bot_user_id else message.author.name

    def get_image_from_message(self, message: Message):
        """Returns the first image from a message if one exists, otherwise returns None"""
        if message.author.id == self.bot_user_id:
            return None
        else:
            return message.attachments[0].url if message.attachments else None

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
            CachedMessage(message_id=message.id,
                          author=author_name,
                          content=message.content,
                          image_url=self.get_image_from_message(message))
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

    def clear_cache(self):
        self.message_to_chain.clear()
        self.message_chains.clear()


class ChatLLMManager:
    def __init__(self, api_key: str, system_prompt: str, model_name: str = "gpt-4o-mini",
                 max_tokens: int = 1000, temperature: float = 0.04,
                 tool_function_references: dict = None, tool_definitions: List[dict] = None,
                 get_memories=None):
        """

        :param api_key:
        :param system_prompt:
        :param model_name:
        :param functions:
        :param max_tokens:
        :param temperature:
        """
        # Updating the api_key, Defining the client
        self.client = openai.OpenAI(api_key=api_key)

        # Model settings
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.tool_function_references = tool_function_references
        self.tool_definitions = tool_definitions
        # self.function_handler = function_handler
        self.get_memories = get_memories

    def generate_gpt_messages_list(self, message_chain: List[CachedMessage]):
        """
        Converts cached messages to those ready for GPT consumption. Includes name information to the model.
        Also includes the system prompt as needed.
        :param message_chain: The cached messages to convert
        :return: A list of messages for use by chatgpt
        """
        # Adding the system prompt
        message_list = [{"role": "system", "content": self.system_prompt}]

        # Adding long-term memories for the bot
        if self.get_memories:
            memories = self.get_memories()

        for msg in message_chain:
            content = [{
                "type": "text",
                "text": msg.message if msg.author is None else f"{msg.author}: {msg.message}"
            }]

            if msg.image_url:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": msg.image_url, "detail": "low"},
                })

            message_list.append({
                "role": "assistant" if msg.author is None else "user",
                "content": content
            })

        return message_list

    async def run_model(self, message_list: []) -> openai.ChatCompletion.Message:
        """Runs the GPT model, returns the best message choice for later processing"""
        # Making the requests
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=message_list,
            tools=self.tool_definitions
        )
        return response.choices[0].message

    async def run_model_with_funcs(self, message_list: []) -> (str, [Image.Image]):
        """Runs the GPT model with function handling"""
        message = await self.run_model(message_list)



        # Doing any necessary tool calls
        if message.tool_calls:
            # Keep track of the previous tool_call request
            message_list.append(message.model_dump())

            # Tracking any images we need to attach
            image_attachments: [Image.Image] = []

            for tool in message.tool_calls:
                args = json.loads(tool.function.arguments)
                func = self.tool_function_references.get(tool.function.name)

                # If the function exists in the references
                if func:
                    gpt_message, image = await func(**args)

                    if image:
                        image_attachments.append(image)

                    # Adding the message to our message list
                    message_list.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "content": gpt_message
                    })
                else:
                    logging.error(f"function '{tool.function.name}' not found in tool references")

            # Making another call after all tools have run
            post_tool_message = await self.run_model(message_list)
            return post_tool_message, image_attachments
        else:
            return message, []

    async def process_with_history(self, message_chain: List[CachedMessage]):
        """Processes a message with cache history, the process_text could be merged into this"""
        message_list = self.generate_gpt_messages_list(message_chain)
        response, images = await self.run_model_with_funcs(message_list)

        return response, images



    async def process_text(self, text):
        """Processes only text through the AI model"""
        pass
