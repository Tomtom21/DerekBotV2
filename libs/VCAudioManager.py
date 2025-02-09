import asyncio
import logging
import threading
from enum import Enum
from typing import List, Optional
import discord


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
        return (
            f"AudioQueueItem(audio_file_path={self.audio_file_path}, "
            f"high_priority={self.high_priority}, "
            f"voice_channel={self.voice_channel}, "
            f"audio_name={self.audio_name}, "
            f"added_by={self.added_by})"
        )


class VCAudioManager:
    """
    The audio manager that maintains the queue, plays audio in the vc
     - This uses threading and asyncio to handle audio playback. Multiprocessing would be overkill
    """
    def __init__(self, leave_timeout_length=300):
        self.leave_timeout_length = leave_timeout_length
        self.queue: List[AudioQueueItem] = []
        self.current_audio_item: Optional[AudioQueueItem] = None
        self.current_state = AudioState.STOPPED
        self._current_voice_channel: Optional[discord.VoiceClient] = None

        # Handling async/threading
        self.processing_task = None
        self.idle_task = None
        self.lock = asyncio.Lock()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._setup_asyncio_thread, daemon=True)
        self._thread.start()

    def _setup_asyncio_thread(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def add_to_queue(self, audio_file_path, voice_channel, high_priority=True):
        """"""
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
            self.processing_task = asyncio.run_coroutine_threadsafe(self._playback_loop(), self._loop)

        # If the idle task is set and not done, cancel it
        if self.idle_task and not self.idle_task.done():
            self.idle_task.cancel()

    async def _playback_loop(self):
        """"""
        while self.queue:
            async with self.lock:
                self.current_audio_item = self.queue[0]
                self.queue.pop(0)

            try:
                # Connecting to the proper voice channel
                if self._current_voice_channel is None:
                    self._current_voice_channel = await self.current_audio_item.voice_channel.connect()
                    logging.info(f"Joined new voice channel {self._current_voice_channel.name}")
                elif self._current_voice_channel != self.current_audio_item.voice_channel:
                    await self._current_voice_channel.move_to(self.current_audio_item.voice_channel)
                    self._current_voice_channel = self.current_audio_item.voice_channel
                    logging.info(f"Moved to voice channel {self._current_voice_channel.name}")

                # Playing the audio
                self._current_voice_channel.play(discord.FFmpegPCMAudio(self.current_audio_item.audio_file_path),
                                                 options="-loglevel quiet")
            except discord.DiscordException as e:
                logging.error(f"Discord Exception: {e}")
            except Exception as e:
                logging.error(f"Error: {e}")

            await asyncio.sleep(1)

        # Starting the idle task if we finish all queue items
        self.idle_task = asyncio.create_task(self._idle_timer())

    async def _idle_timer(self):
        try:
            await asyncio.sleep(self.leave_timeout_length)

            # Leaving the vc
            await self._disconnect()
        except asyncio.CancelledError:
            pass

    def disconnect_from_vc(self):
        if self._current_voice_channel:
            # Calling the async disconnect
            asyncio.run_coroutine_threadsafe(self._disconnect(), self._loop)
            return True
        else:
            return False

    async def _disconnect(self):
        if self._current_voice_channel:
            await self._current_voice_channel.disconnect()
            self._current_voice_channel = None
            logging.info(f"Disconnecting from voice channel{self._current_voice_channel}")
