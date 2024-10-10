import os

import subprocess

current_user = subprocess.check_output(['whoami']).decode().strip()
DEBUG = False if current_user == 'phys-bot' else True
workdir=os.path.dirname(os.path.abspath(__file__))
print(DEBUG)
responses_db_name = f'{workdir}/user_responses{"_test" if DEBUG else ""}.db'
users_db_name = f'{workdir}/users{"_test" if DEBUG else ""}.db'
token_key = f"physbot-{"test" if DEBUG else "main"}-token"
