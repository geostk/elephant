"""
Functions to generate random spike trains.

Most of these functions were adapted from the NeuroTools stgen module, which was mostly written by Eilif Muller.

:copyright: Copyright 2015 by the Elephant team, see AUTHORS.txt.
:license: Modified BSD, see LICENSE.txt for details.
"""

from __future__ import division
import numpy as np
from quantities import ms, Hz, Quantity
from neo import SpikeTrain


def _homogeneous_process(interval_generator, args, mean_rate, t_start, t_stop, as_array):
    """
    Returns a spike train whose spikes are a realization of a random process generated by the function `interval_generator`
    with the given rate, starting at time `t_start` and stopping `time t_stop`.
    """
    def rescale(x):
        return (x / mean_rate.units).rescale(t_stop.units)

    n = int(((t_stop - t_start) * mean_rate).simplified)
    number = np.ceil(n + 3 * np.sqrt(n))
    if number < 100:
        number = min(5 + np.ceil(2 * n), 100)
    assert number > 4  # if positive, number cannot be less than 5
    isi = rescale(interval_generator(*args, size=number))
    spikes = np.cumsum(isi)
    spikes += t_start

    i = spikes.searchsorted(t_stop)
    if i == len(spikes):
        # ISI buffer overrun
        extra_spikes = []
        t_last = spikes[-1] + rescale(interval_generator(*args, size=1))[0]
        while t_last < t_stop:
            extra_spikes.append(t_last)
            t_last = t_last + rescale(interval_generator(*args, size=1))[0]
        # np.concatenate does not conserve units
        spikes = Quantity(
            np.concatenate((spikes, extra_spikes)).magnitude, units=spikes.units)
    else:
        spikes = spikes[:i]

    if as_array:
        spikes = spikes.magnitude
    else:
        spikes = SpikeTrain(
            spikes, t_start=t_start, t_stop=t_stop, units=spikes.units)

    return spikes


def homogeneous_poisson_process(rate, t_start=0.0 * ms, t_stop=1000.0 * ms, as_array=False):
    """
    Returns a spike train whose spikes are a realization of a Poisson process
    with the given rate, starting at time `t_start` and stopping time `t_stop`.

    All numerical values should be given as Quantities, e.g. 100*Hz.

    Parameters
    ----------

    rate : Quantity scalar with dimension 1/time
           The rate of the discharge.
    t_start : Quantity scalar with dimension time
              The beginning of the spike train.
    t_stop : Quantity scalar with dimension time
             The end of the spike train.
    as_array : bool
               If True, a NumPy array of sorted spikes is returned,
               rather than a SpikeTrain object.

    Examples
    --------
        >>> from quantities import Hz, ms
        >>> spikes = homogeneous_poisson_process(50*Hz, 0*ms, 1000*ms)
        >>> spikes = homogeneous_poisson_process(20*Hz, 5000*ms, 10000*ms, as_array=True)

    """
    mean_interval = 1 / rate
    return _homogeneous_process(np.random.exponential, (mean_interval,), rate, t_start, t_stop, as_array)


def homogeneous_gamma_process(a, b, t_start=0.0 * ms, t_stop=1000.0 * ms, as_array=False):
    """
    Returns a spike train whose spikes are a realization of a gamma process
    with the given parameters, starting at time `t_start` and stopping time `t_stop`.
    (average rate will be b/a).

    All numerical values should be given as Quantities, e.g. 100*Hz.

    Parameters
    ----------

    a : int or float
        The shape parameter of the gamma distribution.
    b : Quantity scalar with dimension 1/time
        The rate parameter of the gamma distribution.
    t_start : Quantity scalar with dimension time
              The beginning of the spike train.
    t_stop : Quantity scalar with dimension time
             The end of the spike train.
    as_array : bool
               If True, a NumPy array of sorted spikes is returned,
               rather than a SpikeTrain object.

    Examples
    --------
        >>> from quantities import Hz, ms
        >>> spikes = homogeneous_gamma_process(2.0, 50*Hz, 0*ms, 1000*ms)
        >>> spikes = homogeneous_gamma_process(5.0, 20*Hz, 5000*ms, 10000*ms, as_array=True)

    """
    rate = b / a
    k, theta = a, (1 / b)
    return _homogeneous_process(np.random.gamma, (k, theta), rate, t_start, t_stop, as_array)
