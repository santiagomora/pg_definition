from dataclasses import\
    dataclass


__all__ = ['add_comment', 'add_field_comment']


@dataclass
class comment:
    value: str


class add_comment:
    def __init__(self, *, value: str):
        self.value = value

    def __call__(self, target: type):
        definition = target._postgres_definition
        assert definition['comment'] is None
        definition['comment'] = comment(self.value)
        return target


class add_field_comment:
    def __init__(self, *, field_name: str, value: str, accessor: str):
        self.value = value
        self.field_name = field_name
        self.accessor = accessor

    def __call__(self, target: type):
        # esto va a cambiar, no se deberia poder acceder a la definicion directamente
        # esto deberia devolver una copia siempre
        assert target._postgres_definition[self.accessor][self.field_name]['comment'] is None
        target._postgres_definition[self.accessor][self.field_name]['comment'] = comment(self.value)
        return target
