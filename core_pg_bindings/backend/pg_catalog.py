import core_pg_bindings.backend.cpp.module.wrapper as pw
from core_pg_bindings.metaclasses.builtin import builtin


class int1(pw.int1, metaclass=builtin):
    pass


class bool(pw.boolean, metaclass=builtin):
    pass


class int2(pw.int2, metaclass=builtin):
    pass


class int4(pw.int4, metaclass=builtin):
    pass


class int8(pw.int8, metaclass=builtin):
    pass


class float4(pw.float4, metaclass=builtin):
    pass


class float8(pw.float8, metaclass=builtin):
    pass


class text(pw.text, metaclass=builtin):
    pass


class timestamptz(pw.timestamptz, metaclass=builtin):
    pass


class date(pw.date, metaclass=builtin):
    pass
