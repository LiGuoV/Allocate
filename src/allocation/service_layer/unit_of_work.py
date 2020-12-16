from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from allocation import config
from allocation.adapters import repository


class AbsUnitOfWork:
    products : repository.AbsProductRepository

    def __exit__(self,*args):
        self.rollback()

    def __enter__(self):
        return self

    def rollback(self):
        pass

    def commit(self):
        self._commit()
        # self.publish_events()

    def _commit(self):
        pass

    # def publish_events(self):
    def collect_new_events(self):
        for product in self.products.seen:
            while product.events:
                yield product.events.pop(0)


DEFAULT_SESSION_FACTORY = sessionmaker(bind=create_engine(
    config.get_db_uri(),
    isolation_level='REPEATABLE READ'
))

class SqlAlchemyUnitOfWork(AbsUnitOfWork):

    def __init__(self,session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.products = repository.SqlAlchemyRepository(self.session)
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def rollback(self):
        self.session.rollback()

    def _commit(self):
        self.session.commit()

