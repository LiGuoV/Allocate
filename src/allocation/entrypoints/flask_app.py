from datetime import datetime

from allocation.domain import commands
from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from allocation import bootstrap,views
from allocation import config
from allocation.adapters import orm
from allocation.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from allocation.service_layer import messagebus, handlers

app = Flask(__name__)

# orm.start_mappers()
bus = bootstrap.bootstrap()


@app.route('/allocate', methods=['POST'])
def allocate():
    orderid, sku, qty = request.json['orderid'], request.json['sku'], request.json['qty'],

    # uow = SqlAlchemyUnitOfWork()
    try:
        cmd = commands.Allocate(orderid, sku, qty)
        bus.handle(cmd)
        # messagebus.handle(cmd, uow)
        # batchref = rsts.pop(0)
    except (handlers.InvalidSku,) as e:
        return jsonify({'message': str(e)}), 400

    # 读写分离
    # return jsonify({'batchref': batchref}), 201
    return 'OK', 202


@app.route('/add_batch', methods=['POST'])
def add_batch():

    eta = request.json['eta']
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    cmd = commands.CreateBatch(
        request.json['ref'],
        request.json['sku'],
        request.json['qty'],
        eta
    )
    bus.handle(cmd)
    # uow = SqlAlchemyUnitOfWork()
    # messagebus.handle(cmd, uow)

    # handlers.add_batch(
    #     request.json['ref'], request.json['sku'], request.json['qty'], eta,
    #     uow)
    return 'OK', 201


# @app.route('/deallocate', methods=['POST'])
# def deallocate():
#     orderid, sku = request.json['orderid'], request.json['sku'],
#     batchref = services.deallocate(orderid, sku, repo, session)
#     return jsonify({'batchref': batchref}), 200

@app.route('/allocations/<orderid>',methods=['GET'])
def allocations_view_endpoint(orderid):
    uow = SqlAlchemyUnitOfWork()
    result = views.allocations(orderid,uow)
    if not result:
        return 'not fount', 404
    return jsonify(result), 200

# if __name__ == '__main__':
#     app.run(port=5005, debug=True)
