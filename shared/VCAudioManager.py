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

        self.disconnect_func = disconnect_func
        self.tts_manager = tts_manager
        self.bot_leave_messages = bot_leave_messages or ["Bot is leaving the voice channel"]

        self.processing_task: Optional[asyncio.Task] = None
        self.idle_task: Optional[asyncio.Task] = None
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

        # Cancel idle timer if running, since new audio is queued
        if self.idle_task and not self.idle_task.done():
            self.idle_task.cancel()

        # Start playback loop if not already running
        if not self.processing_task or self.processing_task.done():
            self.processing_task = asyncio.create_task(self._playback_loop())

    async def _playback_loop(self):
        """
        The loop used to join the voice channel and play audio from the queue.
        After the queue is empty, starts the idle timer.
        """
        while True:
            async with self.lock:
                if not self.queue:
                    break
                self.current_audio_item = self.queue.pop(0)

            try:
                # Connect or move to the correct voice channel
                if self._current_voice_channel is None or not self._current_voice_channel.is_connected():
                    try:
                        self._current_voice_channel = await asyncio.wait_for(
                            self.current_audio_item.voice_channel.connect(),
                            timeout=10
                        )
                        logging.info(f"Joined new voice channel {self._current_voice_channel.channel.name}")
                    except Exception as e:
                        logging.error(f"Failed to connect to voice channel: {e}")
                        self._current_voice_channel = None
                        continue  # Skip to next item
                elif self._current_voice_channel.channel != self.current_audio_item.voice_channel:
                    try:
                        await asyncio.wait_for(
                            self._current_voice_channel.move_to(self.current_audio_item.voice_channel),
                            timeout=10
                        )
                        logging.info(f"Moved to voice channel {self._current_voice_channel.channel.name}")
                    except Exception as e:
                        logging.error(f"Failed to move to voice channel: {e}")
                        continue  # Skip to next item

                # Play the audio
                self._current_voice_channel.play(
                    discord.FFmpegPCMAudio(
                        self.current_audio_item.audio_file_path,
                        options="-loglevel quiet"
                    )
                )
                self.current_state = AudioState.PLAYING
                logging.info(f"Playing audio: {self.current_audio_item.audio_name}")

                # Wait for the audio to finish playing
                while self._current_voice_channel.is_playing():
                    await asyncio.sleep(0.5)

                # After audio finishes, update state
                self.current_state = AudioState.STOPPED
                self.current_audio_item = None
                logging.info(f"Finished playing audio: {self.current_audio_item.audio_name}")

                # Add a delay between audios
                await asyncio.sleep(1)
                
            except discord.DiscordException as e:
                logging.error(f"Discord Exception: {e}")
            except Exception as e:
                logging.error(f"Error: {e}")

        # After all queue items are played, start idle timer
        self.idle_task = asyncio.create_task(self._idle_timer())

    async def _idle_timer(self):
        """
        Waits for leave_timeout_length after the last audio finishes.
        If no new audio is queued, disconnects from the voice channel.
        """
        try:
            await asyncio.sleep(self.leave_timeout_length)
            # Only disconnect if not playing and queue is still empty
            if self._current_voice_channel and not self._current_voice_channel.is_playing() and not self.queue:
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
            # Run provided disconnect function
            if self.disconnect_func:
                self.disconnect_func()

            # Announce bot is disconnecting
            leave_audio_path = self.tts_manager.process(random.choice(self.bot_leave_messages))
            self._current_voice_channel.play(
                discord.FFmpegPCMAudio(
                    leave_audio_path,
                    options="-loglevel quiet"
                )
            )

            # Wait for the leave message to finish playing. It needs a longer audio sleep time than usual.
            while self._current_voice_channel.is_playing():
                await asyncio.sleep(2)

            # Disconnect from the server
            logging.info(f"Disconnecting from voice channel {self._current_voice_channel.channel.name}")
            await self._current_voice_channel.disconnect()
            self._current_voice_channel = None

    def set_bot_leave_messages(self, leave_messages: list):
        """
        Updates the bot leave messages if the provided list is not empty.

        :param messages: List of leave messages (strings)
        """
        if leave_messages and all(isinstance(m, str) for m in leave_messages):
            self.bot_leave_messages = leave_messages
        else:
            logging.warning("The leave messages list is either empty or not all strings")

    def skip_current(self):
        """
        Skips the currently playing audio, if any.
        """
        if self._current_voice_channel and self._current_voice_channel.is_playing():
            self._current_voice_channel.stop()
            self.current_state = AudioState.STOPPED
            logging.info("Skipped current audio playback")
            return True
        return False
    
    def pause_current(self):
        """
        Pauses the currently playing audio, if any.
        """
        if self._current_voice_channel and self._current_voice_channel.is_playing():
            self._current_voice_channel.pause()
            self.current_state = AudioState.PAUSED
            logging.info("Paused current audio playback")
            return True
        return False
    
    def resume_current(self):
        """
        Resumes the currently paused audio, if any.
        """
        if self._current_voice_channel and self._current_voice_channel.is_paused():
            self._current_voice_channel.resume()
            self.current_state = AudioState.PLAYING
            logging.info("Resumed current audio playback")
            return True
        return False
    
    def get_current_audio_name(self):
        """
        Returns the name of the currently playing audio, if any.
        
        :return: The name of the current audio or None if no audio is playing
        """
        if self.current_audio_item:
            return self.current_audio_item.audio_name
        return None
