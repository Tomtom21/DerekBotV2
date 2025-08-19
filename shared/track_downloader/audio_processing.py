import os
import logging
from pathlib import Path

from pydub.audio_segment import AudioSegment
from shared.track_downloader.errors import AudioProcessingError


def match_target_amplitude(sound: AudioSegment, target_dbfs):
        """
        Changes a sound's dbfs to match the target_dbfs value

        :param sound: The sound to apply to this to
        :param target_dbfs: The target dbfs value
        :return: The new sound with the gain applied
        """
        change_in_dbfs = target_dbfs - sound.dBFS
        return sound.apply_gain(change_in_dbfs)

def normalize_audio_track(audio_path):
    """
    Normalizes the audio track so that it isn't too loud or quiet

    :param audio_path: The audio path to normalize
    :return: The new path of the normalized audio file
    """
    try:
        audio_path = Path(audio_path)
        # Get original extension and stem
        ext = audio_path.suffix  # e.g., '.m4a'
        stem = audio_path.stem
        
        # Create new filename with 'normalized' tag
        new_path = audio_path.with_name(f"{stem}_normalized{ext}")

        # Load and normalize
        sound = AudioSegment.from_file(audio_path)
        normalized_sound = match_target_amplitude(sound, -15.0)
        normalized_sound.export(new_path, format='mp4')

        # Delete the old audio
        os.remove(audio_path)
        logging.info(f"Deleted {audio_path} after normalization, new filename is {new_path}")
        return new_path
    except Exception as e:
        logging.warning(e)
        raise AudioProcessingError("Failed to normalize audio") from e
