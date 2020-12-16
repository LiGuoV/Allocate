import inspect
from typing import Callable

from allocation.adapters import redis_eventpublisher, orm, email
from allocation.adapters.notifications import AbsNotifications, EmailNotifications
from allocation.service_layer import unit_of_work, messagebus, handlers


def injected_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters
    deps = {
        name: dependency
        for name, dependency in dependencies.items()
        if name in params
    }
    return lambda message: handler(message, **deps)


def bootstrap(
        start_orm: bool = True,
        uow: unit_of_work.AbsUnitOfWork = unit_of_work.SqlAlchemyUnitOfWork(),
        notifications: AbsNotifications = EmailNotifications(),
        publish: Callable = redis_eventpublisher.publish,
) -> messagebus.MessageBus:
    if start_orm:
        orm.start_mappers()

    dependencies = {'uow': uow, 'notifications': notifications, 'publish': publish}
    injected_event_handlers = {
        event_type: [
            injected_dependencies(handler, dependencies)
            for handler in event_handlers

        ]
        for event_type, event_handlers in handlers.EVENT_HANDLERS.items()
    }
    injected_command_handlers = {
        command_type: injected_dependencies(handler, dependencies)
        for command_type, handler in handlers.COMMAND_HANDLERS.items()
    }

    return messagebus.MessageBus(
        uow=uow, event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
