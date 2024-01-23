# from psycopg2 import Warning, Error


class PGError(BaseException):
    pass


class PGInvalidOperationError(BaseException):
    pass


class PGOperationNotBuiltError(BaseException):
    pass
