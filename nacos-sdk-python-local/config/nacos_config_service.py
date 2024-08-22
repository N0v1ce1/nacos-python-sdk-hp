import copy
import threading
import time
import uuid
from ..common.constants import Constants
from ..common.client_config import ClientConfig
from ..nacos_client import NacosClient
from model.config_proxy import ConfigProxy
from model.config_param import UsageType
from model.config_filter import *
from model.config_param import *
from model.config import *
from ..util.common_util import check_key_param, get_config_cache_key
from ..util.md5_util import md5
from model.config_response import ConfigResponse
from model.config_request import ConfigRequest
from cache.disk_cache import *
from ..transport.model import RpcRequest
from ... import NacosError

perTaskConfigSize = 3000


# 以下为 IConfigFilter 接口的 Python 版本示例，具体实现根据实际需要进行


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


class ConfigClient(NacosClient):
    def __init__(self, logger,
                 log_file: str,
                 client_config: ClientConfig,
                 config_filter_chain_manager: ConfigFilterChain,
                 config_proxy: ConfigProxy,
                 config_cache_dir: str,
                 uid: str,
                 listen_execute):
        super().__init__(client_config, log_file)
        self.logger = logger
        self.config_filter_chain_manager = config_filter_chain_manager
        self.config_proxy = config_proxy
        self.config_cache_dir = config_cache_dir
        self.last_all_sync_time = time.time()
        self.cache_map = []
        self.uid = uid
        self.listen_execute = listen_execute

    @staticmethod
    def new_config_client(logger,
                          log_file: str,
                          client_config: ClientConfig,
                          config_filter_chain_manager: ConfigFilterChain,
                          config_proxy: ConfigProxy,
                          config_cache_dir: str,
                          uid: str,
                          listen_execute):
        return ConfigClient(logger,
                            log_file,
                            client_config,
                            config_filter_chain_manager,
                            config_proxy,
                            config_cache_dir,
                            uid,
                            listen_execute)

    def get_config_filter_chain_manager(self):
        return self.config_filter_chain_manager

    def set_config_filter_chain_manager(self, manager):
        self.config_filter_chain_manager = manager

    def get_local_configs(self):
        return self.local_configs

    def set_local_configs(self, configs):
        self.local_configs = configs

    def get_config_proxy(self):
        return self.config_proxy

    def set_config_proxy(self, proxy):
        self.config_proxy = proxy

    def get_config_cache_dir(self):
        return self.config_cache_dir

    def set_config_cache_dir(self, dir_path):
        self.config_cache_dir = dir_path

    def get_last_all_sync_time(self):
        return self.last_all_sync_time

    def get_cache_map(self):
        return self.cache_map

    def set_cache_map(self, cache_map):
        self.cache_map = cache_map

    def get_uid(self):
        return self.uid

    def set_uid(self, uid):
        self.uid = uid

    def get_listen_execute(self):
        return self.listen_execute

    def set_listen_execute(self, execute):
        self.listen_execute = execute


class ConfigService:
    """配置服务接口，用于获取和监听配置信息，以及发布配置"""
    UP = "UP"
    DOWN = "DOWN"

    def __init__(self, logger, client_config, rpc_client, nacos_client, config_proxy) -> None:
        self.logger = logger
        self.lock = threading.Lock()
        self.config_filter_chain_manager = new_config_filter_chain_manager()
        self.nacos_client = nacos_client
        self.client_config = client_config
        self.config_proxy = config_proxy
        self.rpc_client = rpc_client
        self.config_cache_dir = os.path.join(self.nacos_client.client_config.cache_dir, "config")
        self.listen_execute = threading.Event()  # 改
        self.namespace_id = client_config.namespace_id
        self.config_client = self.get_config_client()
        self.cache_map = self.config_client.cache_map

    def get_config_client(self):
        self.start_internal()
        return ConfigClient.new_config_client(self.logger,
                                              None,
                                              self.client_config,
                                              self.config_filter_chain_manager,
                                              self.config_proxy,
                                              self.config_cache_dir,
                                              str(uuid.uuid4()),
                                              self.listen_execute)

    def get_config(self, param: ConfigParam):
        """获取配置信息, 过滤response"""
        content, encrypted_data_key, err_msg = self._get_config_inner(param)
        if err_msg is not None:
            return "", err_msg
        deep_copy = copy.deepcopy(param)
        deep_copy.encrypted_data_key = encrypted_data_key
        deep_copy.content = content
        deep_copy.type = UsageType.response_type
        try:
            self.config_filter_chain_manager.do_filters(deep_copy)
        except Exception as e:
            return "", str(e)
        return content, None

    def _get_config_inner(self, param: ConfigParam):
        if not param.group:
            param.group = Constants.DEFAULT_GROUP
        check_key_param(param.data_id, param.group)

        cache_key = get_config_cache_key(param.data_id, param.group, self.namespace_id)
        content = get_failover(cache_key, self.config_client.config_cache_dir, self.logger)

        if content:
            self.logger.warning(f"{self.namespace_id} {param.group} {param.data_id} is using failover content!")
            encrypted_data_key = get_failover_encrypted_data_key(cache_key, self.config_client.config_cache_dir,
                                                                 self.logger)
            return content, encrypted_data_key

        # 这里要对齐下log如何实现的传errorMsg
        response, logger_msg = self.config_proxy.query_config(param.data_id, param.group, self.namespace_id,
                                                              self.client_config.timeout_ms, False, self.nacos_client)
        if logger_msg is not None:
            self.logger.error(
                f"get config from server error:{logger_msg}, dataId:{param.data_id}, group:{param.group}, namespaceId:{self.namespace_id}")
            if self.client_config.disable_use_snap_shot:
                return "", "", self.logger.error(
                    f"get config from remote nacos server fail, and is not allowed to read local file, err:{logger_msg}")
            cache_content, cache_err = read_config_from_file(cache_key, self.config_client.config_cache_dir)
            if cache_err is not None:
                return "", "", self.logger.error(
                    f"read config from both server and cache fail, err={cache_err}, dataId={param.data_id}, group={param.group}, namespaceId={self.namespace_id}")
            if not param.data_id.startswith(Constants.CipherPrefix):
                return cache_content, "", None
            encrypted_data_key, cache_err = read_encrypted_data_key_from_file(cache_key,
                                                                              self.config_client.config_cache_dir)
            return cache_content, encrypted_data_key, None
        if response and response.Response is not None and not response.is_success():
            return response.content, response.encrypted_data_key, response.get_message()
        encrypted_data_key = response.encrypted_data_key
        content = response.content
        return content, encrypted_data_key, None

    def add_listener(self, listeners, param: ConfigParam) -> None:
        """为指定的配置添加监听器，当服务器修改配置后，客户端将使用传入的监听器进行回调"""
        if not param.data_id:
            self.logger.error("[client.ListenConfig] DataId cannot be empty")
            return None
        if not param.group:
            self.logger.error("[client.ListenConfig] Group cannot be empty")
            return None

        if self.config_client is None:
            self.logger.error("[checkConfigInfo.GetClientConfig] failed")
            return None

        key = get_config_cache_key(param.data_id, param.group, self.namespace_id)

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
                data_id=param.data_id,
                group=param.group,
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
            with self.lock:
                self.cache_map[key] = cache_data

    def publish_config(self, param: ConfigParam) -> bool:
        """发布配置信息"""

        if not param.data_id:
            self.logger.errors("[client.PublishConfig] data_id can not be empty")
            return False

        if not param.content:
            self.logger.errors("[client.PublishConfig] content can not be empty")
            return False

        if not param.group:
            param.group = Constants.DEFAULT_GROUP

        request = ConfigRequest.new_config_request(
            param.group, param.data_id, self.namespace_id,
            param.content, param.cas_md5)
        request.addition_map["tag"] = param.tag
        request.addition_map["appName"] = param.app_name
        request.addition_map["betaIps"] = param.beta_ips
        request.addition_map["type"] = param.type
        request.addition_map["src_user"] = param.src_user
        request.addition_map["encryptedDataKey"] = param.encrypted_data_key

        self.config_filter_chain_manager.do_filters(request)

        response = self.config_proxy.request_proxy(self.rpc_client, request, Constants.DEFAULT_TIMEOUT_MILLS)

        if response:
            return True

        return False

    def remove_config(self, param: ConfigParam):
        """移除配置信息"""
        if not param.data_id:
            self.logger.error("[client.DeleteConfig] param.dataId can not be empty")

        if not param.group:
            param.group = Constants.DEFAULT_GROUP

        request = RpcRequest.remove_request(param.group, param.data_id, self.namespace_id)

        rpc_client = self.config_proxy.get_rpc_client(self)

        response = self.config_proxy.request_proxy(rpc_client, request, Constants.DEFAULT_TIMEOUT_MILLS)
        if response is not None:
            return self._build_response(response)
        else:
            self.logger.error("Response is None")
            return False

    def remove_listener(self, listener: Listener, param: ConfigParam):
        """移除指定的监听器"""
        if self.nacos_client.get_client_config is None:
            self.logger.error("get config info failed")
            return
        with self.lock:
            self.cache_map.remove_tenant_listener(get_config_cache_key(param.data_id, param.group, self.namespace_id),
                                                  listener)
        return

    def add_config_filter(self, config_filter: 'IConfigFilter') -> None:
        """
        大工程，和listen_execute、config_filter_chain_manager
        """
        raise NotImplementedError

    def search_config(self, param: SearchConfigParam):
        return self._search_config_inner(param)

    def _search_config_inner(self, param: SearchConfigParam) -> ConfigPage:
        if param.search not in ["accurate", "blur"]:
            raise ValueError("[client.searchConfigInner] param.search must be 'accurate' or 'blur'")

        param.page_no = max(1, param.page_no)
        param.page_size = max(1, param.page_size)

        try:
            config_items = self.config_proxy.search_config_proxy(
                param, self.client_config.namespace_id, self.client_config.access_key, self.client_config.secret_key
            )
        except Exception as err:
            self.logger.error(f"search config from server error: {err}")

            # 假设 err 是 NacosError 类型
            if isinstance(err, NacosError):
                if err.error_code == "404":
                    raise FileNotFoundError("config not found")
                if err.error_code == "403":
                    raise PermissionError("get config forbidden")
            raise

        return config_items

    def shut_down(self):
        """关闭资源服务"""
        self.config_proxy.get_rpc_client.shutdown()
        self.config_proxy.shut_down()

    def _build_response(self, response):
        if response.is_success():
            return True
        err_msg = response.get_message()
        self.logger.error(err_msg)
        return False

    # 下面是listener的逻辑，待确认
    def start_internal(self):
        pass

    def execute_config_listen(self):
        pass

    def build_config_batch_listen_request(self):
        pass

    def refresh_content_and_check(self):
        pass

    def build_listen_task(self):
        pass
