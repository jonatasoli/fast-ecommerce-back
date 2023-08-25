import abc


class AbstractPublish(abc.ABC):   # noqa: B024
    ...


class RabbitMQPublish(AbstractPublish):
    ...


class MemoryPublish(AbstractPublish):
    ...
