def test_rollback():
    from compensating_transaction.transaction import CompensatingTransaction

    l = []

    def add_item(name):
        if name == 'l7':
            raise ValueError('not l7')
        l.append(name)

    def sub_item(name):
        if name in l:
            l.remove(name)
        print(f'run sub_item: {name}')
        return f'sub_item: {name}'

    step1 = CompensatingTransaction(
        run_func=add_item,
        run_args=('l1',),
        rollback_func=sub_item,
        rollback_args=('l1',),
    )
    step1.run()
    step2 = CompensatingTransaction(
        run_func=add_item,
        run_args=('l2',),
        rollback_func=sub_item,
        rollback_args=('l2',),
        previous=step1,
    )
    step2.run()
    step3 = CompensatingTransaction(
        run_func=add_item,
        run_args=('l3',),
        rollback_func=sub_item,
        rollback_args=('l3',),
        previous=step2,
        rollback_exe=AttributeError,
    )
    step3.run()
    step4 = CompensatingTransaction(
        run_func=add_item,
        run_args=('l4',),
        rollback_func=sub_item,
        rollback_args=('l4',),
        previous=step3,
        rollback_exe=AttributeError,
    )
    step4.run()
    step4_1 = CompensatingTransaction(
        run_func=add_item,
        run_args=('l4-1',),
        rollback_func=sub_item,
        rollback_args=('l4-1',),
        previous=step3,
        rollback_exe=AttributeError,
    )
    step4_1.run()
    step5 = CompensatingTransaction(
        run_func=add_item,
        run_args=('l5',),
        rollback_func=sub_item,
        rollback_args=('l5',),
        previous=[step4, step4_1],
        rollback_exe=AttributeError,
    )
    step5.run()
    assert l == ['l1', 'l2', 'l3', 'l4', 'l4-1', 'l5']
    step5.rollback_all()
    assert l == []
    list1 = ['l6', 'l7']
    last_step = None
    for item in list1:
        step6 = CompensatingTransaction(
            run_func=add_item,
            run_args=(item,),
            rollback_func=sub_item,
            rollback_args=(item,),
            previous=step5 if not last_step else last_step,
        )
        last_step = step6
        # try:
        #     step6.run()
        # except Exception:
        #     step6.rollback_all(True)
        try:
            step6.run(auto_rollback=True, rollback_all=True)
        except Exception:
            pass
    assert l == []
