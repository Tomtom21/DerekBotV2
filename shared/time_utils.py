from datetime import datetime
import pytz

def get_est_iso_date():
    """
    DEPRECIATED: Use DB time. This is only being preserved incase future time functions are needed
    Gets the current date and time for EST in iso format
    
    :return: ISO formatted date and time in EST
    """
    utc_now = datetime.now()
    est_tz = pytz.timezone("America/New_York")
    est_now = utc_now.replace(tzinfo=pytz.utc).astimezone(est_tz)
    return est_now.isoformat()
