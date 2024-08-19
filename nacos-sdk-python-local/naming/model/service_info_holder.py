import os
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import json
from collections import defaultdict


class ServiceInfoHolder:
    def __init__(self, namespace, notifier_event_scope, properties):
        self.service_info_map = defaultdict(dict)
        self.cache_dir = self.init_cache_dir(namespace, properties)
        self.instances_differ = InstancesDiffer()
        self.failover_reactor = FailoverReactor(self, notifier_event_scope)
        self.push_empty_protection = self.is_push_empty_protect(properties)
        self.notifier_event_scope = notifier_event_scope
        self.load_cache_at_start(properties)

    def init_cache_dir(self, namespace, properties):
        # 根据properties初始化缓存目录
        return os.path.join(properties.get('cache_dir'), namespace)

    def is_load_cache_at_start(self, properties):
        # 根据properties判断是否在启动时加载缓存
        return properties.get('naming_load_cache_at_start', False)

    def is_push_empty_protect(self, properties):
        # 根据properties判断是否保护空推送
        return properties.get('naming_push_empty_protection', False)

    def load_cache_at_start(self, properties):
        if self.is_load_cache_at_start(properties):
            # 从磁盘加载缓存
            pass

    def get_service_info_map(self):
        return self.service_info_map

    def get_service_info(self, service_name, group_name, clusters):
        grouped_service_name = NamingUtils.get_grouped_name(service_name, group_name)
        key = ServiceInfo.get_key(grouped_service_name, clusters)
        return self.service_info_map[key]

    def process_service_info(self, json_str):
        service_info = json.loads(json_str, cls=ServiceInfo.json_decoder)
        service_info.json_from_server = json_str
        return self._process_service_info(service_info)

    def _process_service_info(self, service_info):
        service_key = service_info.key
        if not service_key:
            print("process service info but serviceKey is null")
            return None

        old_service = self.service_info_map.get(service_key)
        if self.is_empty_or_error_push(service_info):
            print("process service info but found empty or error push")
            return old_service

        self.service_info_map[service_key] = service_info
        diff = self.get_service_info_diff(old_service, service_info)
        if not service_info.json_from_server:
            service_info.json_from_server = json.dumps(service_info)

        if diff.has_different():
            print("current ips: {}, service: {} -> {}".format(service_info.ip_count(), service_key, service_info.hosts))

            if not self.failover_reactor.is_failover_switch(service_key):
                # 这里需要实现NotifyCenter.publishEvent的Python对应逻辑
                pass

            # 写入磁盘缓存
            with open(os.path.join(self.cache_dir, service_key), 'w') as f:
                json.dump(service_info.__dict__, f)

        return service_info

    def is_empty_or_error_push(self, service_info):
        return service_info.hosts is None or (self.push_empty_protection and not service_info.validate())

    def get_service_info_diff(self, old_service, new_service):
        return self.instances_differ.do_diff(old_service, new_service)

    def get_cache_dir(self):
        return self.cache_dir

    def is_failover_switch(self):
        return self.failover_reactor.is_failover_switch()

    def get_failover_service_info(self, service_name, group_name, clusters):
        grouped_service_name = NamingUtils.get_grouped_name(service_name, group_name)
        key = ServiceInfo.get_key(grouped_service_name, clusters)
        return self.failover_reactor.get_service(key)

    def shutdown(self):
        print("ServiceInfoHolder do shutdown begin")
        self.failover_reactor.shutdown()
        print("ServiceInfoHolder do shutdown stop")
