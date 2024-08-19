import time
from abc import ABC, abstractmethod

from ...common.constants import Constants
from ...util.common_util import check_key_param, get_config_cache_key
from ..model.config_response import ConfigQueryResponse
from ..model.config_request import ConfigRequest
from ..cache.disk_cache import *
from limiter import *


class IConfigProxy(ABC):

    @abstractmethod
    def query_config(self, data_id: str, group: str, tenant: str, timeout: int, notify: bool, client):
        """
        查询配置的方法。
        :param data_id: 配置的dataId
        :param group: 配置的分组
        :param tenant: 租户标识
        :param timeout: 超时时间（毫秒）
        :param notify: 是否需要通知
        :param client: ConfigClient实例
        :return: 配置查询响应对象和可能发生的错误
        """
        pass

    @abstractmethod
    def search_config_proxy(self, param, tenant, access_key, secret_key: str):
        """
        搜索配置代理的方法。
        :param param: 搜索参数
        :param tenant: 租户标识
        :param access_key: 访问密钥
        :param secret_key: 密钥
        :return: 配置分页对象和可能发生的错误
        """
        pass

    @abstractmethod
    def request_proxy(self, rpc_client, request, timeout_mills: int):
        """
        发送请求到代理的方法。
        :param rpc_client: RpcClient实例
        :param request: 请求对象
        :param timeout_mills: 超时时间（毫秒）
        :return: 响应对象和可能发生的错误
        """
        pass

    @abstractmethod
    def create_rpc_client(self, ctx, task_id: str, client):
        """
        创建RpcClient的方法。
        :param ctx: 上下文对象
        :param task_id: 任务ID
        :param client: ConfigClient实例
        :return: RpcClient实例
        """
        pass

    @abstractmethod
    def get_rpc_client(self, client):
        """
        获取RpcClient的方法。
        :param client: ConfigClient实例
        :return: RpcClient实例
        """
        pass


class ConfigProxy(IConfigProxy, ABC):
    def __init__(self, nacos_server, client_config, logger):
        self.nacos_server = nacos_server
        self.client_config = client_config
        self.logger = logger

    def query_config(self, data_id, group, tenant, timeout, notify, client):
        if not group:
            group = Constants.DEFAULT_GROUP

        config_query_request = ConfigRequest.new_config_request(group, data_id, tenant)
        config_query_request.headers["notify"] = str(notify)

        cache_key = get_config_cache_key(data_id, group, tenant)

        if is_limited(cache_key):
            return None, self.logger.errorMsg("ConfigQueryRequest is limited")

        i_response = self.request_proxy(self.get_rpc_client(client), config_query_request, timeout)
        if i_response is None:
            return None, self.logger.errorMsg("ConfigQueryRequest failed")

        response = i_response
        if not isinstance(response, ConfigQueryResponse):
            return None, self.logger.errorMsg("ConfigQueryRequest returns type error")

        if response.is_success():
            write_config_to_file(cache_key, self.client_config.cache_dir, response.content, self.logger)
            write_encrypted_data_key_to_file(cache_key, self.client_config.cache_dir, response.encrypted_data_key, self.logger)
            if not response.content_type:
                response.content_type = "text"
            return response

        if response.get_error_code() == 300:
            write_config_to_file(cache_key, self.client_config.cache_dir, "", self.logger)
            write_encrypted_data_key_to_file(cache_key, self.client_config.cache_dir, "", self.logger)
            return response

        if response.get_error_code() == 400:
            self.logger.error(
                "[config_rpc_client] [sub-server-error] get server config being modified concurrently, "
                "dataId=%s, group=%s, tenant=%s", data_id, group, tenant)

            return None, self.logger.errorMsg("data being modified, dataId=" + data_id + ",group=" + group + ",tenant=" + tenant)

        if response.get_error_code() > 0:
            self.logger.error("[config_rpc_client] [sub-server-error] "
                          "dataId=%s, group=%s, tenant=%s, code=%+v",
                          data_id, group, tenant, response)

        return response

    def request_proxy(self, rpc_client, request, timeout_millis):
        self.nacos_server.inject_security_info(request.get_headers())
        self._inject_comm_header(request.get_headers())
        self.nacos_server.inject_sk_ak(request.get_headers(), self.client_config)

        sign_headers = self.nacos_server.get_sign_headers_from_request(request, self.client_config.secret_key)
        request.put_all_headers(sign_headers)

        try:
            response = rpc_client.request(request, int(timeout_millis / 1000))
            return response
        except Exception as e:
            return e

    def _inject_comm_header(self, param):
        pass

    def shut_down(self):
        pass

