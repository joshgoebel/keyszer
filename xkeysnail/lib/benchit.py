import time
def benchit(fn):
    def fni(*args):
        a = time.perf_counter_ns()
        fn(*args)
        b = time.perf_counter_ns()
        print((b-a)//1000,"us")

    return fni
