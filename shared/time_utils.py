from datetime import datetime
import pytz


def get_est_iso_date():
    utc_now = datetime.now()
    est_tz = pytz.timezone("America/New_York")
    est_now = utc_now.replace(tzinfo=pytz.utc).astimezone(est_tz)
    return est_now.isoformat()
