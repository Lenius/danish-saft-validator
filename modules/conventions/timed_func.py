from functools import wraps
import datetime
from loguru import logger

def timed_func():
    def decorator(method):
        @wraps(method)
        def wrapped(*args, **kwargs):
            start = datetime.datetime.now()
            res = method(*args, **kwargs)
            delta = datetime.datetime.now() - start
            logger.info(f'{method.__name__}: {delta.total_seconds()} sec')
            return res

        return wrapped

    return decorator


import functools
import gc
import itertools
import math
import sys
import timeit


class TimeitResult(object):
    """
    Object returned by the timeit magic with info about the run.
    Contains the following attributes :
    loops: (int) number of loops done per measurement
    repeat: (int) number of times the measurement has been repeated
    best: (float) best execution time / number
    all_runs: (list of float) execution time of each run (in s)
    compile_time: (float) time of statement compilation (s)
    """

    def __init__(self, loops, repeat, best, worst, all_runs, precision):
        self.loops = loops
        self.repeat = repeat
        self.best = best
        self.worst = worst
        self.all_runs = all_runs
        self._precision = precision
        self.timings = [dt / self.loops for dt in all_runs]

    @property
    def average(self):
        return math.fsum(self.timings) / len(self.timings)

    @property
    def stdev(self):
        mean = self.average
        return (math.fsum([(x - mean) ** 2 for x in self.timings]) / len(self.timings)) ** 0.5

    def __str__(self):
        pm = '+-'
        if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
            try:
                u'\xb1'.encode(sys.stdout.encoding)
                pm = u'\xb1'
            except:
                pass
        return (
            u"{mean} {pm} {std} per loop (mean {pm} std. dev. of {runs} run{run_plural}, {loops} loop{loop_plural} each)"
                .format(pm=pm,
                        runs=self.repeat,
                        loops=self.loops,
                        loop_plural="" if self.loops == 1 else "s",
                        run_plural="" if self.repeat == 1 else "s",
                        mean=format_time(self.average, self._precision),
                        std=format_time(self.stdev, self._precision)))

    def _repr_pretty_(self, p, cycle):
        unic = self.__str__()
        p.text(u'<TimeitResult : ' + unic + u'>')


def format_time(timespan, precision=3):
    """Formats the timespan in a human readable form"""

    if timespan >= 60.0:
        # we have more than a minute, format that in a human readable form
        # Idea from http://snipplr.com/view/5713/
        parts = [("d", 60 * 60 * 24), ("h", 60 * 60), ("min", 60), ("s", 1)]
        time = []
        leftover = timespan
        for suffix, length in parts:
            value = int(leftover / length)
            if value > 0:
                leftover = leftover % length
                time.append(u'%s%s' % (str(value), suffix))
            if leftover < 1:
                break
        return " ".join(time)

    # Unfortunately the unicode 'micro' symbol can cause problems in
    # certain terminals.
    # See bug: https://bugs.launchpad.net/ipython/+bug/348466
    # Try to prevent crashes by being more secure than it needs to
    # E.g. eclipse is able to print a µ, but has no sys.stdout.encoding set.
    units = [u"s", u"ms", u'us', "ns"]  # the save value
    if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
        try:
            u'\xb5'.encode(sys.stdout.encoding)
            units = [u"s", u"ms", u'\xb5s', "ns"]
        except:
            pass
    scaling = [1, 1e3, 1e6, 1e9]

    if timespan > 0.0:
        order = min(-int(math.floor(math.log10(timespan)) // 3), 3)
    else:
        order = 3
    return u"%.*g %s" % (precision, timespan * scaling[order], units[order])


class Timer(timeit.Timer):
    """Timer class that explicitly uses self.inner
    which is an undocumented implementation detail of CPython,
    not shared by PyPy.
    """

    # Timer.timeit copied from CPython 3.4.2
    # @staticmethod
    # def empty(*args, **kwargs):

    def timeit(self, number=timeit.default_number, **kwargs):
        """Time 'number' executions of the main statement.
        To be precise, this executes the setup statement once, and
        then returns the time it takes to execute the main statement
        a number of times, as a float measured in seconds.  The
        argument is the number of times through the loop, defaulting
        to one million.  The main statement, the setup statement and
        the timer function to be used are passed to the constructor.
        """
        it = itertools.repeat(None, number)
        gcold = gc.isenabled()
        gc.disable()
        try:
            timing = self.inner(it, self.timer)
        finally:
            if gcold:
                gc.enable()
        return timing

def time_func(stmt, *args, verbose=True, repeat=3, number=0, print_precision=3, **kwargs):
    timer = Timer(timer=timeit.default_timer)

    def temp(_it, _timer, stmt, *args, **kwargs):
        _t0 = _timer()
        for _i in _it:
            stmt(*args, **kwargs)
        _t1 = _timer()
        return _t1 - _t0

    def inner(_it, _timer):
        return temp(_it, _timer, stmt, *args, **kwargs)

    timer.inner = inner

    # This is used to check if there is a huge difference between the
    # best and worst timings.
    # Issue: https://github.com/ipython/ipython/issues/6471

    # tic = time.time()
    if number == 0:
        # determine number so that 0.2 <= total time < 2.0
        for index in range(0, 10):
            number = 10 ** index
            # toc = time.time()
            time_number = timer.timeit(number)
            # print("toc:", time.time() - toc)
            if time_number >= 0.2:
                break
    # print(time.time() - tic)

    # tic = time.time()
    all_runs = timer.repeat(repeat, number)
    # print(time.time() - tic)

    best = min(all_runs) / number
    worst = max(all_runs) / number
    # timeit_result = TimeitResult(number, repeat, best, worst, all_runs, tc, precision)
    timeit_result = TimeitResult(number, repeat, best, worst, all_runs, print_precision)

    # Check best timing is greater than zero to avoid a
    # ZeroDivisionError.
    # In cases where the slowest timing is lesser than a micosecond
    # we assume that it does not really matter if the fastest
    # timing is 4 times faster than the slowest timing or not.
    if worst > 4 * best and best > 0 and worst > 1e-6:
        print("The slowest run took %0.2f times longer than the "
              "fastest. This could mean that an intermediate result "
              "is being cached." % (worst / best))

    if verbose:
        print(timeit_result)

    return timeit_result
def dec_timer(repeat=3, number=0, print_precision=3):
    def decorator_Timer(func):
        @functools.wraps(func)
        def wrapper_Timer(*args, **kwargs):
            time_func(func,
                      *args,
                      verbose=True,
                      repeat=repeat,
                      number=number,
                      print_precision=print_precision,
                      **kwargs)
            return func(*args, **kwargs)

        return wrapper_Timer

    return decorator_Timer