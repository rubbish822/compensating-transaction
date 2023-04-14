import typing


class RollBackError(Exception):
    def __init__(
        self,
        detail: str,
        rollback: typing.Optional[typing.Callable],
        args: tuple = (),
        kwargs: dict = None,
    ):
        self.detail = detail
        self.rollback = rollback
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return f'detail: {self.detail} rollback: {self.rollback}, args: {self.args}, kwargs: {self.kwargs}'
