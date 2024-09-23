import os

DEBUG = True
workdir=os.path.dirname(os.path.abspath(__file__))

responses_db_name = f'{workdir}/user_responses{"_test" if DEBUG else ""}.db'
users_db_name = f'{workdir}/users{"_test" if DEBUG else ""}.db'
token_key = f"physbot-{"test" if DEBUG else "main"}-token"
