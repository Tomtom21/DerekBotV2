import os
import base64

def save_google_service_file():
    """
    This function decodes the base64 encoded Google service credentials and saves it to a file.
    The environment variable 'GOOGLE_CRED_FILE' should contain the base64 encoded string.
    """
    # Making sure we have the environment variable set
    if os.environ.get("GOOGLE_CRED_FILE", None) is None:
        raise EnvironmentError("No value set for 'GOOGLE_CRED_FILE'")
    
    # Converting our Google service json to back from base64 and putting it into a file
    google_cred_b64 = os.environ.get('GOOGLE_CRED_FILE')
    if google_cred_b64:
        google_cred_json = base64.b64decode(google_cred_b64)
        with os.fdopen(os.open('google-services.json',
                  os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                  0o600), 'wb') as f:
            f.write(google_cred_json)
