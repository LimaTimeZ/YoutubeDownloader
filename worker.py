import config
from rq import Connection, Worker
from redis import Redis

redis_conn = Redis.from_url(config.REDIS_URL)

if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker(["default"])
        worker.work()