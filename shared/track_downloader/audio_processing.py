from pydub.audio_segment import AudioSegment
from pathlib import Path
import logging
import os
from errors import AudioProcessingError

def match_target_amplitude(sound: AudioSegment, target_dbfs):
        """
        Changes a sound's dbfs to match the target_dbfs value

        :param sound: The sound to apply to this to
        :param target_dbfs: The target dbfs value
        :return: The new sound with the gain applied
        """
        change_in_dbfs = target_dbfs - sound.dBFS
        return sound.apply_gain(change_in_dbfs)

def normalize_audio_track(self, audio_path):
        """
        Normalizes the audio track so that it isn't too loud or quiet

        :param audio_path: The audio path to normalize
        :return: The new path of the normalized audio file
        """
        try:
            # Loading and normalizing
            new_path = Path(audio_path).with_suffix(".wav")
            sound = AudioSegment.from_file(audio_path)
            normalized_sound = self.match_target_amplitude(sound, -15.0)
            normalized_sound.export(new_path, format="wav")
            
            # Deleting the old audio
            os.remove(audio_path)
            logging.info(f"Deleted {audio_path} after normalization, new filename is {new_path}")
            return new_path
        except Exception as e:
            logging.warning(e)
            raise AudioProcessingError("Failed to normalize audio") from e
