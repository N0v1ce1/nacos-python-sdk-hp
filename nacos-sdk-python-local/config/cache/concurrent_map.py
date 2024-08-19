import threading
import json
import fnvhash

SHARD_COUNT = 32


class Shard:
    def __init__(self):
        self._items = {}
        self._lock = threading.RLock()

    def set(self, key, value):
        with self._lock:
            self._items[key] = value

    def get(self, key):
        with self._lock:
            return self._items.get(key)

    def delete(self, key):
        with self._lock:
            if key in self._items:
                del self._items[key]

    def __iter__(self):
        with self._lock:
            return ((key, self._items[key]) for key in self._items)


class ConcurrentMap:
    def __init__(self):
        self._shards = [Shard() for _ in range(SHARD_COUNT)]

    def _get_shard(self, key):
        # Use FNV-1a hash to determine the shard
        shard_index = fnvhash.fnv1a_32(key.encode('utf-8')) % SHARD_COUNT
        return self._shards[shard_index]

    def set(self, key, value):
        shard = self._get_shard(key)
        shard.set(key, value)

    def get(self, key):
        shard = self._get_shard(key)
        return shard.get(key)

    def delete(self, key):
        shard = self._get_shard(key)
        shard.delete(key)

    def __iter__(self):
        for shard in self._shards:
            for key, value in shard:
                yield (key, value)

    def items(self):
        return list(self)

    def keys(self):
        return [key for key, _ in self]

    def values(self):
        return [value for _, value in self]

    def count(self):
        count = 0
        for shard in self._shards:
            with shard._lock:
                count += len(shard._items)
        return count

    def has(self, key):
        shard = self._get_shard(key)
        with shard._lock:
            return key in shard._items

    def set_if_absent(self, key, value):
        shard = self._get_shard(key)
        with shard._lock:
            if key not in shard._items:
                shard._items[key] = value
            return True
        return False

    def upsert(self, key, value, func):
        shard = self._get_shard(key)
        with shard._lock:
            exist = key in shard._items
            current_value = shard._items.get(key)
            new_value = func(exist, current_value, value)
            shard._items[key] = new_value
            return new_value

    def mset(self, data):
        for key, value in data.items():
            self.set(key, value)

    def pop(self, key):
        shard = self._get_shard(key)
        with shard._lock:
            if key in shard._items:
                value = shard._items.pop(key)
                return value
            return None

    def is_empty(self):
        return self.count() == 0

    def iter_buffered(self):
        # This method would need to be implemented to provide an efficient buffered iterator.
        pass

    def iter_cb(self, func):
        for key, value in self:
            func(key, value)

    def marshal_json(self):
        tmp = {}
        for key, value in self:
            tmp[key] = value
        return json.dumps(tmp).encode('utf-8')



