from typing import Callable, Optional
from enum import Enum


class Listener:
    def __init__(self, executor, config_info):
        self.executor = executor
        self.config_info = config_info

    def get_executor(self):
        if self.executor:
            return self.executor
        else:
            return None

    def receive_config_info(self, config_info):
        pass


# 定义用途类型枚举
class UsageType(Enum):
    request_type = "RequestType"
    response_type = "ResponseType"


class ConfigParam:
    def __init__(self, data_id: str, group: str, content: str,
                 tag: Optional[str] = None, app_name: Optional[str] = None,
                 beta_ips: Optional[str] = None, cas_md5: Optional[str] = None,
                 type: Optional[str] = None, src_user: Optional[str] = None,
                 encrypted_data_key: Optional[str] = None, kms_key_id: Optional[str] = None,
                 usage_type: UsageType = UsageType.request_type,
                 onChange: Optional[Callable[[str, str, str, str], None]] = None):
        self.data_id = data_id
        self.group = group
        self.content = content
        self.tag = tag
        self.app_name = app_name
        self.beta_ips = beta_ips
        self.cas_md5 = cas_md5
        self.type = type
        self.src_user = src_user
        self.encrypted_data_key = encrypted_data_key
        self.kms_key_id = kms_key_id
        self.usage_type = usage_type
        self.on_change = onChange

    def deep_copy(self) -> 'ConfigParam':
        return ConfigParam(**self.__dict__)


class SearchConfigParam:
    def __init__(self, search: Optional[str] = None, data_id: Optional[str] = None,
                 group: Optional[str] = None, tag: Optional[str] = None,
                 app_name: Optional[str] = None, page_no: int = 1,
                 page_size: int = 10):
        self.search = search
        self.data_id = data_id
        self.group = group
        self.tag = tag
        self.app_name = app_name
        self.page_no = page_no
        self.page_size = page_size

