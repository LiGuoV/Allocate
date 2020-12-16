import uuid

import pytest

from tests.e2e import api_client


def _random_suffix():
    return uuid.uuid4().hex


def random_orderid(name=''):
    return f'O-{name}-{_random_suffix()}'


def random_sku(name=''):
    return f'O-{name}-{_random_suffix()}'


def random_batchref(name=''):
    return f'B-{name}-{_random_suffix()}'


@pytest.mark.usefixtures('postgres_session')
@pytest.mark.usefixtures('restart_api')
def test_happy_path_returns_202_and_allocated_batch():
    sku, othersku = random_sku(), random_sku('other')
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)

    api_client.post_to_add_batch(laterbatch, sku, 100, '2011-01-02')
    api_client.post_to_add_batch(earlybatch, sku, 100, '2011-01-01')
    api_client.post_to_add_batch(otherbatch, othersku, 100, None)

    orderid = random_orderid()
    r = api_client.post_to_allocte(
        orderid, sku, 3)
    assert r.status_code == 202

    r = api_client.get_allocation(orderid=orderid)
    assert r.ok
    assert r.json() == [
        {'sku': sku, 'batchref': earlybatch}]


@pytest.mark.usefixtures('postgres_session')
@pytest.mark.usefixtures('restart_api')
def test_unhappy_path_returns_400_and_error_msg():
    sku,orderid = random_sku(),random_orderid()
    r = api_client.post_to_allocte(
        orderid, sku, 200, expect_success=False)

    assert r.status_code == 400
    assert r.json()['message'] == f'Invalid sku {sku}'

    r = api_client.get_allocation(orderid)
    assert r.status_code == 404
