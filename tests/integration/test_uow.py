import threading
import time
import traceback

import pytest

from allocation.domain import model
from allocation.service_layer import unit_of_work
from tests.e2e.test_api import random_sku, random_batchref, random_orderid

pytestmark = pytest.mark.usefixtures('mappers')

def insert_batch(session, ref, sku, qty, eta,product_version=1):
    session.execute(
        ' insert into products (sku,version_number) values (:sku,:version)',
        dict(sku=sku,version=product_version)
    )

    session.execute(
        'INSERT INTO batches (ref, sku, _purchased_quantity, eta)'
        ' VALUES (:ref, :sku, :qty, :eta)',
        dict(ref=ref, sku=sku, qty=qty, eta=eta)
    )


def get_allocated_batch_ref(session, orderid, sku):
    [[orderlineid]] = session.execute(
        'select id from order_lines where order_id=:orderid and sku=:sku',
        dict(orderid=orderid, sku=sku)
    )
    [[batchref]] = session.execute(
        'select b.ref  from allocations join batches as b on batch_id=b.id '
        'where orderline_id=:orderlineid',
        dict(orderlineid=orderlineid)
    )
    return batchref


def test_uow_can_retrieve_a_batch_and_allocate_to_it(sqlite_session_factory):
    session = sqlite_session_factory()
    insert_batch(session, 'batch1', 'HIPSTER-WORKBENCH', 100, None)
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    with uow:
        product = uow.products.get(sku='HIPSTER-WORKBENCH')
        line = model.OrderLine('o1', 'HIPSTER-WORKBENCH', 10)
        product.allocate(line)
        uow.commit()

    batchref = get_allocated_batch_ref(session, 'o1', 'HIPSTER-WORKBENCH')
    assert batchref == 'batch1'


def test_rollback_unicommitted_work_by_default(sqlite_session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    with uow:
        insert_batch(uow.session, 'b1', '椅子', 100, None)
    new_session = sqlite_session_factory()
    rows = list(new_session.execute(
        'select * from "batches"'
    ))
    assert rows == []


def test_rollback_on_error(sqlite_session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)

    with pytest.raises(MyException):
        with uow:
            insert_batch(uow.session, 'b1', '椅子', 100, None)
            raise MyException()

    new_session = sqlite_session_factory()
    rows = list(new_session.execute(
        'select * from  batches '
    ))
    assert rows == []


def try_to_allocate(orderid,sku,exceptions):
    line = model.OrderLine(orderid, sku, 10)
    try:
        with unit_of_work.SqlAlchemyUnitOfWork() as uow:
            product = uow.products.get(sku=sku)
            product.allocate(line)
            time.sleep(0.2)
            uow.commit()
    except Exception as e:
        print(traceback.format_exc())
        exceptions.append(e)

def test_concurrent_updates_to_version_are_not_allowed(postgres_session_factory):
    sku,batch = random_sku(),random_batchref()
    session = postgres_session_factory()
    insert_batch(session,batch,sku,100,None,product_version=1)
    session.commit()

    order1,order2 = random_orderid(1),random_orderid(2)
    exceptions = []
    try_to_allocate_order1 = lambda :try_to_allocate(order1,sku,exceptions)
    try_to_allocate_order2 = lambda :try_to_allocate(order2,sku,exceptions)
    thread1 = threading.Thread(target=try_to_allocate_order1)
    thread2 = threading.Thread(target=try_to_allocate_order2)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    [[version]] = session.execute(
        'select version_number from products where sku=:sku',
        dict(sku=sku)
    )
    assert version == 2
    [exception] = exceptions
    assert 'could not serialize access due to concurrent update' in str(exception)

    orders = list(session.execute(
        ' select order_id from allocations '
        ' join batches on allocations.batch_id = batches.id'
        ' join order_lines on allocations.orderline_id=order_lines.id'
        ' where order_lines.sku=:sku',
        dict(sku=sku)
    ))
    assert len(orders) == 1
    with unit_of_work.SqlAlchemyUnitOfWork() as uow:
        uow.session.execute('select 1')

