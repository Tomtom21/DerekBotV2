import logging

from shared.track_downloader.song_downloader import SongDownloader
from shared.VCAudioManager import VCAudioManager

class MusicService:
    def __init__(self, song_downloader: SongDownloader, audio_manager: VCAudioManager):
        self.song_downloader = song_downloader
        self.audio_manager = audio_manager

    async def download_and_queue_song(
            self,
            song_url: str,
            voice_channel,
            high_priority: bool = None
    ):
        """
        Downloads a song using the SongDownloader and adds it to the VCAudioManager's queue.

        :param song_downloader: Instance of SongDownloader to handle the download
        :param audio_manager: Instance of VCAudioManager to manage the playback queue
        :param song_url: The URL of the song to download and queue
        :return: The SongRequest object if successful, None otherwise
        """
        try:
            # Download the song
            song_request = await self.song_downloader.download_song_by_url(song_url)
            logging.info(f"Downloaded song: {song_request.title}")

            # Add the downloaded song to the audio manager's queue
            if high_priority is not None:
                await self.audio_manager.add_to_queue(
                    song_request, voice_channel, high_priority=high_priority
                )
            else:
                await self.audio_manager.add_to_queue(song_request, voice_channel)
            logging.info(f"Added song to queue: {song_request.title}")

            return song_request
        except Exception as e:
            logging.error(f"Error downloading and queuing song from URL {song_url}: {e}")
            return None
