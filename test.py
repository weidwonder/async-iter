import random
from time import sleep

from multitasking import MultiTaskHandler

async_iter = MultiTaskHandler('threading')  # using multi-threading


# async_iter = MultiTaskHandler('gevent')  # using gevent
# async_iter = MultiTaskHandler('fake')  # serial, using in debugging

def test_func(*args, **kws):  # a exhibition func
    x = random.randint(0, 1000)
    # print 'func', x, 'start:', args, kws
    sleep(1)
    # print 'func', x, 'end', args, kws
    return x


result_dict = async_iter({
    'some_key_A': (test_func,),
    'some_key_B': (test_func, ('some_args1',)),
    'some_key_C': (test_func, ('some_args2', 'some_args3'), {'some_dict_key': 'some_dict_value'}),
}, worker_limit=2)

print result_dict  # example: {'some_key_C': 152, 'some_key_B': 109, 'some_key_A': 497}

result_list = async_iter([
    (test_func,),
    (test_func, ('some_args1', 'some_args2')),
    (test_func, ('some_args3', 'some_args4'), {'some_dict_key': 'some_dict_value'}),
], worker_limit=2)

print result_list  # example: [798, 958, 882]
