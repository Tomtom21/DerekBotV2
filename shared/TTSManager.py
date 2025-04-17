from google.cloud import texttospeech
from constants import GOOGLE_TTS_VOICE_INFO
import os
import logging

from shared.file_utils import get_random_file_id


class TTSManager:
    def __init__(self, output_path, voice_info: dict = GOOGLE_TTS_VOICE_INFO, speaking_rate=0.9):
        """
        Class for handling TTS interactions with Google's api.
        Environment variable named "GOOGLE_APPLICATION_CREDENTIALS" must be set for api to work

        :param output_path: The path that the output mp3 files will be stored
        :param voice_info: A dictionary containing the language, and the code and voice name for each desired language
        :param speaking_rate: The speaking rate the voice should have
        """

        # Making sure we have the environment variable set
        if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", None) is None:
            raise EnvironmentError("No value set for 'GOOGLE_APPLICATION_CREDENTIALS'")

        self.client = texttospeech.TextToSpeechClient()
        self.output_path = output_path
        self.voice_info = voice_info
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate
        )

        # Setting the first option as our default voice config
        self.voice_config = texttospeech.VoiceSelectionParams(
            language_code=voice_info['english-US']['language_code'],
            name=voice_info['english-US']['voice_name']
        )

    def set_voice(self, language):
        """
        Sets the voice configuration for synthesis. Uses the keys found in constants.py for voice info

        :param language: A language key from 'GOOGLE_TTS_VOICE_INFO'
        """
        # Making sure we definitely have a valid value
        default = next(iter(self.voice_info))
        voice = self.voice_info.get(language, default)

        # Updating the voice configuration
        self.voice_config = texttospeech.VoiceSelectionParams(
            language_code=voice['language_code'],
            name=voice['voice_name']
        )

    def process(self, text) -> str:
        """
        Synthesize speech based on the input text. Saves the file in the output path location with a random file id

        :param text: The text to synthesize
        :return: The file path of the synthesized text
        """
        # Generating a random filename
        new_file_id = get_random_file_id(self.output_path)
        new_file_path = os.path.join(self.output_path, new_file_id + ".mp3")

        try:
            # Making the synthesis request
            synthesis_input = texttospeech.SynthesisInput(text=text)
            response = self.client.synthesize_speech(
                input=synthesis_input, voice=self.voice_config, audio_config=self.audio_config
            )

            # Saving the audio content
            with open(new_file_path, "wb") as f:
                f.write(response.audio_content)

            return new_file_path
        except Exception as e:
            logging.error(e)
