from abc import ABC, abstractmethod
from grpc import Channel
from  ..common.model.request import IRequest
from  ..common.model.response import IResponse
from rpc_client import RpcClient, ServerInfo


class IConnection(ABC):
    @abstractmethod
    def request(self, request: IRequest, timeout_mills: int, client: RpcClient) -> IResponse:
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def get_connection_id(self) -> str:
        pass

    @abstractmethod
    def get_server_info(self) -> ServerInfo:
        pass

    @abstractmethod
    def set_abandon(self, flag: bool):
        pass

    @abstractmethod
    def get_abandon(self) -> bool:
        pass


class Connection(IConnection):
    def __init__(self, conn: Channel, connection_id: str, server_info: ServerInfo):
        self.conn = conn
        self.connection_id = connection_id
        self.abandon = False
        self.server_info = server_info

    def request(self, request: IRequest, timeout_mills: int, client: RpcClient) -> IResponse:
        pass 

    def close(self):
        if self.conn:
            self.conn.close()

    def get_connection_id(self) -> str:
        return self.connection_id

    def get_server_info(self) -> ServerInfo:
        return self.server_info

    def set_abandon(self, flag: bool):
        self.abandon = flag

    def get_abandon(self) -> bool:
        return self.abandon