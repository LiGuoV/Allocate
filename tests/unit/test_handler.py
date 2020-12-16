from collections import defaultdict
from datetime import date
from unittest import mock

import pytest

from allocation import bootstrap
from allocation.adapters import notifications
from allocation.domain import commands, model
from allocation.service_layer import handlers, unit_of_work
from allocation.adapters.repository import AbsProductRepository


class FakeRepository(AbsProductRepository):

    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, batch: model.Product):
        self._products.add(batch)

    def _get(self, sku) -> model.Product:
        return next((p for p in self._products if p.sku == sku), None)

    def _get_by_batcheref(self, batchref):
        return next(
            (p for p in self._products
             for b in p.batches
             if b.ref == batchref),
            None,
        )


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


class FakeUnitOfWork(unit_of_work.AbsUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.commited = False

    def _commit(self):
        self.commited = True

    def rollback(self):
        pass


class FakeUnitOfWorkWithFakebus(FakeUnitOfWork):
    def __init__(self):
        super().__init__()
        self.events_published = []

    def publish_events(self):
        for product in self.products.seen:
            while product.events:
                self.events_published.append(product.events.pop(0))

class FakeNotifications(notifications.AbsNotifications):
    def __init__(self):
        self.sent = defaultdict(list)

    def send(self,destination,message):
        self.sent[destination].append(message)


def bootstrap_test_app():
    return bootstrap.bootstrap(
        start_orm=False,
        uow=FakeUnitOfWork(),

        publish=lambda *args: None
    )


class TestAddBatch:
    def test_add_batch_for_new_product(self):
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch('b1', '黑桌子', 20, None))
        assert bus.uow.products.get('黑桌子') is not None
        assert bus.uow.commited

    def test_for_existing_product(self):
        # bus = bootstrap_test_app()
        bus = bootstrap_test_app()

        bus.handle(commands.CreateBatch("b1", "GARISH-RUG", 100, None))
        bus.handle(commands.CreateBatch("b2", "GARISH-RUG", 99, None))
        assert "b2" in [b.ref for b in bus.uow.products.get("GARISH-RUG").batches]


class TestAllocate:

    def test_allocates(self):
        bus = bootstrap_test_app()

        bus.handle(commands.CreateBatch('b1', '黑桌子', 20, None))
        bus.handle(commands.Allocate('o1', '黑桌子', 10))
        [batch] = bus.uow.products.get('黑桌子').batches
        assert batch.available_quantity == 10

    def test_errors_for_invalid_sku(self):
        '''
        测试 不存在的商品
        :return:
        '''
        bus = bootstrap_test_app()
        bus.handle(commands.CreateBatch("b1", "AREALSKU", 100, None))

        with pytest.raises(handlers.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            bus.handle(commands.Allocate("o1", "NONEXISTENTSKU", 10))

    def test_commits(self):
        bus = bootstrap_test_app()

        bus.handle(
            commands.CreateBatch("b1", "OMINOUS-MIRROR", 100, None)
        )
        bus.handle(
            commands.Allocate("o1", "OMINOUS-MIRROR", 10))
        assert bus.uow.commited

    def test_sends_email_on_out_of_stock_error(self):
        bus = bootstrap_test_app()
        bus.handle(
            commands.CreateBatch("b1", "POPULAR-CURTAINS", 9, None)
        )
        bus.handle(
            commands.Allocate("o1", "POPULAR-CURTAINS", 10)
        )

        with mock.patch("allocation.adapters.notifications.EmailNotifications.send") as mock_send_mail:
            bus.handle(
                commands.Allocate("o1", "POPULAR-CURTAINS", 10)
            )
            assert mock_send_mail.call_args == mock.call(
                ['18511041894@163.com'],"缺货啦,货号POPULAR-CURTAINS"
            )


class TestBatchQuantityChanged:

    def test_changes_avaliable_qty(self):
        bus = bootstrap_test_app()
        bus.handle(
            commands.CreateBatch('批次1', '板凳', 70))
        [batch] = bus.uow.products.get(sku='板凳').batches
        bus.handle(
            commands.ChangeBatchQuantity('批次1', 50))

        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self):
        bus = bootstrap_test_app()
        event_history = [
            commands.CreateBatch('批次1', '桌子', 50),
            commands.CreateBatch('批次2', '桌子', 50, date.today()),
            commands.Allocate('订单1', '桌子', 20),
            commands.Allocate('订单2', '桌子', 20),
        ]
        for e in event_history:
            bus.handle(e)
        [batch1, batch2] = bus.uow.products.get(sku='桌子').batches
        assert batch1.available_quantity == 10  # 下了两单 现在库存10
        assert batch2.available_quantity == 50  # 这个不变

        # bus.handle(
        #     commands.ChangeBatchQuantity('批次1', 25), uow)
        bus.handle(commands.ChangeBatchQuantity('批次1', 25))
        assert batch1.available_quantity == 5  # 批次1泡水了 库存25 所以要退下的单子给批次2
        assert batch2.available_quantity == 30  # 批次2 减少20

# def test_reallocates_if_necessary_isolated():
#     uow = FakeUnitOfWorkWithFakebus()
#
#     # test setup as before
#     event_history = [
#         commands.CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
#         commands.CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
#         commands.Allocate("order1", "INDIFFERENT-TABLE", 20),
#         commands.Allocate("order2", "INDIFFERENT-TABLE", 20),
#     ]
#     for e in event_history:
#         bus.handle(e, uow)
#     [batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches
#     assert batch1.available_quantity == 10
#     assert batch2.available_quantity == 50
#
#     bus.handle(commands.ChangeBatchQuantity("batch1", 25), uow)
#
#     # assert on new events emitted rather than downstream side-effects
#     [reallocation_event] = uow.events_published
#     assert isinstance(reallocation_event, events.AllocationRequired)
#     assert reallocation_event.orderid in {'order1', 'order2'}
#     assert reallocation_event.sku == 'INDIFFERENT-TABLE'
