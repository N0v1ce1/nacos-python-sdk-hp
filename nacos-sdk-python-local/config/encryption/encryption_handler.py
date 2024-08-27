import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict
from encryption_plugin_manager import EncryptionPluginManager
from ...common.constants import Constants
from ...common.client_config import ClientConfig

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class HandlerParam:
    def __init__(self, data_id, content, encrypted_data_key='', plain_data_key='', key_id=''):
        self.data_id = data_id
        self.content = content
        self.encrypted_data_key = encrypted_data_key
        self.plain_data_key = plain_data_key
        self.key_id = key_id

    # 序列化
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    # 反序列化
    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        return HandlerParam(**data)


class EncryptionHandler:
    PREFIX = "cipher-"

    @staticmethod
    def check_cipher(data_id: str) -> bool:
        return data_id.startswith(EncryptionHandler.PREFIX
                                  ) and not data_id == EncryptionHandler.PREFIX

    @staticmethod
    def parse_algorithm_name(data_id: str) -> Optional[str]:
        parts = data_id.split("-")
        return parts[1] if len(parts) > 1 else None

    @staticmethod
    def encrypt_handler(data_id: str, content: str) -> Tuple[str, str]:
        if not EncryptionHandler.check_cipher(data_id):
            return "", content

        algorithm_name = EncryptionHandler.parse_algorithm_name(data_id)
        if not algorithm_name:
            LOGGER.warn(
                f"[EncryptionHandler] [encryptHandler] No algorithm name found in dataId: {data_id}"
            )
            return "", content

        manager = EncryptionPluginManager.get_instance()
        service = manager.find_encryption_service(algorithm_name)
        if not service:
            LOGGER.warn(
                f"[EncryptionHandler] [encryptHandler] No encryption service found for algorithm name: {algorithm_name}"
            )
            return "", content

        secret_key = service.generate_secret_key()
        encrypt_content = service.encrypt(secret_key, content)
        return service.encrypt_secret_key(secret_key), encrypt_content

    @staticmethod
    def decrypt_handler(data_id: str, secret_key: str,
                        content: str) -> Tuple[str, str]:
        if not EncryptionHandler.check_cipher(data_id):
            return secret_key, content

        algorithm_name = EncryptionHandler.parse_algorithm_name(data_id)
        if not algorithm_name:
            LOGGER.warn(
                f"[EncryptionHandler] [decryptHandler] No algorithm name found in dataId: {data_id}"
            )
            return secret_key, content

        manager = EncryptionPluginManager.get_instance()
        service = manager.find_encryption_service(algorithm_name)
        if not service:
            LOGGER.warn(
                f"[EncryptionHandler] [decryptHandler] No encryption service found for algorithm name: {algorithm_name}"
            )
            return secret_key, content

        decrypt_secret_key = service.decrypt_secret_key(secret_key)
        decrypt_content = service.decrypt(decrypt_secret_key, content)
        return decrypt_secret_key, decrypt_content
