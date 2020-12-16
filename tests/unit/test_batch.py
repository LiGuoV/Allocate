from datetime import timedelta

from allocation.domain.model import *


today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def get_a_batch(ref='B-001',sku='红椅子',qty=20,eta=None):
    # id = random('')
    return Batch(ref, sku, qty, eta)

# def make_batch_and_line(sku,batch_qty,line_qty):
#     return Batch('B-001',sku,batch_qty),OrderLine('ORDER-001',sku,line_qty)

def make_batch_and_line(sku, batch_qty, line_qty):
    return (
        Batch("batch-001", sku, batch_qty, eta=date.today()),
        OrderLine("order-123", sku, line_qty)
    )

def test_allocating_to_a_batch_reduces_the_available_quantity():
    # 分配 库存减少可用数量
    batch = get_a_batch()
    line = OrderLine('001','红椅子',2)
    batch.allocate(line)
    assert  batch.available_quantity == 18

def test_can_allocate_if_available_greater_than_required():
    batch = get_a_batch()
    line = OrderLine('001', '红椅子', 2)
    batch.can_allocate(line)
    assert batch.can_allocate(line)

def test_cannot_allocate_if_available_smaller_than_required():
    # batch = get_a_batch()
    # line = OrderLine('001', '红椅子', 21)
    # batch.can_allocate(line)
    large_batch, small_line = make_batch_and_line("红椅子", 20, 2)
    assert large_batch.can_allocate(small_line)


def test_can_allocate_if_available_equal_to_required():
    batch = get_a_batch()
    line = OrderLine('001', '红椅子', 20)
    print(batch.can_allocate(line))


def test_can_only_deallocate_allocated_lines():
    batch, unallocated_line = make_batch_and_line("DECORATIVE-TRINKET", 20, 2)
    assert batch.available_quantity == 20
    batch.deallocate(unallocated_line)
    assert batch.available_quantity == 20

def test_cannot_allocate_if_skus_do_not_match():
    batch = Batch("B-001", "UNCOMFORTABLE-CHAIR", 100, eta=None)
    different_sku_line = OrderLine("L-123", "EXPENSIVE-TOASTER", 10)
    assert batch.can_allocate(different_sku_line) is False

def test_allocation_is_idempotent():
    # 幂等
    batch, line = make_batch_and_line("ANGULAR-DESK", 20, 2)
    batch.allocate(line)
    batch.allocate(line)
    assert batch.available_quantity == 18
