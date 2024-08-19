class PayloadRegistry:
    _REGISTRY_REQUEST = {}

    @classmethod
    def init(cls, payloads):
        # 初始化注册表，扫描并注册 Payload 类
        # 假设有一个名为 payloads 的列表，里面包含了所有的 Payload 子类
        cls.payloads = payloads
        cls.scan()

    @classmethod
    def scan(cls):
        # 模拟服务加载过程，这里只是一个示例，实际情况可能需要根据项目结构调整
        for payload_class in cls.payloads:
            cls.register(payload_class.__name__, payload_class)

    @classmethod
    def register(cls, type_name, clazz):
        # 检查类是否抽象
        if isinstance(clazz, type) and any("Abstract" in b.__name__ for b in clazz.__bases__):
            return
        # 检查类型是否已经注册
        if type_name in cls._REGISTRY_REQUEST:
            raise RuntimeError(f"Fail to register, type:{type_name}, clazz:{clazz.__name__}")
        cls._REGISTRY_REQUEST[type_name] = clazz

    @classmethod
    def get_class_by_type(cls, type_name):
        return cls._REGISTRY_REQUEST.get(type_name)