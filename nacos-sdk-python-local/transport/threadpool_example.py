import asyncio

# 假设这是 ConnectionEvent 类和 notifyConnected/notifyDisConnected 方法
class ConnectionEvent:
    def __init__(self, connection, is_connected):
        self.connection = connection
        self.is_connected = is_connected

    def detect_is_connected(self):
        return self.is_connected

    def detect_is_disconnected(self):
        return not self.is_connected

async def notify_connected(connection):
    print(f"Connected: {connection}")

async def notify_disconnected(connection):
    print(f"Disconnected: {connection}")

# 模拟阻塞队列
event_queue = asyncio.Queue()

# 事件消费者协程
async def event_consumer():
    while True:
        # 从队列中获取事件，模拟阻塞行为
        event = await event_queue.get()
        if event.detect_is_connected():
            await notify_connected(event.connection)
        elif event.detect_is_disconnected():
            await notify_disconnected(event.connection)
        # 任务完成后通知队列任务已完成
        event_queue.task_done()

# 运行事件消费者
async def run_event_consumers(consumer_count):
    # 创建消费者任务列表
    consumers = [event_consumer() for _ in range(consumer_count)]
    # 并发运行所有消费者任务
    await asyncio.gather(*consumers)

# 模拟事件生产者，向队列中添加事件
async def event_producer(event_queue):
    connections = ["Connection{}".format(i) for i in range(99)]
    for connection in connections:
        # 模拟连接事件
        event = ConnectionEvent(connection, True)
        await event_queue.put(event)
        # 模拟断开连接事件
        event = ConnectionEvent(connection, False)
        await event_queue.put(event)
    await event_queue.join()  # 等待所有事件被处理

# 主函数
async def main():
    # 启动两个事件消费者
    await asyncio.gather(
        run_event_consumers(2),
        event_producer(event_queue)
    )

# 运行主函数
asyncio.run(main())