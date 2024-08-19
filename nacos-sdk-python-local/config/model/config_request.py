from abc import ABC, abstractmethod
from ...common.model.request import Request
from .config import ConfigListenContext 

class IConfigRequest(ABC):

    @abstractmethod
    def get_data_id(self):
        pass

    @abstractmethod
    def get_group(self):
        pass

    @abstractmethod
    def get_tenant(self):
        pass


class ConfigRequest(Request):
    def __init__(self, group, data_id, tenant, content, md5_str):
        super().__init__()
        self.ResultType = None
        self.Content = content
        self.md5_str = md5_str
        self.Group = group
        self.DataId = data_id
        self.Tenant = tenant
        self.Module = "config"

    @staticmethod
    def new_config_request(group, data_id, tenant, content, md5_str):
        return ConfigRequest(group, data_id, tenant, content, md5_str)

    def get_data_id(self):
        return self.DataId

    def get_group(self):
        return self.Group

    def get_tenant(self):
        return self.Tenant

    def get_content(self):
        return self.Content

    def set_data_id(self, data_id):
        self.DataId = data_id

    def set_tenant(self, tenant):
        self.Tenant = tenant

    def set_group(self, group):
        self.Group = group

    def set_content(self, content):
        self.Content = content

    def set_type(self, result_type):
        self.ResultType = result_type

class ConfigBatchListenRequest(ConfigRequest):
    def __init__(self, cache_len):
        super().__init__("", "", "")  
        self.listen = True
        self.config_listen_contexts = [ConfigListenContext() for _ in range(cache_len)]  

    @staticmethod
    def new_config_batch_listen_request(cache_len):
        return ConfigBatchListenRequest(cache_len)

    def GetRequestType(self):
        return "ConfigBatchListenRequest"

class ConfigChangeNotifyRequest(ConfigRequest):
    def __init__(self, group, data_id, tenant):
        super().__init__(group, data_id, tenant) 

    @staticmethod
    def new_config_change_notify_request(group, data_id, tenant):
        return ConfigChangeNotifyRequest(group, data_id, tenant)

    def get_request_type(self):
        return "ConfigChangeNotifyRequest"

class ConfigQueryRequest(ConfigRequest):
    def __init__(self, group, data_id, tenant, tag):
        super().__init__(group, data_id, tenant)
        self.tag = tag

    @staticmethod
    def new_config_query_request(group, data_id, tenant, tag):
        return ConfigQueryRequest(group, data_id, tenant, tag)

    def get_request_type(self):
        return "ConfigQueryRequest"

class ConfigPublishRequest(ConfigRequest):
    def __init__(self, group, data_id, tenant, content, cas_md5, addition_map=None):
        super().__init__(group, data_id, tenant)
        self.content = content
        self.cas_md5 = cas_md5
        self.addition_map = addition_map if addition_map is not None else {}

    @staticmethod
    def new_config_publish_request(group, data_id, tenant, content, cas_md5):
        return ConfigPublishRequest(group, data_id, tenant, content, cas_md5)

    def get_request_type(self):
        return "ConfigPublishRequest"

class ConfigRemoveRequest(ConfigRequest):
    def __init__(self, group, data_id, tenant):
        super().__init__(group, data_id, tenant)

    @staticmethod
    def new_config_remove_request(group, data_id, tenant):
        return ConfigRemoveRequest(group, data_id, tenant)

    def get_request_type(self):
        return "ConfigRemoveRequest"