from discord import Guild
import logging

from shared.music_service import MusicService
from shared.discord_utils import find_member_by_display_name

class SongTools:
    def __init__(self, music_service: MusicService):
        self.music_service = music_service
        self.guild = None

    def set_guild(self, guild: Guild):
        """
        Sets the guild for the SongTools instance.
        :param guild: The Discord guild (server) to set
        """
        self.guild = guild

    async def play_song_url(self, url: str, user_display_name: str):
        """
        Queues a song based on a URL.
        :param url: The URL of the song to play
        :param user_display_name: The display name of the user requesting the song
        :return: Tuple containing a status message and None
        """
        member = find_member_by_display_name(self.guild, user_display_name)
        if not member:
            return f"Could not find member with display name '{user_display_name}'. It may also match another display name.", None

        try:
            await self.music_service.download_and_queue_song_from_url(url, member)
            return f"Queued song from URL for {user_display_name}.", None
        except Exception as e:
            logging.error(f"GPT request for play_song_url failed: {e}")
            return f"Failed to queue song from URL.", None

    async def play_song_search(self, search_query: str, user_display_name: str):
        """
        Queues a song based on a search query.
        :param search_query: The search query to find the song
        :param user_display_name: The display name of the user requesting the song
        :return: Tuple containing a status message and None
        """
        member = await find_member_by_display_name(self.guild, user_display_name)
        if not member:
            return f"Could not find member with display name '{user_display_name}'. It may also match another display name.", None

        try:
            await self.music_service.search_and_queue_song_from_query(search_query, member)
            return f"Queued song from search for {user_display_name}.", None
        except Exception as e:
            logging.error(f"GPT request for play_song_search failed: {e}")
            return f"Failed to queue song from search.", None

    async def skip_song(self):
        """
        Skips the currently playing song.
        :return: Tuple containing a status message and None
        """
        try:
            await self.music_service.audio_manager.skip_current()
            return "Skipped the current song.", None
        except Exception as e:
            logging.error(f"GPT request for skip_song failed: {e}")
            return f"Failed to skip song.", None
