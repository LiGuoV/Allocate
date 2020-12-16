import json
import logging

import redis

from allocation import config, bootstrap
from allocation.adapters import orm
from allocation.domain import commands
from allocation.service_layer import messagebus, unit_of_work

r = redis.Redis(**config.get_redis_host_and_port())
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def main():
    logger.debug('Redis pubsub starting')

    bus = bootstrap.bootstrap()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('change_batch_quantity')

    for m in pubsub.listen():
        handle_change_batch_quantity(m,bus)


def handle_change_batch_quantity(m,bus):
    logger.debug(f'handling {m}')
    data = json.loads(m['data'])
    cmd = commands.ChangeBatchQuantity(
        ref=data['batchref'],
        qty=data['qty']
    )
    bus.handle(cmd)


if __name__ == '__main__':
    main()
