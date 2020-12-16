import logging
from typing import Dict, List, Callable, Type, Union

# from tenacity import Retrying,RetryError,stop_after_attempt,wait_exponential
from allocation.domain import commands, events
from allocation.service_layer import handlers, unit_of_work
from allocation.service_layer.handlers import EVENT_HANDLERS, COMMAND_HANDLERS

Message = Union[commands.Command, events.Event]
logger = logging.getLogger(__name__)


class MessageBus:
    def __init__(
            self,
            uow:unit_of_work.AbsUnitOfWork,
            event_handlers:Dict[Type[events.Event],List[Callable]],
            command_handlers:Dict[Type[commands.Command],Callable]
                 ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers


    def handle(self,message: Message):
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message)
            elif isinstance(message, commands.Command):

                self.handle_command(message)
            else:
                raise Exception(f'{message} was not an Event or Command')

    def handle_event(self,event:events.Event ):
        for handler in self.event_handlers[type(event)]:
            try:
                logger.debug(f'handling command {event}')
                handler(event)
                self.queue.extend(self.uow.collect_new_events())
            except Exception:
                logger.exception(f'Exception handing event {event}')
                continue


    def handle_command(self,command:commands.Command ):
        logger.debug(f'handling command {command}')
        try:
            handler = self.command_handlers[type(command)]
            handler(command)
            self.queue.extend(self.uow.collect_new_events())
        except Exception:
            logger.exception(f'Exception handing command {command}')
            raise







