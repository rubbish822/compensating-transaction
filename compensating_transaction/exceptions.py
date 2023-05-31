import typing


class TransactionError(Exception):
    def __init__(self, detail: typing.Union[list, str]):
        self.detail = detail

    def __str__(self):
        return f'TransactionError detail: {self.detail}'
