from datetime import datetime
import pytz


# NOTE: This should be depreciated in the future in favor of using the default system time rather than set EST
def get_est_iso_date():
    """
    Gets the current date and time for EST in iso format
    
    :return: ISO formatted date and time in EST
    """
    utc_now = datetime.now()
    est_tz = pytz.timezone("America/New_York")
    est_now = utc_now.replace(tzinfo=pytz.utc).astimezone(est_tz)
    return est_now.isoformat()
