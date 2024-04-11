cdef extern from "DDC.h":
    int test()


def pytest() -> int:
    return test()