from typing import NewType


# el NewType original lo que hace es devolver el argumento cuando se llama,
# lo que me gustaria es que devuelva una instancia del supertype
class _NewType(NewType):
    def __call__(self, *args, **kwargs):
        return self.__supertype__(*args, **kwargs)
