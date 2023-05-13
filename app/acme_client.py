import json
import logging
import os
import typing
from pathlib import Path

import OpenSSL
import josepy as jose
from acme import challenges
from acme import client
from acme import crypto_util
from acme import messages
from acme.messages import RegistrationResource
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

from ali_dns import Client
from .config import AppConfig
from .consts import *

log = logging.getLogger(__name__)


def select_dns01_chl(order):
    """Extract authorization resource from within order resource."""
    # Authorization Resource: auth.
    # This object holds the offered challenges by the server and their status.
    auth_list = order.authorizations

    for auth in auth_list:
        # Choosing challenge.
        # auth.body.challenges is a set of ChallengeBody objects.
        for i in auth.body.challenges:
            # Find the supported challenge.
            if isinstance(i.chall, challenges.DNS01):
                return i

    raise Exception('DNS-01 challenge was not offered by the CA server.')


class ACMEClient:
    def __init__(self, config: AppConfig):
        self.config = config
        self.reg_res = RegistrationResource()
        self.acc_file_path = Path(self.config.data_dir).joinpath(ACME_ACCOUNT_FILENAME)
        self.acc_key_path = Path(self.config.data_dir).joinpath(ACME_ACCOUNT_KEY_FILENAME)

        self.acc_key: typing.Optional[jose.JWKRSA] = None

        self.client: typing.Optional[client.ClientV2] = None

    def new_csr_comp(self, domain_name: str, pkey_pem=None):
        """Create certificate signing request."""
        if pkey_pem is None:
            # Create private key.
            pkey = OpenSSL.crypto.PKey()
            pkey.generate_key(OpenSSL.crypto.TYPE_RSA, self.config.cert_pkey_bits)
            pkey_pem = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM,
                                                      pkey)
        csr_pem = crypto_util.make_csr(pkey_pem, [f'*.{domain_name}', domain_name])
        return pkey_pem, csr_pem

    def perform_dns01(self, domain: str, chl, order):
        """Set up standalone webserver and perform HTTP-01 challenge."""

        response, validation = chl.response_and_validation(self.client.net.key)

        dns_client = Client(self.config.access_key_id, self.config.access_key_secret)
        record_id = dns_client.set_challenge_dns(domain, self.config.rr, self.config.type, validation, self.config.ttl)
        try:
            # Let the CA server know that we are ready for the challenge.
            log.info('Answer challenge')
            self.client.answer_challenge(chl, response)

            # Wait for challenge status and then issue a certificate.
            # It is possible to set a deadline time.
            log.info('Poll and finalize')
            finalized_order = self.client.poll_and_finalize(order)
            dns_client.clean_challenge_dns(record_id)
        except Exception as err:
            dns_client.clean_challenge_dns(record_id)
            log.critical(err)
            exit(os.EX_SOFTWARE)

        return bytes(finalized_order.fullchain_pem, encoding='utf-8')

    def create_account(self):
        log.info(f'Create and register new account')

        self.acc_key = jose.JWKRSA(
            key=rsa.generate_private_key(public_exponent=65537,
                                         key_size=self.config.acc_key_bits,
                                         backend=default_backend()))

        net = client.ClientNetwork(self.acc_key, user_agent=self.config.user_agent)
        directory = client.ClientV2.get_directory(self.config.directory_url, net)
        self.client = client.ClientV2(directory, net=net)

        # Terms of Service URL is in client_acme.directory.meta.terms_of_service
        # Registration Resource: reg_res
        # Creates account with contact information.
        email = self.config.email
        log.debug(f'Register with email f{email}')
        self.reg_res = self.client.new_account(
            messages.NewRegistration.from_data(
                email=email, terms_of_service_agreed=True))

    def save_account(self):
        log.info(f'Save acme account to {self.acc_file_path}')
        with open(self.acc_file_path, 'w') as f:
            f.write(self.reg_res.json_dumps(indent=4))

        log.info(f'Save acme account key to {self.acc_key_path}')
        with open(self.acc_key_path, 'w') as f:
            f.write(self.acc_key.json_dumps(indent=4))

    def read_account_file(self) -> bool:
        try:
            log.info(f'Load acme account from file: {self.acc_file_path}')
            with open(self.acc_file_path) as f:
                self.reg_res = RegistrationResource.json_loads(f.read())
                log.debug(f'Loaded acme account: {json.dumps(self.reg_res.to_json(), indent=4)}')
            log.info(f'Load acme account key from file: {self.acc_key_path}')
            with open(self.acc_key_path) as f:
                self.acc_key = jose.JWKRSA.json_loads(f.read())
                log.debug(f'Loaded acme account key: {json.dumps(self.acc_key.to_json(), indent=4)}')
        except FileNotFoundError:
            log.debug(f'Load acme account fail, file not found')
            return False
        return True

    def load_account(self):
        if not self.read_account_file():
            self.create_account()
            self.save_account()

        log.info('Query registration status')
        net = client.ClientNetwork(self.acc_key, user_agent=self.config.user_agent)
        log.debug('Get directory')
        directory = client.ClientV2.get_directory(self.config.directory_url, net)
        self.client = client.ClientV2(directory, net=net)

        # Query registration status.
        self.client.net.account = self.reg_res
        try:
            self.client.query_registration(self.reg_res)
        except messages.Error as err:
            if err.typ == messages.ERROR_PREFIX + 'unauthorized':
                # Status is deactivated.
                log.info('Status is deactivated')
                self.create_account()
                self.save_account()
            if err.typ == messages.ERROR_PREFIX + 'accountDoesNotExist':
                # Status is deactivated.
                log.info('Status is not exist')
                self.create_account()
                self.save_account()
            else:
                raise err

        return self.reg_res

    def issue_cert(self, domain: str):
        # Create domain private key and CSR
        log.info(f'Generate new csr compare for {domain}')
        pkey_pem, csr_pem = self.new_csr_comp(domain)

        # Issue certificate

        log.debug(f'Create new order')
        order = self.client.new_order(csr_pem)

        # Select HTTP-01 within offered challenges by the CA server
        chl = select_dns01_chl(order)

        # The certificate is ready to be used in the variable "fullchain_pem".
        log.debug(f'Perform dns01')
        fullchain_pem = self.perform_dns01(domain, chl, order)

        return pkey_pem, fullchain_pem

    def renew(self, domain: str, pkey_pem: bytes):
        log.info(f'Renew csr compare for {domain}')
        _, csr_pem = self.new_csr_comp(domain, pkey_pem)

        log.debug(f'Create new order')
        order = self.client.new_order(csr_pem)

        chl = select_dns01_chl(order)

        # Performing challenge
        log.debug(f'Perform dns01')
        fullchain_pem = self.perform_dns01(domain, chl, order)

        return pkey_pem, fullchain_pem
