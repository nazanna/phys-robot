import os

workdir=os.path.dirname(os.path.abspath(__file__))
DEBUG = 'andrew' in workdir

responses_db_name = f'{workdir}/user_responses{"_test" if DEBUG else ""}.db'
users_db_name = f'{workdir}/users{"_test" if DEBUG else ""}.db'
token_key = f"physbot-{"test" if DEBUG else "main"}-token"

ADMIN_USERNAMES = ['nazanna25', 'andr_zhi']