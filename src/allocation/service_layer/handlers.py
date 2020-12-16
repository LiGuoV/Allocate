from dataclasses import asdict
from typing import Type, Dict, Callable, List

from allocation.adapters import email, redis_eventpublisher
from allocation.domain import commands, model, events
from allocation.service_layer import unit_of_work
from allocation.adapters import notifications

class InvalidSku(Exception): pass


class NoneAlloacted(Exception): pass


def invalid_sku(sku, batches):
    if not sku in {b.sku for b in batches}:
        raise InvalidSku(f'Invalid sku {sku}')



# def allocate(orderid: str, sku: str, qty: int, repo: AbstractRepository, session):
#     batches = repo.list()
#     invalid_sku(sku, batches)
#     line = model.OrderLine(orderid,sku,qty)
#     batchref = model.allocate(batches, line)
#     session.commit()
#     return batchref

def add_batch(command: commands.CreateBatch, uow: unit_of_work.AbsUnitOfWork):
    with uow:
        product = uow.products.get(sku=command.sku)
        if product is None:
            product = model.Product(command.sku, batches=[])
            uow.products.add(product)

        batch = model.Batch(command.ref, command.sku, command.qty, command.eta)
        product.batches.append(batch)
        uow.commit()


def allocate(command: commands.Allocate, uow: unit_of_work.AbsUnitOfWork):
    line = model.OrderLine(command.orderid, command.sku, command.qty)
    with uow:
        product = uow.products.get(command.sku)
        if product is None:
            raise InvalidSku(f'Invalid sku {command.sku}')
        batchref = product.allocate(line)
        uow.commit()
    return batchref


def change_batch_quantity(command: commands.ChangeBatchQuantity, uow: unit_of_work.AbsUnitOfWork):
    with uow:
        product = uow.products.get_by_batcheref(command.ref)
        product.change_batch_quantity(ref=command.ref,qty=command.qty)
        uow.commit()


def send_out_of_stock_notif(event: events.OutOfStock, notifications:notifications.AbsNotifications):
    notifications.send(['18511041894@163.com'],
        f'缺货啦,货号{event.sku}'
    )


def publish_allocated_event(event: events.Allocated, publish:Callable ):
    return publish(channel='line_allocated',event=event)


def add_allocation_to_read_model(event: events.Allocated, uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        uow.session.execute(
            'insert into allocations_view (orderid,sku,batchref) '
            ' values (:orderid,:sku,:batchref)',
            dict(orderid=event.orderid,sku=event.sku,batchref=event.batchref)
        )
        uow.commit()

    # redis_eventpublisher.update_readmodel(event.orderid,event.sku,event.batchref)


def reallocate(event: events.Deallocated, uow: unit_of_work.AbsUnitOfWork):
    with uow:
        products = uow.products.get(event.sku)
        products.events.append(commands.Allocate(**asdict(event)))
        uow.commit()



def remove_allocation_from_read_model(event: events.Deallocated, uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        uow.session.execute(
            'delete from allocations_view'
            ' where orderid=:orderid and sku=:sku',
            dict(orderid=event.orderid,sku=event.sku)
        )
        uow.commit()

    # redis_eventpublisher.update_readmodel(event.orderid,event.sku,None)

EVENT_HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notif],
    events.Allocated: [publish_allocated_event,
                       add_allocation_to_read_model],

    events.Deallocated:[
        remove_allocation_from_read_model,
        reallocate
    ]

}  # type: Dict[Type[events.Event],List[Callable]]

COMMAND_HANDLERS = {
    commands.CreateBatch: add_batch,
    commands.Allocate: allocate,
    commands.ChangeBatchQuantity: change_batch_quantity,

}  # type: Dict[Type[commands.Command],Callable]