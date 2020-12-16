import pytest

from allocation.adapters import repository
from allocation.domain import model

pytestmark = pytest.mark.usefixtures('mappers')


def test_get_by_batchref(sqlite_session):
    repo = repository.SqlAlchemyRepository(sqlite_session)
    b1 = model.Batch('b1','sku1',100)
    b2 = model.Batch('b2','sku1',100)
    b3 = model.Batch('b3','sku2',100)

    p1 = model.Product('sku1',[b1,b2])
    p2 = model.Product('sku2',[b3])

    repo.add(p1)
    repo.add(p2)
    assert repo.get_by_batcheref('b1')==p1
    assert repo.get_by_batcheref('b3')==p2
