from discord import Guild

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
        """
        # Finding the member who request the song
        member = find_member_by_display_name(self.guild, user_display_name)

        # Queuing the song
        await self.music_service.download_and_queue_song_from_url(url, member)

    async def play_song_search(self, search_query: str, user_display_name: str):
        """
        Queues a song based on a search query.
        :param search_query: The search query to find the song
        :param user_display_name: The display name of the user requesting the song
        """
        # Finding the member who request the song
        member = await find_member_by_display_name(self.guild, user_display_name)

        # Queuing the song
        await self.music_service.search_and_queue_song_from_query(search_query, member)

    async def skip_song(self):
        """
        Skips the currently playing song.
        """
        await self.music_service.audio_manager.skip_current()
