from dataclasses import\
    dataclass


__all__ = ['comment']


@dataclass
class comment:
    value: str


def add_comment(value: str):
    def _add_to_definition(target: type):
        # esto va a cambiar, no se deberia poder acceder a la definicion directamente
        # esto deberia devolver una copia siempre
        definition = getattr(target, '__pg_definition')()
        assert definition['comment'] is None
        assert isinstance(value, str)
        definition['comment'] = comment(value)
        return target
    return _add_to_definition
