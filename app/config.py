import configparser
import json
import logging
import os
from pathlib import Path

from .consts import *

log = logging.getLogger(__name__)


class JsonDeSerializable:
    def to_json(self):
        return self.__dict__

    def from_json(self, json_obj):
        for key in json_obj:
            if self.__dict__.get(key) is not None:
                self.__dict__[key] = type(self.__dict__[key])(json_obj[key])


class AppConfig(JsonDeSerializable):
    def __init__(self):
        self.directory_url = DEFAULT_DIRECTORY_URL
        self.user_agent = DEFAULT_USER_AGENT
        self.acc_key_bits = DEFAULT_ACC_KEY_BITS
        self.cert_pkey_bits = DEFAULT_CERT_PKEY_BITS
        self.access_key_id = DEFAULT_ACCESS_KEY_ID
        self.access_key_secret = DEFAULT_ACCESS_KEY_SECRET
        self.email = DEFAULT_EMAIL
        self.type = DEFAULT_TYPE
        self.rr = DEFAULT_CHALLENGE_RR
        self.ttl = DEFAULT_TTL
        self.log_level = DEFAULT_LOG_LEVEL
        self.data_dir = DEFAULT_DATA_DIR


class DomainConfig(JsonDeSerializable):
    def __init__(self):
        self.domain = DEFAULT_DOMAIN
        self.save_dir = ""

    def from_json(self, json_obj):
        super().from_json(json_obj)
        if len(self.save_dir) == 0:
            self.save_dir = Path(DEFAULT_KEY_COMP_DIR).joinpath(self.domain)


app_config = AppConfig()
domain_config = list[DomainConfig]()


def load_config(filename: str):
    log.info(f'Load config file: {filename}')
    config = configparser.ConfigParser()

    try:
        if len(config.read(filename)) == 0:
            log.warning(f'Config file not found')
    except configparser.Error as err:
        log.error(err)
        exit(os.EX_CONFIG)

    if not config.has_section('APP'):
        log.debug(f'Has not APP section, use default')
        config.add_section('APP')

    try:
        app_config.from_json(config['APP'])
    except ValueError as err:
        log.error(err)
        exit(os.EX_CONFIG)
    config['APP'] = app_config.to_json()
    log.info(f'Loaded APP config')
    log.debug(f'Loaded APP config: {json.dumps(app_config.to_json(), indent=4)}')

    for section in config:
        if section in ['DEFAULT', 'APP']:
            continue
        d_config = DomainConfig()
        try:
            d_config.from_json(config[section])
        except ValueError as err:
            log.error(err)
            exit(os.EX_CONFIG)
        domain_config.append(d_config)
        config[section] = d_config.to_json()
        log.info(f'Loaded domain name config: {d_config.domain}')
        log.debug(f'Domain name config: {json.dumps(d_config.to_json(), indent=4)}')
