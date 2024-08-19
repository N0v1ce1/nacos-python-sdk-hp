import uuid

from ....common.constants import Constants
from ....transport.rpc_client import RpcClient
from naming_grpc_redo_service import NamingGrpcRedoService


class AbstractNamingClientProxy:
    def __init__(self, security_proxy):
        self.security_proxy = security_proxy

    def get_security_headers(self, namespace, group, service_name):
        pass


class NamingGrpcClientProxy(AbstractNamingClientProxy):
    def __init__(self, namespace_id, security_proxy, server_list_factory, properties, service_info_holder):
        super().__init__(security_proxy)
        self.namespace_id = namespace_id
        self.uuid = str(uuid.uuid4())
        self.request_timeout = int(properties.get('nacos.request.timeout', -1))
        self.labels = {'source': 'sdk', 'module': 'naming', 'app_name': Constants.APPNAME}
        self.rpc_client = RpcClient(self.uuid)
        self.redo_service = NamingGrpcRedoService(self, properties)
        self.start(server_list_factory, service_info_holder)

    def start(self):
        self.rpc_client.nacos_server.get_server_list()
        self.rpc_client.register_connection_listener(self.redo_service)
        # 注册服务请求处理器，这里需要根据实际情况实现
        self.rpc_client.start()

    def get_app_name(self):
        # 实现获取应用名称的方法
        return self.labels['app_name']

    def onEvent(self):
        pass

    def getRetainInstance(self):
        pass

    def compareIpAndPort(self):
        pass

    def doBatchRegisterService(self):
        pass

    def doRegisterService(self):
        pass

    def doRegisterServiceForPersistent(self):
        pass

    def deregisterService(self):
        pass

    def deregisterServiceForEphemeral(self):
        pass

    def doDeregisterService(self):
        pass

    def doDeregisterServiceForPersistent(self):
        pass

    def updateInstance(self):
        pass

    def queryInstancesOfService(self):
        pass

    def queryService(self):
        pass

    def createService(self):
        pass

    def deleteService(self):
        pass

    def updateService(self):
        pass

    def getServiceList(self):
        pass

    def subscribe(self):
        pass

    def doSubscribe(self):
        pass

    def unsubscribe(self):
        pass

    def isSubscribed(self):
        pass

    def serverHealthy(self):
        pass

    def isAbilitySupportedByServer(self):
        pass

    def requestToServer(self):
        pass

    def recordRequestFailedMetrics(self):
        pass

    def shutdown(self):
        pass

    def shutDownAndRemove(self):
        pass

    def isEnable(self):
        pass
    
