from src.lockbox import get_lockbox_secret
from src.constants import GOOGLE_CREDENTIALS_KEY, WORKDIR

with open(f'{WORKDIR}/secrets/credentials.json', 'w') as f:
    print(get_lockbox_secret(GOOGLE_CREDENTIALS_KEY), file=f) 
