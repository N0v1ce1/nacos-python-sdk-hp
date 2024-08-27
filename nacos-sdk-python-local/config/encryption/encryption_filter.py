from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from .encryption_handler import EncryptionHandler
from ..model.config_filter import IConfigFilter
from ..model.config_request import ConfigRequest
from ..model.config_response import ConfigResponse
from ..model.config_param import ConfigParam, UsageType
from ...common.constants import Constants
from ..encryption.encryption_handler import HandlerParam

defaultConfigEncryptionFilterName = "defaultConfigEncryptionFilter"

noNeedEncryptionError = Exception("dataId doesn't need to encrypt/decrypt.")


class IConfigFilterChain:
    @abstractmethod
    def do_filter(self, request: Any, response: Any) -> None:
        pass


def _param_check(param: ConfigParam):
    if not param.data_id.startswith(Constants.CipherPrefix) or \
            len(param.content.strip()) == 0:
        raise ValueError("dataId doesn't need to encrypt/decrypt.")
    return True


class ConfigEncryptionFilter(IConfigFilter):

    def __init__(self, encryption_handler: EncryptionHandler):
        self.handler = encryption_handler

    def do_filter(self, param: ConfigParam) -> None:
        if _param_check(param):
            raise ValueError("Parameter check failed")
        if param.type == UsageType.request_type:
            encryption_param = HandlerParam(
                data_id=param.data_id,
                content=param.content,
                key_id=param.kms_key_id,
            )
            encryption_handler_result = self.handler.encrypt_handler(encryption_param.data_id, encryption_param.encrypted_data_key)
            if encryption_handler_result is not None:
                raise encryption_handler_result

            param.Content = encryption_param.content
            param.encrypted_data_key = encryption_param.encrypted_data_key

        elif param.type == UsageType.response_type:
            decryption_param = HandlerParam(
                data_id=param.data_id,
                content=param.content,
                encrypted_data_key=param.encrypted_data_key,
            )
            decryption_handler_result = self.handler.decrypt_handler(decryption_param.data_id, param.encrypted_data_key, decryption_param.content)
            if decryption_handler_result is not None:
                raise decryption_handler_result

            param.Content = decryption_param.content
        return None

    def get_order(self) -> int:
        return 0

    def get_filter_name(self) -> str:
        return defaultConfigEncryptionFilterName
