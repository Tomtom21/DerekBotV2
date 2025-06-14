import asyncio
import logging
import random
from enum import Enum
from typing import List, Optional
import discord
from shared.TTSManager import TTSManager


class AudioState(Enum):
    PAUSED = "paused"
    PLAYING = "playing"
    STOPPED = "stopped"


class AudioQueueItem:
    """The queue items for the audio queue"""
    def __init__(self, audio_file_path, voice_channel, high_priority, audio_name="System audio", added_by="System"):
        self.audio_file_path = audio_file_path
        self.voice_channel = voice_channel
        self.high_priority = high_priority
        self.audio_name = audio_name
        self.added_by = added_by

    def __repr__(self):
        """
        Changes the output representation when the object is printed to console

        :return: The new output representation string
        """
        return (
            f"AudioQueueItem(audio_file_path={self.audio_file_path}, "
            f"high_priority={self.high_priority}, "
            f"voice_channel={self.voice_channel}, "
            f"audio_name={self.audio_name}, "
            f"added_by={self.added_by})"
        )


class VCAudioManager:
    def __init__(self,
                 tts_manager: TTSManager,
                 bot_leave_messages: List = None,
                 disconnect_func=None,
                 leave_timeout_length=300):
        """
        Audio manager that maintains the queue, plays audio in the vc
        Threading and async are used to handle audio playback. Multiprocessing would be overkill

        :param tts_manager: The TTSManager to be used for leave messages
        :param bot_leave_messages: A list of leave messages for the bot to randomly choose from
        :param disconnect_func: An extra function to call when the bot disconnects
        :param leave_timeout_length: The amount of time the bot should wait before disconnecting
        """
        self.leave_timeout_length = leave_timeout_length
        self.queue: List[AudioQueueItem] = []
        self.current_audio_item: Optional[AudioQueueItem] = None
        self.current_state = AudioState.STOPPED
        self._current_voice_channel: Optional[discord.VoiceClient] = None

        # Leaving VC
        self.disconnect_func = disconnect_func
        self.tts_manager = tts_manager
        self.bot_leave_messages = bot_leave_messages or ["Bot is leaving the voice channel"]

        # Handling async/threading
        self.processing_task = None
        self.idle_task = None
        self.lock = asyncio.Lock()

    async def add_to_queue(self, audio_file_path, voice_channel, high_priority=True):
        """
        Adds an audio to the queue, positions it in the list based on priority

        :param audio_file_path: The path to the audio
        :param voice_channel: The voice channel to play the audio in
        :param high_priority: Whether the audio is high priority
        """
        new_item = AudioQueueItem(audio_file_path, voice_channel, high_priority)

        # Finding the first low-priority item, other defaulting to appending
        if high_priority:
            insert_idx = next(
                (idx for idx, item in enumerate(self.queue) if not item.high_priority),
                len(self.queue)
            )
            self.queue.insert(insert_idx, new_item)
        else:
            self.queue.append(new_item)

        # Determining whether to start the processing loop task
        if not self.processing_task or self.processing_task.done():
            self.processing_task = asyncio.create_task(self._playback_loop())

        # If the idle task is set and not done, cancel it
        if self.idle_task and not self.idle_task.done():
            self.idle_task.cancel()

    async def _playback_loop(self):
        """
        The loop used to join the voice channel and play audio from
        """
        while self.queue:
            async with self.lock:
                self.current_audio_item = self.queue[0]
                self.queue.pop(0)

            try:
                # Connecting to the proper voice channel
                if self._current_voice_channel is None:
                    self._current_voice_channel = await self.current_audio_item.voice_channel.connect()
                    logging.info(f"Joined new voice channel {self._current_voice_channel.channel.name}")
                elif self._current_voice_channel.channel != self.current_audio_item.voice_channel:
                    await self._current_voice_channel.move_to(self.current_audio_item.voice_channel)
                    logging.info(f"Moved to voice channel {self._current_voice_channel.channel.name}")

                # Playing the audio
                self._current_voice_channel.play(
                    discord.FFmpegPCMAudio(
                        self.current_audio_item.audio_file_path,
                        options="-loglevel quiet"
                    )
                )
            except discord.DiscordException as e:
                logging.error(f"Discord Exception: {e}")
            except Exception as e:
                logging.error(f"Error: {e}")

            await asyncio.sleep(1)

        # Starting the idle task if we finish all queue items
        self.idle_task = asyncio.create_task(self._idle_timer())

    async def _idle_timer(self):
        """
        Waiting for the leave_timeout_length, then leaving the current voice channel
        """
        try:
            await asyncio.sleep(self.leave_timeout_length)

            # Leaving the vc
            await self._disconnect()
        except asyncio.CancelledError:
            pass

    async def disconnect_from_vc(self):
        """
        User-callable function to ask the bot to disconnect from the current voice channel

        :return: True if the bot is in a voice channel and the bot has been disconnected, False otherwise
        """
        if self._current_voice_channel:
            # Calling the async disconnect
            await self._disconnect()
            return True
        else:
            return False

    async def _disconnect(self):
        """
        Async disconnect function that disconnects the bot from the current voice channel
        """
        if self._current_voice_channel:
            # Running a provided disconnect function
            if self.disconnect_func:
                self.disconnect_func()

            # Announcing that the bot is disconnecting.
            leave_audio_path = self.tts_manager.process(random.choice(self.bot_leave_messages))
            self._current_voice_channel.play(
                discord.FFmpegPCMAudio(
                    leave_audio_path,
                    options="-loglevel quiet"
                )
            )

            # Disconnecting from the server
            await self._current_voice_channel.disconnect()
            self._current_voice_channel = None
            logging.info(f"Disconnecting from voice channel{self._current_voice_channel}")
