import threading
import time
import uuid
from idlelib.rpc import RPCClient
from typing import Optional
from ..common.constants import Constants
from ..nacos_client import NacosClient
from ..util.common_util import check_key_param, get_config_cache_key
from ..util.md5_util import md5
from model.config_response import ConfigResponse
from model.config_request import ConfigRequest
from cache.disk_cache import *
from ..transport.model import RpcRequest

perTaskConfigSize = 3000


# 以下为 IConfigFilter 接口的 Python 版本示例，具体实现根据实际需要进行
class IConfigFilter:
    """配置过滤器接口，用于对获取的配置进行过滤处理，例如配置内容的解密等"""

    def filter(self, config_info: str) -> str:
        """对配置信息进行过滤处理"""
        raise NotImplementedError


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


class ConfigClient:
    def __init__(self, logger):
        self.logger = logger
        # self.cancel = lambda : None
        self.nacos_client = None
        self.config_filter_chain_manager = None
        self.local_configs = None
        self.config_proxy = None
        self.config_cache_dir = None
        self.last_all_sync_time = time.time()
        self.cache_map = {}
        self.uid = None
        self.listen_execute = None



class ConfigService:
    """配置服务接口，用于获取和监听配置信息，以及发布配置"""
    UP = "UP"
    DOWN = "DOWN"

    def __init__(self, logger, properties, rpc_client, nacos_client) -> None:
        self.logger = logger
        self.config_filter_chain_manager = filter.ConfigFilterChainManager()
        self.nacos_client = nacos_client
        self.rpc_client = rpc_client
        self.config_proxy = None
        self.config_client = self.get_config_client()
        self.cache_map = None
        self.config_cache_dir = None
        self.listen_execute = threading.Event()  # 改
        self.namespace_id = properties.namespace_id

    def get_config_client(self):
        config_client = ConfigClient(self.logger)
        config_client.nacos_client = self.nacos_client
        config_client.config_proxy = self.config_client.nacos_client.config_proxy
        config_client.config_filter_chain_manager = self.config_filter_chain_manager
        config_client.config_cache_dir = self.config_cache_dir
        config_client.uid = uuid.uuid4()
        config_client.listen_execute = self.listen_execute
        self.start_internal()
        return config_client

    def get_config(self, data_id, group, timeout_ms):
        """获取配置信息, 过滤response"""
        content, encrypted_data_key, err_msg = self._get_config_inner(data_id, group, timeout_ms)
        if err_msg is not None:
            return "", err_msg
        config_response = ConfigResponse()
        config_response.set_data_id(data_id)
        config_response.set_tenant(self.namespace_id)
        config_response.set_group(group)
        config_response.set_content(content)
        config_response.set_encrypted_data_key(encrypted_data_key)
        self.config_filter_chain_manager.do_filter(config_response)
        return content, None

    def _get_config_inner(self, data_id, group, timeout_ms):
        group = self._blank_to_default_group(group)
        check_key_param(data_id, group)

        cache_key = get_config_cache_key(data_id, group, self.namespace_id)
        content = get_failover(cache_key, self.config_client.config_cache_dir, self.logger)

        if len(content) > 0:
            self.logger.warning(f"{self.namespace_id} {group} {data_id} is using failover content!")
            encrypted_data_key = get_failover_encrypted_data_key(cache_key, self.config_client.config_cache_dir,
                                                                 self.logger)
            return content, encrypted_data_key

        # 这里要对齐下log如何实现的传errorMsg
        response, logger_msg = self.config_proxy.query_config(data_id, group, self.namespace_id,
                                                              timeout_ms, False, self.nacos_client)
        if logger_msg is not None:
            self.logger.error(
                f"get config from server error:{logger_msg}, dataId:{data_id}, group:{group}, namespaceId:{self.namespace_id}")
            if self.config_client.disable_use_snap_shot:
                return "", "", self.logger.error(
                    f"get config from remote nacos server fail, and is not allowed to read local file, err:{logger_msg}")
            cache_content, cache_err = read_config_from_file(cache_key, self.config_client.config_cache_dir)
            if cache_err is not None:
                return "", "", self.logger.error(
                    f"read config from both server and cache fail, err={cache_err}, dataId={data_id}, group={group}, namespaceId={self.namespace_id}")
            if not data_id.startswith(Constants.CipherPrefix):
                return cache_content, "", None
            encrypted_data_key, cache_err = read_encrypted_data_key_from_file(cache_key,
                                                                              self.config_client.config_cache_dir)
            return cache_content, encrypted_data_key, None
        if response and response.Response is not None and not response.is_success():
            return response.content, response.encrypted_data_key, response.get_message()
        encrypted_data_key = response.encrypted_data_key
        content = response.content
        return content, encrypted_data_key, None

    def add_listener(self, data_id, group, listeners) -> None:
        """为指定的配置添加监听器，当服务器修改配置后，客户端将使用传入的监听器进行回调"""
        if not data_id:
            self.logger.error("[client.ListenConfig] DataId cannot be empty")
            return None
        if not group:
            self.logger.error("[client.ListenConfig] Group cannot be empty")
            return None

        if self.config_client is None:
            self.logger.error("[checkConfigInfo.GetClientConfig] failed")
            return None

        key = get_config_cache_key(data_id, group, self.namespace_id)

        if key in self.cache_map:
            c_data = self.cache_map[key]
            c_data.is_initializing = True
        else:
            content = read_config_from_file(key, self.config_cache_dir)
            if not content:
                self.logger.warning("Failed to read config from file")
                return None

            encrypted_data_key = read_encrypted_data_key_from_file(key, self.config_cache_dir)
            md5_str = md5(content) if content else ''

            cache_data = CacheData(
                is_initializing=True,
                data_id=data_id,
                group=group,
                tenant=self.namespace_id,
                content=content,
                md5_str=md5_str,
                encrypted_data_key=encrypted_data_key,
                task_id=len(self.cache_map) // perTaskConfigSize,
                config_client=self
            )

            for listener in listeners:
                cache_data.listeners.append(listener)

            # 刷新缓存
            self.cache_map[key] = cache_data

    def publish_config(self, data_id, group, content, result_type, cas_md5, tag, app_name, beta_ips, src_user,
                       encrypted_data_key) -> bool:
        """发布配置信息"""

        if not data_id:
            self.logger.errors("[client.PublishConfig] data_id can not be empty")
            return False

        if not content:
            self.logger.errors("[client.PublishConfig] content can not be empty")
            return False

        if not group:
            group = Constants.DEFAULT_GROUP

        request = ConfigRequest.new_config_request(
            group, data_id, self.config_client.namespace_id,
            content, cas_md5)
        request.addition_map["tag"] = tag
        request.addition_map["appName"] = app_name
        request.addition_map["betaIps"] = beta_ips
        request.addition_map["type"] = result_type
        request.addition_map["src_user"] = src_user
        request.addition_map["encryptedDataKey"] = encrypted_data_key

        self.config_filter_chain_manager.do_filter(request)

        response = self.config_proxy.request_proxy(self.rpc_client, request, Constants.DEFAULT_TIMEOUT_MILLS)

        if response:
            return True

        return False

    def remove_config(self, data_id, group):
        """移除配置信息"""
        if len(data_id) <= 0:
            self.logger.error("[client.DeleteConfig] param.dataId can not be empty")

        if len(group) <= 0:
            group = Constants.DEFAULT_GROUP

        request = RpcRequest.remove_request(group, data_id, self.config_client.namespace_id)

        rpc_client = self.config_proxy.get_rpc_client(self)

        response = self.config_proxy.request_proxy(rpc_client, request, Constants.DEFAULT_TIMEOUT_MILLS)
        if response is not None:
            return self._build_response(response)
        else:
            self.logger.error("Response is None")
            return False

    def remove_listener(self, data_id: str, group: str, listener: Listener):
        """移除指定的监听器"""
        if self.config_client.get_config is None:
            self.logger.error("get config info failed")
            return
        self.cache_map.remove_tenant_listener(get_config_cache_key(data_id, group, self.namespace_id),
                                              listener)
        return

    def add_config_filter(self, config_filter: 'IConfigFilter') -> None:
        """
        大工程，和listen_execute、config_filter_chain_manager
        """
        raise NotImplementedError

    def search_config(self):
        """
        go里有但是没有用到，不知道是否要写
        """
        pass

    def shut_down(self):
        """关闭资源服务"""
        self.config_proxy.get_rpc_client.shutdown()
        self.config_proxy.shut_down()

    def _blank_to_default_group(self, group):
        return group.strip() if group else Constants.DEFAULT_GROUP

    def _build_response(self, response):
        if response.is_success():
            return True
        err_msg = response.get_message()
        self.logger.error(err_msg)
        return False

    def start_internal(self):
        pass


class CacheData:
    def __init__(self, is_initializing, data_id, group, tenant, content, md5_str, encrypted_data_key, task_id,
                 config_client, listeners=None):
        self.is_initializing = is_initializing
        self.data_id = data_id
        self.group = group
        self.tenant = tenant
        self.content = content
        self.md5 = md5_str
        self.listeners = listeners
        self.encrypted_data_key = encrypted_data_key
        self.task_id = task_id
        self.config_client = config_client
