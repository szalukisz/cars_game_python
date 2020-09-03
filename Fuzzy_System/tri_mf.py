import numpy as np


def tri_mf(x, params):

    if len(params)==3:
        a,b,c = np.asarray(params)
        if a <= b <= c:
            if type(x) is not np.ndarray:
                x = np.asarray([x])
            y = np.zeros(len(x))

            if a != b:
                index = np.logical_and(a < x, x < b)
                y[index] = (x[index] - a) / (b - a)

            # Right slope
            if b != c:
                index = np.logical_and(b < x, x < c)
                y[index] = (c - x[index]) / (c - b)

            # Center
            y[x == b] = 1

            return y

    raise Exception("Something is Wrong")
