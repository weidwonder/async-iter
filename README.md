# AsyncIter (0.1.2)  

A async function tool supporting threading and gevent.  
You can easily make a group of functions run in the same time without worrying about 
thread maximum exceed.

# Installation

> pip install async-iter 

# Quickstart
Construct a multi-task `processor` by `AsyncIterHandler(<type>)`, then you can use the `processor`
to process the list of or dict of functions.

```python
import random
from time import sleep

from async_iter import AsyncIterHandler

async_iter = AsyncIterHandler('threading')  # using multi-threading
# async_iter = AsyncIterHandler('gevent')  # using gevent
# async_iter = AsyncIterHandler('fake')  # serial, using in debugging

def test_func(*args, **kws):  # a exhibition func
    x = random.randint(0, 1000)
    print('func', x, 'start:', args, kws)
    sleep(1)
    print('func', x, 'end', args, kws)
    return x


result_dict = async_iter({
    'some_key_A': (test_func,),
    'some_key_B': (test_func, ('some_args1',)),
    'some_key_C': (test_func, ('some_args2', 'some_args3'), {'some_dict_key': 'some_dict_value'}),
}, worker_limit=2)

print(result_dict)  # example: {'some_key_C': 152, 'some_key_B': 109, 'some_key_A': 497}

result_list = async_iter([
    (test_func,),
    (test_func, ('some_args1', 'some_args2')),
    (test_func, ('some_args3', 'some_args4'), {'some_dict_key': 'some_dict_value'}),
], worker_limit=2)

print(result_list)  # example: [798, 958, 882]
```

# DEBUG & PROFILING

The fake async\_iter allows you to profile your functions. If you uncomment above `async_iter = AsyncIterHandler('fake')`
then you will get a output like this:

Every line represents: 

> [key of function] : [time cost in microseconds] \> [time cost percent of entire task]

```txt
********** cost: 0.002495 (S) **********
some_key_C : 1068 > 42.81%
some_key_B : 1063 > 42.61%
some_key_A : 364 > 14.59%
{'some_key_C': 839, 'some_key_B': 318, 'some_key_A': 803}
********** cost: 0.002163 (S) **********
2 : 1058 > 48.91%
0 : 827 > 38.23%
1 : 278 > 12.85%
[575, 94, 346]
```
