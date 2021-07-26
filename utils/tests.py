from testing.testcases import TestCase
from .redis_client import RedisClient

class UtilTests(TestCase):
    def setUp(self):
        RedisClient.clear()

    def test_redis_client(self):
        conn = RedisClient.get_connection()
        conn.lpush('redis_key', 1)
        conn.lpush('redis_key', 2)
        cached_list = conn.lrange('redis_key', 0, -1)
        self.assertEqual(cached_list, [b'2', b'1'])

        