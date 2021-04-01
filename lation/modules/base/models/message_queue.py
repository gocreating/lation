import time
from typing import List, Callable

from kombu import Connection, Exchange, Producer, Queue
from kombu.mixins import ConsumerMixin

from lation.core.env import get_env


APP = get_env('APP')
MESSAGE_QUEUE_URL = get_env('MESSAGE_QUEUE_URL')

class MessageClient:

    @staticmethod
    def establish_connection():
        assert MESSAGE_QUEUE_URL != None, 'MESSAGE_QUEUE_URL is required'
        # https://github.com/celery/kombu/issues/596#issuecomment-225751069
        conn = Connection(MESSAGE_QUEUE_URL)
        revived_conn = conn.ensure_connection(max_retries=3)
        return revived_conn


class MessageBroker:
    exchange = Exchange('default_exchange', 'topic', durable=True)
    queue = Queue(f'default_queue_{APP}', exchange=exchange, routing_key=f'app.{APP}')


class Publisher:

    def publish(self, message):
        exchange = MessageBroker.exchange
        queue = MessageBroker.queue

        # https://docs.celeryproject.org/projects/kombu/en/stable/userguide/producers.html#basics
        with MessageClient.establish_connection() as conn:
            producer = Producer(conn)
            producer.publish(message,
                             serializer='json',
                             exchange=exchange,
                             routing_key=queue.routing_key,
                             declare=[queue],
                             retry=True,
                             retry_policy={
                                 'interval_start': 0, # First retry immediately,
                                 'interval_step': 2,  # then increase by 2s for every retry.
                                 'interval_max': 30,  # but don't exceed 30s between retries.
                                 'max_retries': 30,   # give up after 30 tries.
                             })


class Subscriber(ConsumerMixin):

    @classmethod
    def run_forever(cls):
        while True:
            try:
                cls().run()
            except Exception as e:
                print('[Subscriber] run() exited with exception:')
                print(e)
                print('[Subscriber] will retry run() after 5 seconds')
                time.sleep(5)

    def __init__(self):
        self.connection = MessageClient.establish_connection()

    def get_consumers(self, Consumer, channel):
        queue = MessageBroker.queue
        return [
            Consumer([queue], callbacks=self.get_callbacks(), accept=['json']),
        ]

    def get_callbacks(self) -> List[Callable]:
        raise NotImplementedError
