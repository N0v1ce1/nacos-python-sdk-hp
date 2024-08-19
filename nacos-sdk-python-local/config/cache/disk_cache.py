from cache_const import *
import os
from ...common.file import file


def get_failover(key, dir, logger):
    file_path = get_config_fail_over_content_file_name(key, dir)
    return get_fail_over_config(file_path, ConfigCachedFileType.CONFIG_CONTENT, logger)


def get_config_fail_over_content_file_name(cache_key, cache_dir):
    return get_file_name(cache_key, cache_dir) + FAILOVER_FILE_SUFFIX


def get_file_name(cache_key, cache_dir):
    return os.path.join(cache_dir, cache_key)


def get_fail_over_config(file_path, file_type, logger):
    if not file.is_file_exist(file_path):
        error_msg = f"read {file_type} failed. cause file doesn't exist, file path: {file_path}."
        logger.error(error_msg)
        return ""

    logger.warning(f"reading failover {file_type} from path:{file_path}")
    try:
        file_content = file.read_file(file_path)
    except Exception as e:
        logger.error(f"fail to read failover {file_type} from {file_path}")
        return ""

    return file_content


def get_failover_encrypted_data_key(cache_key, config_cache_dir, logger):
    file_path = get_config_fail_over_content_file_name(cache_key, dir)
    return get_fail_over_config(file_path, ConfigCachedFileType.CONFIG_ENCRYPTED_DATA_KEY, logger)


def write_config_to_file(file_path, file_name, file_type, logger):
    pass


def write_encrypted_data_key_to_file(file_path, file_name, file_type, logger):
    pass


def _read_config_from_file(file_name, file_type):
    if not os.path.isfile(file_name):
        error_msg = f"read cache file {file_type} failed. cause file doesn't exist, file path: {file_name}."
        return "", error_msg

    try:
        with open(file_name, 'rb') as file:
            file_content = file.read()
        return file_content.decode('utf-8'), None  # 假设文件编码为UTF-8
    except IOError as e:  # 捕获文件读取过程中可能发生的IO错误
        error_msg = f"get {file_type} from cache failed, filePath:{file_name}, error:{e}"
        return "", error_msg


def read_config_from_file(cache_key, cache_dir):
    file_name = get_file_name(cache_key, cache_dir)
    return _read_config_from_file(file_name, ConfigCachedFileType.CONFIG_CONTENT)


def read_encrypted_data_key_from_file(cache_key, cache_dir):
    pass



