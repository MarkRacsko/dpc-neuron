import numpy as np
cimport numpy as cnp
import math


def smooth(cnp.ndarray[cnp.float64_t, ndim=1] array, int window_size = 5):
    """This function performs a sliding window type smoothing on an array representing an individual Ca trace.

    Args:
        array (np.ndarray): The array to be smoothed. Must be 1-dimensional.
        window_size (int, optional): The average of this many elements will be taken for the smoothing. Defaults to 5,
        it should be an odd number, and not larger than the square root of the array's length (ie. the length of the
        measurement in frames).

    Raises:
        ValueError: If the input array is of the incorrect shape, or the selected window_size is too large or it isn't odd.

    Returns:
        np.ndarray: The smoothed array.
    """
    # these checks are strictly speaking not necessary in this project, but their performance impact should be minimal
    # so I'm keeping them as a reminder (the user has no control over the array dimensions, and the window_size is also
    # validated elsewhere)

    cdef int length = array.shape[0]
    cdef int sliding_size = window_size // 2 + 1
    cdef int half_size = window_size // 2
    cdef int sliding_index = 0
    cdef cnp.ndarray[cnp.float64_t, ndim=1] out_array = np.zeros_like(array)
    dont_touch = set()  # This is a set for fast membership checking.
    
    while sliding_size < window_size:
        # This loop handles the edges of the array where we want to take the mean of fewer than window_size number of elements.
        out_array[sliding_index] = array[:sliding_size].mean()
        out_array[length - sliding_index - 1] = array[-sliding_size:].mean()
        dont_touch.add(sliding_index)
        dont_touch.add(length - sliding_index - 1)
        sliding_index += 1
        sliding_size += 1

    cdef int index
    for index in range(length):
        # This loop handles the middle parts where all elements required for a mean-window_size smoothing exist.
        if index in dont_touch:
            continue
        else:
            out_array[index] = array[index - half_size : index + half_size + 1].mean()

    return out_array