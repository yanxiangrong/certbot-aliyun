# Constants:

# This is the staging point for ACME-V2 within Let's Encrypt.
# Production 'https://acme-v02.api.letsencrypt.org/directory'
DEFAULT_DIRECTORY_URL = 'https://acme-staging-v02.api.letsencrypt.org/directory'

DEFAULT_USER_AGENT = 'python-acme'

# Account key size
DEFAULT_ACC_KEY_BITS = 2048

# Certificate private key size
DEFAULT_CERT_PKEY_BITS = 2048

# Domain name for the certificate.
DEFAULT_DOMAIN = 'client.example.com'
DEFAULT_EMAIL = 'fake@example.com'

DEFAULT_ACCESS_KEY_ID = ''
DEFAULT_ACCESS_KEY_SECRET = ''
DEFAULT_TYPE = 'TXT'
DEFAULT_CHALLENGE_RR = '_acme-challenge'
DEFAULT_TTL = 600
DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_DATA_DIR = 'run'
ACME_ACCOUNT_FILENAME = 'acme_account.json'
ACME_ACCOUNT_KEY_FILENAME = 'acme_account_key.json'
DEFAULT_KEY_COMP_DIR = 'save/'
PKEY_FILENAME = 'privkey.pem'
FULLCHAIN_FILENAME = 'fullchain.pem'

CONFIG_FILENAME = 'config.ini'

LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
