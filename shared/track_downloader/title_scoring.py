from datetime import datetime, timezone, timedelta

from shared.track_downloader.models import SongRequest
from shared.constants import TITLE_SCORE_TWEAKS

class TitleScore:
    """
    Keywords and their associated values within a title.
    For instance, a result with "lyric" adds significant value, while "vocals only" removes a lot of value.
    """

    def get_relevance_score(self, song_request: SongRequest):
        """
        Generates a new relevance score for a song request base on title contents

        :param song_request: The song request whos relevance score we want to tweak
        :return: The new relevance score
        """
        # TODO: We may want this to simply default to zero in the future
        score = song_request.relevance_score

        # Checking the title for good or bad keywords
        for phrase, score_change in TITLE_SCORE_TWEAKS.items():
            if phrase.lower() in song_request.title.lower():
                score += score_change

        # Penalizing very new results
        upload_date = datetime.fromisoformat(
            song_request.source_publish_date.replace("Z", "+00:00")
        )
        if upload_date > (datetime.now(timezone.utc) - timedelta(weeks=5)):
            score += -0.2

        # Penalizing short videos
        if song_request.content_duration < 40:
            score += -0.4
        elif song_request.content_duration < 80:
            score += -0.2

        return score
