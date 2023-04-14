import hashlib
import typing
from dataclasses import dataclass

from . import exceptions


@dataclass
class RollBack:
    value: typing.Optional[typing.Any] = None


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
    ```
    def add_item(name):
        if name == 'l1':
            raise ValueError()
        l.append(name)

    def sub_item(name):
        l.remove(name)

    p1 = CompensatingTransaction(run_func=add_item, run_args=('l1',), rollback_func=sub_item, rollback_args=('l1', ))
    p2 = CompensatingTransaction(run_func=add_item, run_args=('l2',), rollback_func=sub_item, rollback_args=('l2', ), previous=p1)
    p3 = CompensatingTransaction(run_func=add_item, run_args=('l3',), rollback_func=sub_item, rollback_args=('l3', ), previous=[p1,p2])
    try:
        p1.run()
    except Exception:
        pass
    p1.rollback()
    p2.run(auto_rollback=False)  # l = ['l2']
    p2.rollback()  # l = []
    try:
        p3.run()
    except Exception:
        p3.rollback_all(ignore_exe=True)
    ```
    """

    def __init__(
        self,
        run_func: callable,
        run_args: tuple = (),
        run_kwargs: dict = None,
        rollback_func: typing.Optional[callable] = None,
        rollback_args: tuple = (),
        rollback_kwargs: dict = None,
        rollback_exe: typing.Optional[Exception] = None,
        previous: typing.Optional[list] = None,
    ):
        """

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
        self.run_func = run_func
        self.run_args = run_args
        self.run_kwargs = run_kwargs
        self.rollback_func = rollback_func
        self.rollback_args = rollback_args
        self.rollback_kwargs = rollback_kwargs
        self.rollback_exe = rollback_exe
        self.previous = previous
        self._is_success = None
        if self.run_kwargs is None:
            self.run_kwargs = {}
        if self.rollback_kwargs is None:
            self.rollback_kwargs = {}

    def run(self, auto_rollback: bool = False, rollback_all: bool = False):
        try:
            res = self.run_func(*self.run_args, **self.run_kwargs)
        except Exception as err:
            self._is_success = False
            if auto_rollback:
                # After the execution fails, the upper-level operation is automatically rolled back
                if self.rollback_exe and not isinstance(err, self.rollback_exe):
                    # Specify the rollback exception type, only the exception
                    # type will perform the rollback operation
                    return RollBack('ignore exe')
                if not rollback_all:
                    self.previous_rollback()
                else:
                    self.rollback_all()
            raise err
        else:
            self._is_success = True
            return res

    def previous_rollback(self):
        """
        previous rollback
        """
        if self.previous:
            if isinstance(self.previous, list):
                for previous in self.previous:
                    previous.rollback()
            elif isinstance(self.previous, self.__class__):
                self.previous.rollback()
        return True

    def rollback_all(self, ignore_exe: bool = False) -> list:
        """rollback all

        Args:
            ignore_exe (bool, optional): Whether to ignore the rollback exception,
                and continue to roll back other exceptions. Defaults to False.

        Raises:
            err: _description_

        Returns:
            list: [Rollback result, Rollback exception details]
        """
        if self.rollback_func and self._is_success is True:
            self.rollback_func(*self.rollback_args, **self.rollback_kwargs)
        all_previous_rollback = self.get_all_rollback()
        rollback_exe = []
        for previous_func_dict in all_previous_rollback:
            rollback_func = previous_func_dict['rollback_func']
            args = previous_func_dict['args']
            kwargs = previous_func_dict['kwargs']
            try:
                rollback_func(*args, **kwargs)
            except Exception as err:
                if not ignore_exe:
                    raise exceptions.RollBackError(
                        str(err), rollback_func, args, kwargs
                    ) from err
                else:
                    rollback_exe.append([previous_func_dict, str(err)])
        return not bool(rollback_exe), rollback_exe

    def get_all_rollback(self) -> list:
        """
        Traverse all superior rollback functions
        """
        all_rollback = []
        hash_set = set()
        all_previous_instance = self.previous
        while all_previous_instance:
            if isinstance(all_previous_instance, self.__class__):
                all_previous_instance = [all_previous_instance]
            _all_previous_instance = []
            for previous_instance in all_previous_instance:
                if (
                    previous_instance.rollback_func
                    and previous_instance._is_success is True
                ):
                    hash_key = (
                        f'{previous_instance.rollback_func}:{previous_instance}:'
                        + f'{previous_instance.rollback_args}:{previous_instance.rollback_kwargs}'
                    )
                    hash_key = hashlib.md5(hash_key.encode()).hexdigest()
                    if hash_key not in hash_set:
                        all_rollback.append(
                            {
                                'rollback_func': previous_instance.rollback_func,
                                'self': previous_instance,
                                'args': previous_instance.rollback_args,
                                'kwargs': previous_instance.rollback_kwargs,
                            }
                        )
                        hash_set.add(hash_key)
                if previous_instance.previous:
                    if isinstance(previous_instance.previous, list):
                        _all_previous_instance.extend(previous_instance.previous)
                    else:
                        _all_previous_instance.append(previous_instance.previous)
            all_previous_instance = _all_previous_instance
        return all_rollback

    def rollback(self):
        """rollback
        1. If the current run_func function is successfully executed, the rollback operation is performed,
        otherwise it is not executed.
        2. If the current run_func function is successfully executed, execute the upper-level rollback operation,
          otherwise it will not execute.

        Returns:
            _type_: RollBack(True) rollback result
        """
        res = True
        if self.rollback_func and self._is_success is True:
            # The rollback of the current operation can only be performed after the current operation is
            # successfully executed
            self.rollback_func(*self.rollback_args, **self.rollback_kwargs)
        if self.previous:
            # When performing a rollback, automatically perform a superior rollback
            self.previous_rollback()
        return RollBack(res)
