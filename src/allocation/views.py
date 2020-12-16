from allocation.adapters import redis_eventpublisher
from allocation.service_layer import unit_of_work


def allocations(orderid, uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        # results = list(uow.session.execute(
        #     ' select ol.sku, b.ref'
        #     ' from allocations as a'
        #     ' join batches b on a.batch_id = b.id'
        #     ' join order_lines ol on a.orderline_id = ol.id'
        #     ' where ol.order_id =:orderid',
        #     dict(orderid=orderid)
        # ))

        results = list(uow.session.execute(
            'select sku,batchref from allocations_view where orderid=:orderid',
            dict(orderid=orderid)))
        return [{'sku': sku, 'batchref': batchref}
                    for sku, batchref in results]

    # batches = redis_eventpublisher.get_readmodel(orderid)
    # return [{'batchref': b.decode(), 'sku': s.decode()} for s, b in batches.items()]
