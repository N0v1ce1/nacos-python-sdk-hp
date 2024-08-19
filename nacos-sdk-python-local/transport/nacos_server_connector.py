import json
import sched
import threading
from concurrent.futures import ThreadPoolExecutor
from random import randrange

import time
import uuid
import hmac
import hashlib
import base64
from typing import List, Dict, Optional

from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM, SERVER_ERROR
from v2.nacos.common.client_config import ClientConfig
from v2.nacos.naming.util.naming_client_util import get_group_name
from v2.nacos.utils.common_util import get_current_time_millis
from v2.nacos.transport.auth_client import AuthClient
from v2.nacos.transport.http_agent import HttpAgent


def _choose_random_index(upper_limit: int):
    return randrange(0, upper_limit)


class NacosServerConnector:
    def __init__(self, logger, client_config: ClientConfig, http_agent: HttpAgent):
        self.logger = logger

        if len(client_config.server_list) == 0 and not client_config.endpoint:
            raise NacosException(INVALID_PARAM, "both server list and endpoint are empty")

        self.client_config = client_config
        self.server_list = client_config.server_list
        self.current_index = 0
        self.http_agent = http_agent
        self.endpoint = client_config.endpoint

        self.server_src_change_signal = threading.Event()
        self.server_list_lock = threading.Lock()
        if len(self.server_list) == 0:
            self._get_server_list_from_endpoint()
            self.last_server_list_refresh_time = 0
            self.refresh_server_list_executor = ThreadPoolExecutor(max_workers=1)
            self.timer = sched.scheduler(time.time, time.sleep)
            self.refresh_server_list_internal = 30  # second
            self.timer.enter(self.refresh_server_list_internal, 0, self._refresh_server_srv_if_need)
            self.refresh_server_list_executor.submit(self.timer.run)

        if len(self.server_list) == 0:
            raise NacosException(INVALID_PARAM, "server list is empty")

        self.current_index = _choose_random_index(len(self.server_list))
        self.auth_client = AuthClient(self.logger, client_config, self.get_server_list, http_agent)
        self.auth_client.get_access_token(True)

    def _get_server_list_from_endpoint(self) -> Optional[List[str]]:

        if self.endpoint is None or self.endpoint.strip() == "":
            return None

        url = self.endpoint.strip() + self.client_config.endpoint_context_path + "/serverlist"
        response, err = self.http_agent.request(url, "GET", None, None, None)
        if err:
            self.logger.error("[get-server-list] get server list from endpoint failed,url:%s, err:%s", url, err)
            return None
        else:
            self.logger.debug("[get-server-list] content from endpoint,url:%s,response:%s", url, response)
            server_list = []
            if response:
                for server_info in response.decode('utf-8').strip().split("\n"):
                    sp = server_info.strip().split(":")
                    if len(sp) == 1:
                        server_list.append((sp[0] + ":" + Constants.DEFAULT_PORT))
                    else:
                        server_list.append(server_info)

                if len(server_list) != 0 and set(server_list) == set(self.server_list):
                    with self.server_list_lock:
                        old_server_list = self.server_list
                        self.server_list = server_list
                        self.logger.info("[refresh server list] nacos server list is updated from %s to %s",
                                         str(old_server_list), str(server_list))
        return server_list

    def _refresh_server_srv_if_need(self):
        if self.server_list:
            self.logger.debug("server list provided by user: " + str(self.server_list))
            return

        if get_current_time_millis() - self.last_server_list_refresh_time < self.refresh_server_list_internal:
            return

        server_list = self._get_server_list_from_endpoint()

        if not server_list:
            self.logger.warning("failed to get server list from endpoint, endpoint: " + self.endpoint)

        self.last_server_list_refresh_time = get_current_time_millis()

    def call_config_server(self, api: str, params: Dict[str, str], new_headers: Dict[str, str], method: str,
                           cur_server: str, context_path: Optional[str], timeout_ms: int):
        # Logic for calling the server for configuration
        pass

    def req_api(self, url: str, headers=None, params=None, data=None, method="GET"):
        servers = self.get_server_list()
        if servers is None or len(servers) == 0:
            raise NacosException(INVALID_PARAM, "server list is empty")

        all_headers = {}
        if headers:
            all_headers.update(headers)
        all_params = {}
        if params:
            all_params.update(params)

        self._inject_security_info(all_params)
        self._inject_naming_params_sign(all_params, data)

        if len(servers) == 1:
            for i in range(Constants.MAX_RETRY):
                try:
                    return self._call_server(servers[0], url, params, method)
                except Exception as e:
                    self.logger.error(
                        "[req_api] api:%s, method:%s, params:%s call server error: %s", url, method,
                        {json.dumps(params)}, e)
        else:
            index = randrange(len(servers))
            for _ in range(len(servers)):
                current_server = servers[index]
                try:
                    return self._call_server(current_server, url, params, method)
                except Exception as e:
                    self.logger.error(
                        "[req_api] api:%s, method:%s, params:%s call server error: %s", url, method,
                        {json.dumps(params)}, e)
                    index = (index + 1) % len(servers)

        raise NacosException(SERVER_ERROR, f"failed to request api after {Constants.MAX_RETRY} tries")

    def _call_server(self, current_server: str, url: str, params: Dict[str, str], method: str):
        context_path = self.client_config.context_path if self.client_config.context_path != '' else Constants.WEB_CONTEXT
        url = current_server + context_path + url
        # 设置HTTP请求的头部信息
        headers = {
            'Client-Version': Constants.CLIENT_VERSION,
            'User-Agent': Constants.CLIENT_VERSION,
            'Connection': 'Keep-Alive',
            'RequestId': str(uuid.uuid4()),
            'Request-Module': 'Naming',
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        }
        response, error = self.http_agent.request(url, method, headers=headers, params=params)
        if error is not None:
            raise NacosException(response.status_code, response.text)
        return response

    def get_server_list(self):
        return self.server_list

    def get_next_server(self):
        if not self.server_list:
            raise ValueError('server list is empty')
        self.current_index = (self.current_index + 1) % len(self.server_list)
        return self.server_list[self.current_index]

    def _inject_security_info(self, params):
        if self.client_config.username and self.client_config.password:
            access_token = self.auth_client.get_access_token(False)
            params[Constants.ACCESS_TOKEN] = access_token

    def _inject_naming_params_sign(self, params, data):
        if self.client_config.access_key is None or self.client_config.secret_key is None:
            return

        if not params and not data:
            return

        timeStamp = str(int(time.time() * 1000))
        params_to_sign = params or data or {}
        group = params_to_sign.get(Constants.GROUP_NAME_KEY)
        service_name = params_to_sign.get(Constants.SERVICE_NAME_KEY)

        if service_name:
            if Constants.SERVICE_INFO_SPLITER in service_name or group is None or group == "":
                sign_str = service_name
            else:
                sign_str = get_group_name(group, service_name)
            sign_str = timeStamp + Constants.SERVICE_INFO_SPLITER + sign_str
        else:
            sign_str = timeStamp

        params.update({
            "ak": self.client_config.access_key,
            "data": sign_str,
            "signature": self.__do_sign(sign_str, self.client_config.secret_key),
        })

    @staticmethod
    def __do_sign(sign_str, sk):
        return base64.encodebytes(
            hmac.new(sk.encode(), sign_str.encode(), digestmod=hashlib.sha1).digest()).decode().strip()
