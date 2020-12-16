import json

from tenacity import Retrying, stop_after_delay

from tests.e2e import api_client, redis_client
from tests.e2e.test_api import random_orderid, random_sku, random_batchref
from tests.unit.test_batch import today,tomorrow


def test_change_batch_qty_leading_to_reallocation():
    '''
    测试改变批次数量 导致重新分配
    '''
    orderid,sku = random_orderid(),random_sku()
    earlier_batch,later_batch = random_batchref('old'),random_batchref('new')
    api_client.post_to_add_batch(earlier_batch,sku,10,str(today))
    api_client.post_to_add_batch(later_batch,sku,10,str(tomorrow))
    api_client.post_to_allocte(orderid,sku,10)
    r = api_client.get_allocation(orderid)

    assert r.json()[0]['batchref'] == earlier_batch

    subscription = redis_client.subscribe_to('line_allocated')

    # 发布一个命令 终端的事件消费者接收到 调用hander 这个逻辑里 成功完成分配订单 发布了一个line_allocated
    redis_client.publish_message('change_batch_quantity',{
        'batchref':earlier_batch,'qty':5
    })

    messages = []
    for attempt in Retrying(stop=stop_after_delay(3),reraise=True):
        with attempt:
            message = subscription.get_message(timeout=1)
            if message:
                messages.append(message)
                print(message)
            data = json.loads(messages[-1]['data'])
            assert data['orderid'] == orderid
            assert data['batchref'] == later_batch