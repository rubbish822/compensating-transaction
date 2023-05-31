import logging
import typing

from . import exceptions


logger = logging.getLogger(__name__)


class CompensatingTransaction:
    """
    When the function execution fails, the function execution can be rolled back,
    and all previous function executions can be rolled back
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
    
    """
    def __init__(self, rollback_raise_err: bool = False):
        self.rollback_raise_err = rollback_raise_err
        self.transactions = []
        self.submit_transactions = []
        self.errors = []

    def add(
        self,
        run_func: callable,
        run_args: tuple = (),
        run_kwargs: dict = None,
        rollback_func: typing.Optional[callable] = None,
        rollback_args: tuple = (),
        rollback_kwargs: dict = None,
        rollback_exe: typing.Optional[Exception] = None,
    ):
        """
        add transaction func
        Args:
            run_func (callable): execute function
            run_args (tuple, optional): _description_. Defaults to ().
            run_kwargs (dict, optional): _description_. Defaults to None.
            rollback_func (typing.Optional[callable], optional): rollback function. Defaults to None.
            rollback_args (tuple, optional): _description_. Defaults to ().
            rollback_kwargs (dict, optional): _description_. Defaults to None.
            rollback_exe (typing.Optional[Exception], optional): The specified rollback exception. Defaults to None.
            previous (typing.Optional[list], optional): previous node. Defaults to None.
        """
        transaction_instance = {
            'run_func': run_func,
            'run_args': run_args,
            'run_kwargs': run_kwargs or {},
            'rollback_func': rollback_func,
            'rollback_args': rollback_args,
            'rollback_kwargs': rollback_kwargs or {},
            'rollback_exe': rollback_exe,
        }
        self.transactions.append(transaction_instance)

    def run(self, transaction_instance: dict):
        """run transaction

        Args:
            transaction_instance (dict): _description_
        """
        run_func = transaction_instance['run_func']
        run_args = transaction_instance['run_args']
        run_kwargs = transaction_instance['run_kwargs']
        return run_func(*run_args, **run_kwargs)

    def rollback(self, transaction_instance: dict):
        """rollback transaction

        Args:
            transaction_instance (dict): _description_
        """
        rollback_func = transaction_instance['rollback_func']
        rollback_args = transaction_instance['rollback_args']
        rollback_kwargs = transaction_instance['rollback_kwargs']
        return rollback_func(*rollback_args, **rollback_kwargs)

    def transaction_rollback(self):
        """
        Roll back all committed transactions
        """
        for transaction_instance in reversed(self.submit_transactions):
            try:
                self.rollback(transaction_instance)
            except Exception as err:
                logger.error(
                    '[transaction_rollback] %s, Exception: %s', transaction_instance, err
                )
                self.errors.append(
                    f'[transaction_rollback] {transaction_instance}, Exception: {err}'
                )
                if self.rollback_raise_err:
                    raise err from err

    def submit(self) -> typing.Optional[exceptions.TransactionError]:
        """
        submit transaction
        """
        self.submit_transactions = []
        for transaction_instance in self.transactions:
            rollback_exe = transaction_instance['rollback_exe']
            try:
                self.run(transaction_instance)
            except Exception as err:
                if rollback_exe and isinstance(err, rollback_exe):
                    # 指定不回滚异常
                    continue
                self.errors.append(f'[submit] {transaction_instance}, err: {err}')
                self.transaction_rollback()
                break
            else:
                self.submit_transactions.append(transaction_instance)
                logger.info('[submit] %s', transaction_instance)
        if self.errors:
            return exceptions.TransactionError(self.errors)
