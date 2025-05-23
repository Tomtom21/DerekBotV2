from discord import Message
import logging


async def get_message_history(message: Message):
    """
    Building a list of the response chain of messages

    :param message: The initial child message to check the history for
    :return: The chain of messages
    """
    try:
        if message and message.reference:
            logging.info(f"Downloading message history for message: {message.id}")
            parent_message = await message.channel.fetch_message(message.reference.message_id)
            chain = await get_message_history(parent_message)

            # Continuing after we get all the messages
            chain.append(parent_message)
            return chain
        else:
            return []  # Base case
    except Exception as e:
        logging.error(e)
        return []  # Returning the base case if we have an issue
