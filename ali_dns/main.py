# -*- coding: utf-8 -*-
import json
import logging
import os

from alibabacloud_alidns20150109 import models as alidns_20150109_models
from alibabacloud_alidns20150109.client import Client as Alidns20150109Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models

LANG = 'zh'

log = logging.getLogger(__name__)


class Client:
    def __init__(self, access_key_id: str, access_key_secret: str):
        self.client = Client.create_client(access_key_id, access_key_secret)
        self.runtime = util_models.RuntimeOptions()

    @staticmethod
    def create_client(access_key_id: str, access_key_secret: str, ) -> Alidns20150109Client:
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        log.debug(f"Create client with access key id: {access_key_id[:8]}..."
                  f" access key secret {access_key_secret[:8]}...")
        config = open_api_models.Config(
            # 必填，您的 AccessKey ID,
            access_key_id=access_key_id,
            # 必填，您的 AccessKey Secret,
            access_key_secret=access_key_secret
        )
        # 访问的域名
        config.endpoint = f'alidns.cn-beijing.aliyuncs.com'
        return Alidns20150109Client(config)

    def find_records_by_type(self, domain: str, type_name: str):
        log.debug(f'Find records domain name: {domain}, type: {type_name}')
        describe_domain_records_request = alidns_20150109_models.DescribeDomainRecordsRequest(
            domain_name=domain, lang=LANG, type=type_name)

        try:
            response = self.client.describe_domain_records_with_options(describe_domain_records_request, self.runtime)
            log.debug(f'Found {len(response.body.domain_records.record)} records')
        except Exception as err:
            log.critical(err)
            exit(os.EX_SOFTWARE)
        return response.body.domain_records.record

    def add_record(self, domain: str, rr: str, type_name: str, value: str, ttl: int) -> str:
        log.info(f'Add record, domain name: {domain}, rr {rr}, type: {type_name}, value: {value[:8]}..., ttl: {ttl}')
        add_domain_record_request = alidns_20150109_models.AddDomainRecordRequest(
            domain_name=domain, rr=rr, type=type_name, lang=LANG, value=value, ttl=ttl)

        try:
            response = self.client.add_domain_record_with_options(add_domain_record_request, self.runtime)
        except Exception as err:
            log.critical(err)
            exit(os.EX_SOFTWARE)
        log.debug(f'Add done, record id: {response.body.record_id}')
        return response.body.record_id

    def delete_record(self, record_id: str) -> None:
        log.info(f'Delete record, record id: {record_id}')

        delete_domain_record_request = alidns_20150109_models.DeleteDomainRecordRequest(
            record_id=record_id, lang=LANG)

        try:
            self.client.delete_domain_record_with_options(delete_domain_record_request, self.runtime)
        except Exception as err:
            log.critical(err)
            exit(os.EX_SOFTWARE)

    def update_record(self, record_id: str, rr: str, type_name: str, value: str, ttl: int) -> None:
        log.info(f'Update record, rr {rr}, type: {type_name}, value: {value[:8]}..., ttl: {ttl}')
        update_domain_record_request = alidns_20150109_models.UpdateDomainRecordRequest(
            lang=LANG, record_id=record_id, rr=rr, type=type_name, value=value, ttl=ttl)

        try:
            self.client.update_domain_record_with_options(update_domain_record_request, self.runtime)
        except Exception as err:
            log.critical(err)
            exit(os.EX_SOFTWARE)

    def find_challenge_records(self, domain: str, rr: str, type_name: str):
        log.info(f'Find record, domain: {domain}, type: {type_name}')
        all_records = self.find_records_by_type(domain, type_name)
        result = list[alidns_20150109_models.DescribeDomainRecordsResponseBodyDomainRecordsRecord]()
        print_result = list()
        for record in all_records:
            if record.rr == rr:
                result.append(record)
                print_result.append(record.to_map())
        log.debug(f'Found record: {json.dumps(print_result, indent=4)}')
        return result

    def set_challenge_dns(self, domain: str, rr: str, type_name: str, value: str, ttl: int) -> str:
        records = self.find_challenge_records(domain, rr, type_name)
        if len(records) == 0:
            record_id = self.add_record(domain, rr, type_name, value, ttl)
        else:
            for r in records[1:]:
                self.delete_record(r.record_id)

            record_id = records[0].record_id
            if records[0].value != value:
                self.update_record(record_id, rr, type_name, value, ttl)

        return record_id

    def clean_challenge_dns(self, record_id: str):
        self.delete_record(record_id)
