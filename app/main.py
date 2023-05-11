import logging
import sys
from pathlib import Path

from .config import load_config, app_config, domain_config
from .acme_client import ACMEClient
from .consts import *

log = logging.getLogger(__name__)


def init():
    logging.basicConfig(format=LOG_FORMAT, level=DEFAULT_LOG_LEVEL, stream=sys.stdout)
    log.info('Initializing')

    load_config(CONFIG_FILENAME)

    log_levels = ['CRITICAL', 'FATAL', 'ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']
    if app_config.log_level in log_levels:
        log.info(f'Set log level: {app_config.log_level}')
        logging.basicConfig(level=app_config.log_level)
    else:
        log.warning(f'Log level can only be set to {log_levels}, use default: {DEFAULT_LOG_LEVEL}')
    Path(app_config.data_dir).mkdir(parents=True, exist_ok=True)


def save_key_comp(save_dir: str, pkey_pem: bytes, fullchain_pem: bytes):
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    pkey_file = Path(save_dir).joinpath(PKEY_FILENAME)
    fullchain_file = Path(save_dir).joinpath(FULLCHAIN_FILENAME)

    log.info(f'Save private key to {pkey_file}')
    with open(pkey_file, 'wb') as f:
        f.write(pkey_pem)

    log.info(f'Save fullchain to {pkey_file}')
    with open(fullchain_file, 'wb') as f:
        f.write(fullchain_pem)


def load_key_comp(save_dir: str, ):
    pkey_file = Path(save_dir).joinpath(PKEY_FILENAME)
    fullchain_file = Path(save_dir).joinpath(FULLCHAIN_FILENAME)
    log.info(f'Load private key from {pkey_file}')
    try:
        with open(pkey_file, 'rb') as f:
            pkey_pem = f.read()
    except FileNotFoundError as err:
        log.error(f'File not found: {pkey_file}')
        raise err
    log.info(f'Load fullchain from {fullchain_file}')
    try:
        with open(fullchain_file, 'rb') as f:
            fullchain_pem = f.read()
    except FileNotFoundError as err:
        log.error(f'File not found: {fullchain_file}')
        raise err

    return pkey_pem, fullchain_pem


def main():
    init()

    acme_client = ACMEClient(app_config)
    acme_client.load_account()

    for i_config in domain_config:
        is_found = False
        pkey_pem, fullchain_pem = bytes(), bytes()
        try:
            pkey_pem, fullchain_pem = load_key_comp(i_config.save_dir)
            is_found = True
        except FileNotFoundError:
            pass

        if not is_found:
            pkey_pem, fullchain_pem = acme_client.issue_cert(i_config.domain)
        else:
            _, fullchain_pem = acme_client.renew(i_config.domain, pkey_pem)

        save_key_comp(i_config.save_dir, pkey_pem, fullchain_pem)

    log.info('Done and exit')
