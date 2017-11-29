import numpy as np
import numpy.matlib


def generate_load():
    size = 300
    a = np.matlib.rand(size, size)
    b = np.matlib.rand(size, size)
    c = np.matmul(a, b)
    return c.tostring()
