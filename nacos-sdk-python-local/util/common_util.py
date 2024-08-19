import time
import json
from ..common.nacos_exception import NacosException, CLIENT_INVALID_PARAM
from ..common.constants import Constants

VALID_CHARS = ('_', '-', '.', ':')

CONTENT_INVALID_MSG = "content invalid"

DATAID_INVALID_MSG = "dataId invalid"

TENANT_INVALID_MSG = "tenant invalid"

BETAIPS_INVALID_MSG = "betaIps invalid"

GROUP_INVALID_MSG = "group invalid"

DATUMID_INVALID_MSG = "datumId invalid"


def get_current_time_millis():
    t = time.time()
    return int(round(t * 1000))


def to_json_string(obj):
    try:
        return json.dumps(obj)
    except (TypeError, ValueError) as e:
        print(f"Error serializing object to JSON: {e}")
        return None


def is_blank(value):
    return not value or value.isspace()


def is_valid(value):
    return len(value) > 0 and not is_blank(value)


def check_key_param(data_id, group):
    if is_blank(data_id) or not is_valid(data_id):
        raise NacosException(CLIENT_INVALID_PARAM, DATAID_INVALID_MSG)
    if is_blank(group) or not is_valid(group):
        raise NacosException(CLIENT_INVALID_PARAM, GROUP_INVALID_MSG)


def get_config_cache_key(data_id, group, tenant):
    return f"{data_id}{Constants.CONFIG_INFO_SPLITER}{group}{Constants.CONFIG_INFO_SPLITER}{tenant}"


def get_config_cache_key(data_id, group, tenant):
    return data_id + Constants.CONFIG_INFO_SPLITER + group + Constants.CONFIG_INFO_SPLITER + tenant
