# compensating-transaction

When the function execution fails, the function execution can be rolled back, and all previous function executions can be rolled back
```
For Example:
    1. step1 -> step2 -> step3
        1). if step2 execution error:
            rollback step1
        2). if step3 execution error:
            rollback step2 -> rollback step1
    2. step1 -> step2 -> step3_1, step3_2, step3_3 -> step4
        1). if step3_2 execution error:
            rollback step3_1 -> rollback step2 -> rollback step1
        2). if step4 execution error:
            rollback step3_3 -> rollback step3_2 -> rollback step3_1 -> rollback step2 -> rollback step1
    
```
# Use Example:
```
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
```