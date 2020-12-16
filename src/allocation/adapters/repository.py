import abc
from typing import Set

from allocation.adapters import orm
from allocation.domain import model


class AbsProductRepository(abc.ABC):

    def __init__(self):
        self.seen = set() # type: Set[model.Product]

    @abc.abstractmethod  #(1)
    def _add(self, product: model.Product):
        raise NotImplementedError  #(2)

    def add(self, product: model.Product):
        self._add(product)
        self.seen.add(product)

    @abc.abstractmethod
    def _get(self, sku) -> model.Product:
        raise NotImplementedError

    def get(self,sku):
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    def _get_by_batcheref(self,batchref):
        pass

    def get_by_batcheref(self,batchref):
        product = self._get_by_batcheref(batchref=batchref)
        if product:
            self.seen.add(product)
        return product

    def _get_by_orderid(self,orderid):
        pass

    def get_by_orderid(self,orderid):
        return self._get_by_orderid(orderid)


class SqlAlchemyRepository(AbsProductRepository):

    def __init__(self,session):
        super().__init__()
        self.session = session

    def _add(self, product: model.Product):
        self.session.add(product)

    def _get(self, sku):
        return self.session.query(model.Product).filter_by(sku=sku).first()

    def _get_by_batcheref(self,batchref):
        return self.session.query(model.Product).join(model.Batch)\
            .filter(orm.batches.c.ref == batchref).first()

    def _get_by_orderid(self,orderid):
        pass


