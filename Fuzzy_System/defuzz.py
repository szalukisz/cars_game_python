import numpy as np

np.seterr('raise')

def defuzz(x, y, def_method):
    if def_method == 'centroid':     # _ specific gravity
        total_area = sum(y)
        if total_area!= 0:
            return sum(y * x) / total_area
        else:
            return 0
    elif def_method == 'mom':        # _ middle of maximum
        return np.mean(x[y == max(y)])
    elif def_method == 'lom':        # _ last maximum
        tmp = x[y == max(y)]
        which = np.argmax(abs(tmp))
        return tmp[which]
    else:
        raise ValueError("Incorrect value of 'def_method'")
