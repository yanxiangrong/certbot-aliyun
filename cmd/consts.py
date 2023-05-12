EXAMPLE_CONFIG_FILE = '''[APP]
# Production Environment https://acme-v02.api.letsencrypt.org/directory
# Staging Environment https://acme-staging-v02.api.letsencrypt.org/directory
directory_url = https://acme-staging-v02.api.letsencrypt.org/directory
user_agent = python-acme
acc_key_bits = 2048
cert_pkey_bits = 2048
access_key_id = xxxxxxxx
access_key_secret = xxxxxxx
type = TXT
challenge_rr = _acme-challenge
ttl = 600
log_level = INFO
data_dir = run

[client.example.com]
domain = client.example.com
email = fake@example.com
save_dir = save/client.example.com
'''

PRODUCTION_URL = 'https://acme-v02.api.letsencrypt.org/directory'
STAGING_URL = 'https://acme-staging-v02.api.letsencrypt.org/directory'
VAR_APP_CONFIG = '''[APP]
# Production Environment https://acme-v02.api.letsencrypt.org/directory
# Staging Environment https://acme-staging-v02.api.letsencrypt.org/directory
directory_url = {directory}
user_agent = python-acme
acc_key_bits = 2048
cert_pkey_bits = 2048
access_key_id = {access_key_id}
access_key_secret = {access_key_secret}
type = TXT
challenge_rr = _acme-challenge
ttl = 600
log_level = INFO
data_dir = run
email = {email}

'''

VAR_DOMAIN_CONFIG = '''[{domain}]
domain = {domain}
save_dir = save/{domain}

'''

EXAMPLE_SERVICE_FILE = '''[Unit]
Description=Certbot--维护 SSL证书
Wants=network.target network-online.target
After=network.target network-online.target

[Service]
Type=idle
WorkingDirectory={wd}
ExecStart={exec}
'''

EXAMPLE_TIMER_FILE = '''[Unit]
Description=Certbot--维护 SSL证书

[Timer]
OnCalendar=*-1,3,5,7,9,11-01 02:00:00


[Install]
WantedBy=timers.target
'''

NAME = 'certbot-aliyun'
CONFIG_FILENAME = 'config.ini'
SYSTEMD_DIR = '/usr/lib/systemd/system/'
SYSTEMD_DIR_USER = '~/.config/systemd/user/'
INSTALL_CONFIG_PATH = f'/usr/local/etc/{NAME}/'
INSTALL_BIN_PATH = '/usr/local/bin/'
INSTALL_DEP_PATH = f'/usr/local/lib/{NAME}/'
VENV_DIR_NAME = f'venv/'
BIN_NAME = f'bin'
PYTHON_NAME = f'python'
PIP_NAME = f'pip'
REQUIREMENTS_NAME = f'requirements.txt'
