from datetime import datetime
from typing import List
from ...common.model.response import Response
from .config import ConfigContext


class ConfigChangeBatchListenResponse(Response):

    def __init__(self):
        super().__init__()
        self.changed_configs = []

    @staticmethod
    def new_config_change_batch_listen_response():
        return ConfigChangeBatchListenResponse()

    def get_response_type(self) -> str:
        return "ConfigChangeBatchListenResponse"


class ConfigQueryResponse(Response):

    def __init__(self):
        super().__init__()
        self.content = ""
        self.encrypted_data_key = ""
        self.content_type = ""
        self.md5 = ""
        self.last_modified = 0
        self.is_beta = False
        self.tag = False

    @staticmethod
    def new_config_query_response():
        return ConfigQueryResponse()

    def get_response_type(self) -> str:
        return "ConfigQueryResponse"


class ConfigPublishResponse(Response):

    def __init__(self):
        super().__init__()

    @staticmethod
    def new_config_publish_response():
        return ConfigPublishResponse()

    def get_response_type(self) -> str:
        return "ConfigPublishResponse"


class ConfigRemoveResponse:

    def __init__(self):
        super().__init__()

    @staticmethod
    def new_config_remove_response():
        return ConfigRemoveResponse()

    def get_response_type(self) -> str:
        return "ConfigRemoveResponse"


class ConfigResponse:
    def __init__(self):
        self.param = {}

    def get_tenant(self):
        return self.param.get('TENANT')

    def set_tenant(self, tenant):
        self.param['TENANT'] = tenant

    def get_data_id(self):
        return self.param.get('DATA_ID')

    def set_data_id(self, data_id):
        self.param['DATA_ID'] = data_id

    def get_group(self):
        return self.param.get('GROUP')

    def set_group(self, group):
        self.param['GROUP'] = group

    def get_content(self):
        return self.param.get('CONTENT')

    def set_content(self, content):
        self.param['CONTENT'] = content

    def get_config_type(self):
        return self.param.get('CONFIG_TYPE')

    def set_config_type(self, config_type):
        self.param['CONFIG_TYPE'] = config_type

    def get_encrypted_data_key(self):
        return self.param.get('ENCRYPTED_DATA_KEY')

    def set_encrypted_data_key(self, encrypted_data_key):
        self.param['ENCRYPTED_DATA_KEY'] = encrypted_data_key

    def get_parameter(self, key):
        return self.param.get(key)

    def put_parameter(self, key, value):
        self.param[key] = value

