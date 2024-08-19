from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.client_config import TLSConfig
from v2.nacos.common.client_config import KMSConfig


class ClientConfigBuilder:
    def __init__(self):
        self._config = ClientConfig()

    def server_address(self, server_address) -> "ClientConfigBuilder":
        self._config.server_address = server_address
        return self

    def endpoint(self, endpoint) -> "ClientConfigBuilder":
        self._config.endpoint = endpoint
        return self

    def namespace_id(self, namespace_id) -> "ClientConfigBuilder":
        self._config.namespace_id = namespace_id
        return self

    def timeout_ms(self, timeout_ms) -> "ClientConfigBuilder":
        self._config.timeout_ms = timeout_ms
        return self

    def heart_beat_interval(self, heart_beat_interval) -> "ClientConfigBuilder":
        self._config.heart_beat_interval = heart_beat_interval
        return self

    def log_level(self, log_level) -> "ClientConfigBuilder":
        self._config.log_level = log_level
        return self

    def log_dir(self, log_dir) -> "ClientConfigBuilder":
        self._config.log_dir = log_dir
        return self

    def access_key(self, access_key) -> "ClientConfigBuilder":
        self._config.access_key = access_key
        return self

    def secret_key(self, secret_key) -> "ClientConfigBuilder":
        self._config.secret_key = secret_key
        return self

    def username(self, username) -> "ClientConfigBuilder":
        self._config.username = username
        return self

    def password(self, password) -> "ClientConfigBuilder":
        self._config.password = password
        return self

    def cache_dir(self, cache_dir) -> "ClientConfigBuilder":
        self._config.cache_dir = cache_dir
        return self

    def tls_config(self, tls_config: TLSConfig) -> "ClientConfigBuilder":
        self._config.tls_config = tls_config
        return self

    def kms_config(self, kms_config: KMSConfig) -> "ClientConfigBuilder":
        self._config.kms_config = kms_config
        return self

    def not_load_cache_at_start(self, not_load_cache_at_start: bool) -> "ClientConfigBuilder":
        self._config.not_load_cache_at_start = not_load_cache_at_start
        return self

    def build(self):
        return self._config
