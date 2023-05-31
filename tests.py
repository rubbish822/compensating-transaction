from compensating_transaction.transaction import CompensatingTransaction
from compensating_transaction.exceptions import TransactionError


def test_add():
    number = 0

    def add():
        nonlocal number
        number += 1

    def add2():
        if 1:
            raise ValueError('error')

    def sub():
        print('sub')
        nonlocal number
        number -= 1
        print(f'sub: {number}')

    t = CompensatingTransaction(rollback_raise_err=True)
    t.add(run_func=add, rollback_func=sub)
    t.add(run_func=add, rollback_func=sub)
    t.add(run_func=add, rollback_func=sub)
    t.add(run_func=add2, rollback_func=sub)
    res = t.submit()
    assert isinstance(res, TransactionError)
    assert number == 0
