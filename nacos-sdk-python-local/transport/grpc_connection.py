from connection import IConnection, Connection
import proto.nacos_grpc_service_pb2_grpc as ngs

class GrpcConnection(Connection):
    tps_control_manager = None

    def __init__(self):
        self.request = ngs.Request
        self.bi_stream = ngs.BiRequestStream

    def send_request_no_ack(self, request):
        pass

    def _send_request(self, request):
        pass

    def send_queue_block_check(self):
        pass

    def trace_if_necessary(self, payload):
        pass

    def request(self, request, timeout_mills):
        pass

    def send_request_inner(self, request, call_back):
        pass

    def close(self):
        pass

    def close_bi_stream(self):
        pass

    def is_connected(self):
        pass