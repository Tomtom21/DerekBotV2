from datetime import datetime, timezone, timedelta
from models import SongRequest

class TitleScore:
    def __init__(self):
        self.TITLE_SCORE_TWEAKS = {
            "live": -0.15,
            "concert": -0.1,
            "official": 0.1,
            "karaoke": -0.1,
            "react": -0.15,
            "lyric": 0.35,
            "Behind the scenes": -0.1,
            "Clean": -0.1,
            "vocals only": -0.5,
            "cover": -0.2,
            "#shorts": -0.2
        }

    def get_relevance_score(self, song_request: SongRequest):
        """
        Generates a new relevance score for a song request base on title contents

        :param song_request: The song request whos relevance score we want to tweak
        :return: The new relevance score
        """
        # TODO: We may want this to simply default to zero in the future
        score = song_request.relevance_score

        # Checking the title for good or bad keywords
        for phrase, score_change in self.TITLE_SCORE_TWEAKS.items():
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
