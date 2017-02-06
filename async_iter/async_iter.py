import datetime

import operator

__version__ = '0.1.2'

try:
    import Queue
except ImportError:
    import queue as Queue
import threading


class ThreadPool:
    """
    Customized thread pool
    """

    class TreadPoolException(Exception):
        pass

    class NULLKEY:
        pass

    def __init__(self, worker_limit):
        self.task_queue = Queue.Queue(maxsize=worker_limit)
        self.result_dict = {}
        self.is_join = False

    def setup_func(self, key, func, *args, **kws):
        """ wrap the function, redirect the output to the `result_dict`.
        """

        def func_wrap():
            self.result_dict[key] = func(*args, **kws)
            # mark one position in queue is available.
            self.task_queue.get()
            self.task_queue.task_done()

        def func_origin():
            func(*args, **kws)
            self.task_queue.get()
            self.task_queue.task_done()

        if key is not self.NULLKEY:
            return func_wrap
        else:
            return func_origin

    def putting_task(self, func, *args, **kws):
        """ put task to the queue
        """
        if self.is_join:
            raise self.TreadPoolException('Thread pool is closed.')
        result_id = kws.pop('_result_id', self.NULLKEY)
        task = self.setup_func(result_id, func, *args, **kws)
        # mark one position in queue has been taken.
        self.task_queue.put(True)
        self.execute_task(task)

    def execute_task(self, task):
        """ execute task by start new thread.
        """
        t = threading.Thread(target=task)
        t.start()

    def join(self):
        """ wait until all tasks in task_queue done.
        """
        self.is_join = True
        self.task_queue.join()


class AsyncIterHandler:
    """ multi-task handler
    """

    @staticmethod
    def _multitasking_threading(task_iter, worker_limit=4):
        """ multi-task using threading
        :param dict/list task_iter: task dict or list.
        :param int worker_limit: thread worker limit in the same time
        :return: result dict or list
        """
        if isinstance(task_iter, dict):
            iter_type = 'dict'
        elif isinstance(task_iter, list):
            iter_type = 'list'
        else:
            raise ValueError('Param `task_iter` must be a list or a dict object.')
        if iter_type == 'dict':
            iters = task_iter.items()
        else:
            iters = enumerate(task_iter)
        pool = ThreadPool(worker_limit=worker_limit)
        for k, v in iters:
            assert len(
                v) <= 3, 'Length of list as the value in dict cant be longer than 3.'
            v = {
                1: list(v) + [(), {}],
                2: list(v) + [{}],
                3: v,
            }.get(len(v))
            func, args, kws = v
            kws['_result_id'] = k
            pool.putting_task(func, *args, **kws)
        pool.join()
        out_dict = pool.result_dict
        if iter_type == 'list':
            out_iter = [None] * len(task_iter)
            for i in range(len(out_iter)):
                out_iter[i] = out_dict[i]
        else:
            out_iter = out_dict
        return out_iter

    @staticmethod
    def _multitasking_gevent(task_iter, **kwargs):
        """ multi-task using gevent
        :param dict/list task_iter: task dict or list.
        :return: result dict or list
        """
        import gevent
        if isinstance(task_iter, dict):
            iter_type = 'dict'
        elif isinstance(task_iter, list):
            iter_type = 'list'
        else:
            raise ValueError('Param `task_iter` must be a list or a dict object.')
        if iter_type == 'dict':
            iters = task_iter
        else:
            iters = dict(enumerate(task_iter))
        for k, v in iters.iteritems():
            assert len(
                v) <= 3, 'Length of list as the value in dict cant be longer than 3.'
            v = {
                1: list(v) + [(), {}],
                2: list(v) + [{}],
                3: v,
            }.get(len(v))
            func, args, kws = v
            new_v = gevent.spawn(func, *args, **kws)
            iters[k] = new_v
        gevent.joinall(iters.values())
        for k, v in iters.iteritems():
            task_iter[k] = v.value
        return iters

    @staticmethod
    def _multitasking_fake(task_iter, **kwargs):
        """ fake multi-task for debugging, it's sync actually
        """
        time_list = []
        if isinstance(task_iter, dict):
            out_iter = {}
            iter_type = 'dict'
        elif isinstance(task_iter, list):
            out_iter = [None] * len(task_iter)
            iter_type = 'list'
        else:
            raise ValueError('Param `task_iter` must be a list or a dict object.')
        if iter_type == 'dict':
            iter_items = task_iter.items()
        else:
            iter_items = enumerate(task_iter)
        for k, v in iter_items:
            assert len(
                v) <= 3, 'Length of list as the value in dict cant be longer than 3.'
            v = {
                1: list(v) + [(), {}],
                2: list(v) + [{}],
                3: v,
            }.get(len(v))
            func, args, kws = v
            start = datetime.datetime.now()
            out_iter[k] = func(*args, **kws)
            end = datetime.datetime.now()
            time_list.append((k, (end - start).microseconds))
        time_list.sort(key=operator.itemgetter(1), reverse=True)
        all_time = float(sum([_[1] for _ in time_list]))
        print '*' * 10, 'cost:', all_time / 1e6, '(S)', '*' * 10
        for t in time_list:
            print t[0], ':', t[1], '>', str(round(t[1] / all_time * 100, 2)) + '%'
        return out_iter

    HANDLER_TYPES = {
        'threading': _multitasking_threading,
        'gevent': _multitasking_gevent,
        'fake': _multitasking_fake,
    }

    def __init__(self, handler_type='threading'):
        self.set_type(handler_type)

    def __call__(self, task_iter, **kwargs):
        """ multi-task processing
        :param dict/list task_iter: task dict or list.
        :param int worker_limit: thread worker limit in the same time
        :return: result dict or list
        """
        return self.handler(task_iter, **kwargs)

    def set_type(self, handler_type):
        """ set multi-task handler type.
        :param str handler_type: handler type, must be one of the key in HANDLER_TYPES.
        """
        try:
            self.handler = self.HANDLER_TYPES[handler_type].__func__
        except KeyError:
            handler_names = ', '.join(['"%s"' % t for t in self.HANDLER_TYPES.keys()])
            raise ValueError(u'Unsupported handler_type %s, options are %s.' %
                             (handler_type, handler_names))
