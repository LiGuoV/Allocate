from sqlalchemy import MetaData, Table, Column, event
import sqlalchemy as sa
from allocation.domain.model import *

from sqlalchemy.orm import relationship, mapper

metadata = MetaData()

order_lines = Table(
    'order_lines', metadata,
    Column('id', sa.Integer, primary_key=True, autoincrement=True),
    Column('order_id', sa.String),
    Column('sku', sa.String),
    Column('qty', sa.Integer),
)

batches = Table(
    'batches', metadata,
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('ref', sa.String, unique=True),
    sa.Column('sku', sa.ForeignKey('products.sku')),
    sa.Column('_purchased_quantity', sa.Integer, ),
    sa.Column('eta', sa.Date, ),
)
allocations = Table(
    'allocations', metadata,
    sa.Column('batch_id', sa.ForeignKey('batches.id')),
    sa.Column('orderline_id', sa.ForeignKey('order_lines.id')),
)

# products = Table(
#     'products',metadata,
#     sa.Column('sku',sa.String,primary_key=True,)
# )
products = Table(
    'products', metadata,
    sa.Column('sku', sa.String(255), primary_key=True),
    sa.Column('version_number', sa.Integer, server_default='0', )
    # Column('version_number', Integer, nullable=False, server_default='0'),
)

allocations_view = Table(
    'allocations_view',metadata,
    sa.Column('orderid',sa.String,),
    sa.Column('sku',sa.String,),
    sa.Column('batchref',sa.String,)
)

def start_mappers():
    order_line_mapper = mapper(OrderLine, order_lines)
    batche_mapper = mapper(
        Batch, batches, properties={
            'allocations': relationship(
                order_line_mapper,
                secondary=allocations,
                collection_class=set, )
        })

    mapper(
        Product, products, properties={
            'batches': relationship(
                batche_mapper
            )
        })


@event.listens_for(Product, 'load')
def recived_load(product, _):
    product.events = []
