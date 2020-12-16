from dataclasses import dataclass

@dataclass
class Event:
    pass


@dataclass
class OutOfStock(Event):
    # 超出库存
    sku: str

@dataclass
class Allocated(Event):
    orderid:str
    sku:str
    qty:int
    batchref:str

@dataclass
class Deallocated(Event):
    orderid:str
    sku:str
    qty:int