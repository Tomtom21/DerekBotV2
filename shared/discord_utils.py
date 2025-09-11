import logging

from discord import Message, Guild, Member, Interaction

from shared.errors import NotInVoiceChannelError

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

def find_member_by_display_name(guild: Guild, display_name: str):
    """
    Finds a member in the guild by their display name.

    :param guild: The Discord guild (server) to search in
    :param display_name: The display name of the member to find
    :return: The member object if found, None otherwise
    """
    matches = [member for member in guild.members if member.display_name == display_name]
    if len(matches) == 1:
        return matches[0]

    return None  # Either no match or multiple matches found

def is_in_voice_channel(member: Member):
    """
    Checks if a member is in a voice channel.

    :param member: The Discord member to check
    :return: True if the member is in a voice channel, False otherwise
    """
    return hasattr(member, 'voice') and member.voice and member.voice.channel

def ensure_in_voice_channel(interaction: Interaction):
    """
    Ensures that a member is in a voice channel.

    :param interaction: The Discord interaction object
    :raises NotInVoiceChannelError: If the user is not in a voice channel
    """
    if not is_in_voice_channel(interaction.user):
        raise NotInVoiceChannelError("Member is not in a voice channel")
