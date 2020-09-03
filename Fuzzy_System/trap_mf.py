import numpy as np


def trap_mf(x, params):
    if len(params) == 4:
        a, b, c, d = np.asarray(params)
        if a <= b <= c <= d:
            if type(x) is not np.ndarray:
                x = np.asarray([x])
            y = np.zeros(len(x))

            # Left slope
            if a != b:
                index = np.logical_and(a < x, x < b)
                y[index] = (x[index] - a) / (b - a)

            # Right slope
            if c != d:
                index = np.logical_and(c < x, x < d)
                y[index] = (d - x[index]) / (d - c)

            # Top
            index = np.logical_and(b <= x, x <= c)
            y[index] = 1

            return y

    raise Exception("Something is Wrong")
