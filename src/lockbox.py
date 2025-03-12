import re
import subprocess
import logging

logger = logging.getLogger(__name__)

def get_lockbox_secret(secret_name: str):
    command = f'yc lockbox payload get {secret_name}'
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        command_output = result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error occurred: {e}")
        exit(1)

    match = re.search(r'text_value:\s*(\S+)', command_output)
    if match:
        value = match.group(1)
        return value
    else:
        logger.error("Lockbox secret is empty!")
        exit(1)
