from abc import ABC, abstractmethod
from typing import List
import heapq


class IConfigFilterChain(ABC):
    @abstractmethod
    def add_filter(self, filter):
        pass

    @abstractmethod
    def get_filters(self):
        pass

    @abstractmethod
    def do_filters(self, config_param):
        pass

    @abstractmethod
    def do_filter_by_name(self, config_param, name):
        pass


class IConfigFilter(ABC):
    @abstractmethod
    def do_filter(self, config_param):
        pass

    @abstractmethod
    def get_order(self):
        pass

    @abstractmethod
    def get_filter_name(self):
        pass


class ConfigFilterChain:
    def __init__(self):
        self.config_filters = []

    def add_filter(self, conf_filter: IConfigFilter) -> None:
        for existing_filter in self.config_filters:
            if conf_filter.get_filter_name() == existing_filter.get_filter_name():
                return
        for i, existing_filter in enumerate(self.config_filters):
            if conf_filter.get_order() < existing_filter.get_order():
                self.config_filters.insert(i, conf_filter)
                return
        self.config_filters.append(conf_filter)

    # 考虑用python优先队列会不会好点

    def get_filters(self) -> List['IConfigFilter']:
        return self.config_filters

    def do_filters(self, param) -> None:
        for config_filter in self.config_filters:
            config_filter.do_filter(param)

    def do_filter_by_name(self, param, name: str) -> None:
        for config_filter in self.config_filters:
            if config_filter.get_filter_name() == name:
                config_filter.do_filter(param)
                return
        raise ValueError(f"Cannot find the filter with name {name}")


# 注册过滤器到链的函数
def register_config_filter_to_chain(chain: 'ConfigFilterChain', config_filter: 'IConfigFilter') -> None:
    chain.add_filter(config_filter)


# 创建配置过滤器链管理器的函数
def new_config_filter_chain_manager() -> 'ConfigFilterChain':
    return ConfigFilterChain()
