from dataclasses import dataclass
from datetime import date
from typing import Optional, List

# from do import commands,events
from allocation.domain import events, commands


@dataclass(unsafe_hash=True)
class OrderLine:
    '''
    TODO 数据类是类变量 如果Batch这么写 allocations就会出问题 不是实例变量
    '''
    order_id: str
    sku: str
    qty: int


class Batch:
    def __init__(self, ref, sku, qty, eta: Optional[date] = None):
        """

        :rtype: object
        """
        self.ref = ref
        self.sku = sku
        self._purchased_quantity = qty
        self.eta = eta
        self.allocations = set()

    @property
    def allocated_quantity(self):
        return sum(line.qty for line in self.allocations)

    @property
    def available_quantity(self):
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line):
        # if line.sku == self.sku and line.qty <= self.available_quantity:
        #     return True
        # return False
        return line.sku == self.sku and line.qty <= self.available_quantity

    def allocate(self, line):
        if self.can_allocate(line):
            # self._available_quantity -= line.qty
            self.allocations.add(line)

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def deallocate(self, unallocated_line: OrderLine):
        if unallocated_line in self.allocations:
            self.allocations.remove(unallocated_line)
            # self.available_quantity += unallocated_line.qty

    def __eq__(self, other):
        if not isinstance(other, Product):
            return False
        return self.ref == other.ref

    def __hash__(self):
        return hash(self.ref)

    def deallocate_one(self) -> OrderLine:
        return self.allocations.pop()


class OutOfStock(Exception): pass


class Product:

    def __init__(self, sku, batches: List[Batch], version_number: int = 0):
        self.sku = sku
        self.batches = batches  # type: List[Batch]
        self.version_number = version_number
        self.events = []

    def allocate(self, line: OrderLine):
        try:
            prefers_batche = next(
                b for b in sorted(self.batches) if b.can_allocate(line))
            prefers_batche.allocate(line)
            self.version_number += 1

            self.events.append(events.Allocated(
                orderid=line.order_id,
                sku=line.sku,
                qty=line.qty,
                batchref=prefers_batche.ref
            ))

            return prefers_batche.ref
        except StopIteration:
            self.events.append(events.OutOfStock(line.sku))
            # raise OutOfStock(f'Out of stock for sku {line.sku}')
            return None

    def change_batch_quantity(self, ref, qty):
        b = next(b for b in self.batches if b.ref == ref)  # type:Batch
        b._purchased_quantity = qty
        while b.available_quantity < 0:
            line = b.deallocate_one()
            self.events.append(
                events.Deallocated(line.order_id, line.sku, line.qty)
                # commands.Allocate(line.order_id, line.sku, line.qty)
            )
