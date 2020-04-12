'''
Misc
'''
from __future__ import absolute_import, division, print_function
import sys
import collections
from wafo import numba_misc
import fractions
import numpy as np
from numpy import (amax, logical_and, arange, linspace, atleast_1d,
                   asarray, ceil, floor, frexp, hypot,
                   sqrt, arctan2, sin, cos, exp, log, log1p, mod, diff,
                   inf, pi, interp, isscalar, zeros, ones,
                   sign, unique, hstack, vstack, nonzero, where, extract,
                   meshgrid)
from scipy.special import gammaln  # pylint: disable=no-name-in-module
from scipy.integrate import trapz, simps
import warnings
from time import strftime, gmtime
from wafo.plotbackend import plotbackend as plt
import numbers
try:
    from wafo import c_library as clib  # @UnresolvedImport
except ImportError:
    warnings.warn('c_library not found. Check its compilation.')
    clib = None
FLOATINFO = np.finfo(float)
_TINY = FLOATINFO.tiny
_EPS = FLOATINFO.eps

__all__ = ['now', 'spaceline', 'narg_smallest', 'args_flat', 'is_numlike',
           'JITImport', 'DotDict', 'Bunch', 'printf', 'sub_dict_select',
           'parse_kwargs', 'detrendma', 'ecross', 'findcross', 'findextrema',
           'findpeaks', 'findrfc', 'rfcfilter', 'findtp', 'findtc',
           'findoutliers', 'common_shape', 'argsreduce', 'stirlerr',
           'getshipchar',
           'betaloge', 'gravity', 'nextpow2', 'discretize',
           'polar2cart', 'cart2polar', 'pol2cart', 'cart2pol',
           'meshgrid', 'ndgrid', 'trangood', 'tranproc',
           'plot_histgrm', 'num2pistr', 'test_docstrings',
           'lazywhere', 'lazyselect',
           'valarray', 'lfind',
           'moving_average',
           'piecewise',
           'check_random_state']


def xor(a, b):
    """
    Return True only when inputs differ.
    """
    return a ^ b


def lfind(haystack, needle, maxiter=None):
    """Return indices to the maxiter first needles in the haystack as an iterable generator.

    Parameters
    ----------
    haystack: list or tuple of items
    needle: item to find
    maxiter: scalar integer maximum number of occurences

    Returns
    -------
    indices_gen: generator object

    Example
    ------
    >>> haystack = (1, 3, 4, 3, 10, 3, 1, 2, 5, 7, 10)
    >>> list(lfind(haystack, 3))
    [1, 3, 5]
    >>> [i for i in lfind(haystack, 3, 2)]
    [1, 3]
    >>> [i for i in lfind(haystack, 0, 2)]
    []
    """
    maxiter = inf if maxiter is None else maxiter
    ix = -1
    i = 0
    while i < maxiter:
        i += 1
        try:
            ix = haystack.index(needle, ix + 1)
            yield ix
        except (ValueError, KeyError):
            break


def check_random_state(seed):
    """Turn seed into a np.random.RandomState instance

    If seed is None (or np.random), return the RandomState singleton used
    by np.random.
    If seed is an int, return a new RandomState instance seeded with seed.
    If seed is already a RandomState instance, return it.
    Otherwise raise ValueError.

    Example
    -------
    >>> check_random_state(seed=None)
    <mtrand.RandomState object at ...
    >>> check_random_state(seed=1)
    <mtrand.RandomState object at ...
    >>> check_random_state(seed=np.random.RandomState(1))
    <mtrand.RandomState object at ...

    check_random_state(seed=2.5)
    """
    if seed is None or seed is np.random:
        return np.random.mtrand._rand
    if isinstance(seed, (numbers.Integral, np.integer)):
        return np.random.RandomState(seed)
    if isinstance(seed, np.random.RandomState):
        return seed
    msg = '{} cannot be used to seed a numpy.random.RandomState instance'
    raise ValueError(msg.format(seed))


def valarray(shape, value=np.nan, typecode=None):
    """Return an array of all value.
    """
    return np.full(shape, fill_value=value, dtype=typecode)


def piecewise(condlist, funclist, xi=None, fillvalue=0.0, args=(), **kw):
    """
    Evaluate a piecewise-defined function.

    Given a set of conditions and corresponding functions, evaluate each
    function on the input data wherever its condition is true.

    Parameters
    ----------
    condlist : list of bool arrays
        Each boolean array corresponds to a function in `funclist`.  Wherever
        `condlist[i]` is True, `funclist[i](x0,x1,...,xn)` is used as the
        output value. Each boolean array in `condlist` selects a piece of `xi`,
        and should therefore be of the same shape as `xi`.

        The length of `condlist` must correspond to that of `funclist`.
        If one extra function is given, i.e. if
        ``len(funclist) - len(condlist) == 1``, then that extra function
        is the default value, used wherever all conditions are false.
    funclist : list of callables, f(*(xi + args), **kw), or scalars
        Each function is evaluated over `x` wherever its corresponding
        condition is True.  It should take an array as input and give an array
        or a scalar value as output.  If, instead of a callable,
        a scalar is provided then a constant function (``lambda x: scalar``) is
        assumed.
    xi : tuple
        input arguments to the functions in funclist, i.e., (x0, x1,...., xn)
    fillvalue : scalar
        fillvalue for out of range values. Default 0.
    args : tuple, optional
        Any further arguments given here passed to the functions
        upon execution, i.e., if called ``piecewise(..., ..., args=(1, 'a'))``,
        then each function is called as ``f(x0, x1,..., xn, 1, 'a')``.
    kw : dict, optional
        Keyword arguments used in calling `piecewise` are passed to the
        functions upon execution, i.e., if called
        ``piecewise(..., ..., lambda=1)``, then each function is called as
        ``f(x0, x1,..., xn, lambda=1)``.

    Returns
    -------
    out : ndarray
        The output is the same shape and type as x and is found by
        calling the functions in `funclist` on the appropriate portions of `x`,
        as defined by the boolean arrays in `condlist`.  Portions not covered
        by any condition have undefined values.


    See Also
    --------
    choose, select, where

    Notes
    -----
    This is similar to choose or select, except that functions are
    evaluated on elements of `xi` that satisfy the corresponding condition from
    `condlist`.

    The result is::

          |--
          |funclist[0](x0[condlist[0]],x1[condlist[0]],...,xn[condlist[0]])
    out = |funclist[1](x0[condlist[1]],x1[condlist[1]],...,xn[condlist[1]])
          |...
          |funclist[n2](x0[condlist[n2]], x1[condlist[n2]],..,xn[condlist[n2]])
          |--

    Examples
    --------
    Define the sigma function, which is -1 for ``x < 0`` and +1 for ``x >= 0``.

    >>> x = np.linspace(-2.5, 2.5, 6)
    >>> np.allclose(piecewise([x < 0, x >= 0], [-1, 1]),
    ...    [-1, -1, -1,  1,  1,  1])
    True

    Define the absolute value, which is ``-x`` for ``x <0`` and ``x`` for
    ``x >= 0``.

    >>> np.allclose(piecewise([x < 0, x >= 0], [lambda x: -x, lambda x: x], xi=(x,)),
    ...            [ 2.5,  1.5,  0.5,  0.5,  1.5,  2.5])
    True

    Define the absolute value, which is ``-x*y`` for ``x*y <0`` and ``x*y`` for
    ``x*y >= 0``
    >>> X, Y = np.meshgrid(x, x)
    >>> np.allclose(piecewise([X * Y < 0, ], [lambda x, y: -x * y,
    ...                                       lambda x, y: x * y], xi=(X, Y)),
    ...        [[ 6.25,  3.75,  1.25,  1.25,  3.75,  6.25],
    ...         [ 3.75,  2.25,  0.75,  0.75,  2.25,  3.75],
    ...         [ 1.25,  0.75,  0.25,  0.25,  0.75,  1.25],
    ...         [ 1.25,  0.75,  0.25,  0.25,  0.75,  1.25],
    ...         [ 3.75,  2.25,  0.75,  0.75,  2.25,  3.75],
    ...         [ 6.25,  3.75,  1.25,  1.25,  3.75,  6.25]])
    True
    """
    def otherwise_condition(condlist):
        return ~np.logical_or.reduce(condlist, axis=0)

    def check_shapes(condlist, funclist):
        num_cond, num_fun = len(condlist), len(funclist)
        _assert(num_cond in [num_fun - 1, num_fun],
                "function list and condition list must be the same length")

    check_shapes(condlist, funclist)

    condlist = np.broadcast_arrays(*condlist)
    if len(condlist) == len(funclist) - 1:
        condlist.append(otherwise_condition(condlist))

    if xi is None:
        arrays = ()
        dtype = np.result_type(*funclist)
        shape = condlist[0].shape
    else:
        if not isinstance(xi, tuple):
            xi = (xi,)
        arrays = np.broadcast_arrays(*xi)
        dtype = np.result_type(*arrays)
        shape = arrays[0].shape

    out = np.full(shape, fillvalue, dtype)
    for cond, func in zip(condlist, funclist):
        if cond.any():
            if isinstance(func, collections.Callable):
                temp = tuple(np.extract(cond, arr) for arr in arrays) + args
                np.place(out, cond, func(*temp, **kw))
            else:  # func is a scalar value or a array
                np.putmask(out, cond, func)
    return out


def lazywhere(cond, arrays, f, fillvalue=None, f2=None):
    """
    np.where(cond, x, fillvalue) always evaluates x even where cond is False.
    This one only evaluates f(arr1[cond], arr2[cond], ...).
    For example,
    >>> a, b = np.array([1, 2, 3, 4]), np.array([5, 6, 7, 8])
    >>> def f(a, b):
    ...     return a*b
    >>> r = lazywhere(a > 2, (a, b), f, np.nan)
    >>> np.allclose(r[2:], [21.,  32.]); np.all(np.isnan(r[:2]))
    True
    True
    >>> def f2(a, b):
    ...    return (a*b)**2
    >>> np.allclose(lazywhere(a > 2, (a, b), f, f2=f2),
    ...            [  25.,  144.,   21.,   32.])
    True

    Notice it assumes that all `arrays` are of the same shape, or can be
    broadcasted together.

    """
    if fillvalue is None:
        _assert(f2 is not None, "One of (fillvalue, f2) must be given.")
        fillvalue = np.nan
    else:
        _assert(f2 is None, "Only one of (fillvalue, f2) can be given.")

    arrays = np.broadcast_arrays(*arrays)
    temp = tuple(np.extract(cond, arr) for arr in arrays)
    out = np.full(np.shape(arrays[0]), fill_value=fillvalue)
    np.place(out, cond, f(*temp))
    if f2 is not None:
        temp = tuple(np.extract(~cond, arr) for arr in arrays)
        np.place(out, ~cond, f2(*temp))

    return out


def lazyselect(condlist, choicelist, arrays, default=0):
    """
    Mimic `np.select(condlist, choicelist)`.

    Notice it assumes that all `arrays` are of the same shape, or can be
    broadcasted together.

    All functions in `choicelist` must accept array arguments in the order
    given in `arrays` and must return an array of the same shape as broadcasted
    `arrays`.

    Examples
    --------
    >>> x = np.arange(6)
    >>> np.allclose(np.select([x <3, x > 3], [x**2, x**3], default=0),
    ...             [  0,   1,   4,   0,  64, 125])
    True
    >>> np.allclose(lazyselect([x < 3, x > 3], [lambda x: x**2, lambda x: x**3], (x,)),
    ...             [   0.,    1.,    4.,    0.,   64.,  125.])
    True
    >>> a = -np.ones_like(x)
    >>> np.allclose(lazyselect([x < 3, x > 3],
    ...                        [lambda x, a: x**2, lambda x, a: a * x**3],
    ...                        (x, a)),
    ...             [   0.,    1.,    4.,    0.,  -64., -125.])
    True
    """
    arrays = np.broadcast_arrays(*arrays)
    tcode = np.mintypecode([a.dtype.char for a in arrays])
    out = valarray(np.shape(arrays[0]), value=default, typecode=tcode)
    for index, cond in enumerate(condlist):
        func = choicelist[index]
        if np.all(cond is False):
            continue
        cond, _ = np.broadcast_arrays(cond, arrays[0])
        temp = tuple(np.extract(cond, arr) for arr in arrays)
        np.place(out, cond, func(*temp))
    return out


def rotation_matrix(heading, pitch, roll):
    '''
    Parameters
    ----------
    heading, pitch, roll : real scalars
        defining heading, pitch and roll in degrees.

    Examples
    --------
    >>> import numpy as np
    >>> np.allclose(rotation_matrix(heading=0, pitch=0, roll=0),
    ...       [[ 1.,  0.,  0.],
    ...        [ 0.,  1.,  0.],
    ...        [ 0.,  0.,  1.]])
    True
    >>> np.allclose(rotation_matrix(heading=180, pitch=0, roll=0),
    ...      [[ -1.,   0.,   0.],
    ...       [  0.,  -1.,   0.],
    ...       [  0.,   0.,   1.]])
    True
    >>> np.allclose(rotation_matrix(heading=0, pitch=180, roll=0),
    ...      [[ -1.,  0.,   0.],
    ...       [  0.,  1.,   0.],
    ...       [  0.,  0.,  -1.]])
    True
    >>> np.allclose(rotation_matrix(heading=0, pitch=0, roll=180),
    ...      [[  1.,  0.,   0.],
    ...       [ 0.,  -1.,   0.],
    ...       [ 0.,   0.,  -1.]])
    True
    '''
    data = np.diag(np.ones(3))  # No transform if H=P=R=0
    if heading != 0 or pitch != 0 or roll != 0:
        deg2rad = np.pi / 180
        rheading = heading * deg2rad
        rpitch = pitch * deg2rad
        rroll = roll * deg2rad  # Convert to radians

        data.put(0, cos(rheading) * cos(rpitch))
        data.put(1, cos(rheading) * sin(rpitch) * sin(rroll) - sin(rheading) * cos(rroll))
        data.put(2, cos(rheading) * sin(rpitch) * cos(rroll) + sin(rheading) * sin(rroll))
        data.put(3, sin(rheading) * cos(rpitch))
        data.put(4, sin(rheading) * sin(rpitch) * sin(rroll) + cos(rheading) * cos(rroll))
        data.put(5, sin(rheading) * sin(rpitch) * cos(rroll) - cos(rheading) * sin(rroll))
        data.put(6, -sin(rpitch))
        data.put(7, cos(rpitch) * sin(rroll))
        data.put(8, cos(rpitch) * cos(rroll))
    return data


def rotate(x, y, z, heading=0, pitch=0, roll=0):
    """
    Example
    -------
    >>> import numpy as np
    >>> x, y, z = 1, 1, 1
    >>> np.allclose(rotate(x, y, z, heading=0, pitch=0, roll=0),
    ...    (1.0, 1.0, 1.0))
    True
    >>> np.allclose(rotate(x, y, z, heading=90, pitch=0, roll=0),
    ...            (-1.0, 1.0, 1.0))
    True
    >>> np.allclose(rotate(x, y, z, heading=0, pitch=90, roll=0),
    ...            (1.0, 1.0, -1.0))
    True
    >>> np.allclose(rotate(x, y, z, heading=0, pitch=0, roll=90),
    ...            (1.0, -1.0, 1.0))
    True
    """
    rot_param = rotation_matrix(heading, pitch, roll).ravel()
    x_out = x * rot_param[0] + y * rot_param[1] + z * rot_param[2]
    y_out = x * rot_param[3] + y * rot_param[4] + z * rot_param[5]
    z_out = x * rot_param[6] + y * rot_param[7] + z * rot_param[8]
    return x_out, y_out, z_out


def rotate_2d(x, y, angle_deg):
    '''
    Rotate points in the xy cartesian plane counter clockwise

    Examples
    --------
    >>> np.allclose(rotate_2d(x=1, y=0, angle_deg=0), (1.0, 0.0))
    True
    >>> np.allclose(rotate_2d(x=1, y=0, angle_deg=90), (0, 1.0))
    True
    >>> np.allclose(rotate_2d(x=1, y=0, angle_deg=180), (-1.0, 0))
    True
    >>> np.allclose(rotate_2d(x=1, y=0, angle_deg=360), (1.0, 0))
    True
    '''
    angle_rad = angle_deg * pi / 180
    cos_a = cos(angle_rad)
    sin_a = sin(angle_rad)
    return cos_a * x - sin_a * y, sin_a * x + cos_a * y


def now(show_seconds=True):
    '''
    Return current date and time as a string
    '''
    if show_seconds:
        return strftime("%a, %d %b %Y %H:%M:%S", gmtime())
    return strftime("%a, %d %b %Y %H:%M", gmtime())


def _assert(cond, txt=''):
    if not cond:
        raise ValueError(txt)


def spaceline(start_point, stop_point, num=10):
    '''Return `num` evenly spaced points between the start and stop points.

    Parameters
    ----------
    start_point : vector, size=3
        The starting point of the sequence.
    stop_point : vector, size=3
        The end point of the sequence.
    num : int, optional
        Number of samples to generate. Default is 10.

    Returns
    -------
    space_points : ndarray of shape n x 3
        There are `num` equally spaced points in the closed interval
        ``[start, stop]``.

    See Also
    --------
    linspace : similar to spaceline, but in 1D.
    arange : Similiar to `linspace`, but uses a step size (instead of the
             number of samples).
    logspace : Samples uniformly distributed in log space.

    Example
    -------
    >>> import wafo.misc as pm
    >>> np.allclose(pm.spaceline((2,0,0), (3,0,0), num=5),
    ...      [[ 2.  ,  0.  ,  0.  ],
    ...       [ 2.25,  0.  ,  0.  ],
    ...       [ 2.5 ,  0.  ,  0.  ],
    ...       [ 2.75,  0.  ,  0.  ],
    ...       [ 3.  ,  0.  ,  0.  ]])
    True
    >>> np.allclose(pm.spaceline((2,0,0), (0,0,3), num=5),
    ...      [[ 2.  ,  0.  ,  0.  ],
    ...       [ 1.5 ,  0.  ,  0.75],
    ...       [ 1.  ,  0.  ,  1.5 ],
    ...       [ 0.5 ,  0.  ,  2.25],
    ...       [ 0.  ,  0.  ,  3.  ]])
    True
    '''
    num = int(num)
    start, stop = np.atleast_1d(start_point, stop_point)
    delta = (stop - start) / float(num - 1)
    return np.array([start + n * delta for n in range(num)])


def narg_smallest(arr, n=1):
    ''' Return the n smallest indices to the arr

    Examples
    --------
    >>> import numpy as np
    >>> t = np.array([37, 11, 4, 23, 4, 6, 3, 2, 7, 4, 0])
    >>> ix = narg_smallest(t, 3)
    >>> np.allclose(ix,
    ...             [10,  7,  6])
    True
    >>> np.allclose(t[ix], [0, 2, 3])
    True
    '''
    return np.array(arr).argsort()[:n]


def args_flat(*args):
    '''
    Return x,y,z positions as a N x 3 ndarray

    Parameters
    ----------
    pos : array-like, shape N x 3
        [x,y,z] positions
    or

    x,y,z : array-like
        [x,y,z] positions

    Returns
    ------
    pos : ndarray, shape N x 3
        [x,y,z] positions
    common_shape : None or tuple
        common shape of x, y and z variables if given as triple input.

    Examples
    --------
    >>> x = [1,2,3]
    >>> pos, c_shape =args_flat(x,2,3)
    >>> pos
    array([[1, 2, 3],
           [2, 2, 3],
           [3, 2, 3]])
    >>> c_shape
    (3,)
    >>> pos1, c_shape1 = args_flat([1,2,3])
    >>> pos1
    array([[1, 2, 3]])
    >>> c_shape1 is None
    True
    >>> pos1, c_shape1 = args_flat(1,2,3)
    >>> pos1
    array([[1, 2, 3]])
    >>> c_shape1
    ()
    >>> pos1, c_shape1 = args_flat([1],2,3)
    >>> pos1
    array([[1, 2, 3]])
    >>> c_shape1
    (1,)

    '''
    nargin = len(args)
    _assert(nargin in [1, 3], 'Number of arguments must be 1 or 3!')
    if nargin == 1:  # pos
        pos = np.atleast_2d(args[0])
        _assert((pos.shape[1] == 3) and (pos.ndim == 2),
                'POS array must be of shape N x 3!')
        return pos, None

    x, y, z = np.broadcast_arrays(*args[:3])
    c_shape = x.shape
    return np.vstack((x.ravel(), y.ravel(), z.ravel())).T, c_shape


def index2sub(shape, index, order='C'):
    '''
    Returns Multiple subscripts from linear index.

    Parameters
    ----------
    shape : array-like
        shape of array
    index :
        linear index into array
    order : {'C','F'}, optional
        The order of the linear index.
        'C' means C (row-major) order.
        'F' means Fortran (column-major) order.
        By default, 'C' order is used.

    This function is used to determine the equivalent subscript values
    corresponding to a given single index into an array.

    Example
    -------
    >>> shape = (3,3,4)
    >>> a = np.arange(np.prod(shape)).reshape(shape)
    >>> order = 'C'
    >>> a[1, 2, 3]
    23
    >>> i = sub2index(shape, 1, 2, 3, order=order)
    >>> a.ravel(order)[i]
    23
    >>> index2sub(shape, i, order=order)
    (1, 2, 3)

    See also
    --------
    sub2index
    '''
    return np.unravel_index(index, shape, order=order)


def sub2index(shape, *subscripts, **kwds):
    '''
    Returns linear index from multiple subscripts.

    Parameters
    ----------
    shape : array-like
        shape of array
    *subscripts :
        subscripts into array
    order : {'C','F'}, optional
        The order of the linear index.
        'C' means C (row-major) order.
        'F' means Fortran (column-major) order.
        By default, 'C' order is used.

    This function is used to determine the equivalent single index
    corresponding to a given set of subscript values into an array.

    Example
    -------
    >>> shape = (3,3,4)
    >>> a = np.arange(np.prod(shape)).reshape(shape)
    >>> order = 'C'
    >>> i = sub2index(shape, 1, 2, 3, order=order)
    >>> a[1, 2, 3]
    23
    >>> a.ravel(order)[i]
    23
    >>> index2sub(shape, i, order=order)
    (1, 2, 3)

    See also
    --------
    index2sub
    '''
    return np.ravel_multi_index(subscripts, shape, **kwds)


def is_numlike(obj):
    """return true if *obj* looks like a number

    Examples
    --------
    >>> is_numlike(1)
    True
    >>> is_numlike('1')
    False
    >>> is_numlike([1])
    False
    """
    try:
        obj + 1
    except TypeError:
        return False
    return True


class JITImport(object):

    '''
    Just In Time Import of module

    Example
    -------
    >>> np = JITImport('numpy')
    >>> np.exp(0)==1.0
    True
    '''

    def __init__(self, module_name):
        self._module_name = module_name
        self._module = None

    def __getattr__(self, attr):
        try:
            return getattr(self._module, attr)
        except AttributeError as exc:
            if self._module is None:
                self._module = __import__(self._module_name, None, None, ['*'])
                # assert(isinstance(self._module, types.ModuleType), 'module')
                return getattr(self._module, attr)
            raise exc


class DotDict(dict):

    ''' Implement dot access to dict values

      Example
      -------
       >>> d = DotDict(test1=1,test2=3)
       >>> d.test1
       1
    '''
    __getattr__ = dict.__getitem__


class Bunch(object):

    ''' Implement keyword argument initialization of class

    Example
    -------
    >>> d = Bunch(test1=1,test2=3)
    >>> (d.test1, d.test2)
    (1, 3)
    >>> sorted(d.keys()) ==  ['test1', 'test2']
    True
    >>> d.update(test1=5)
    >>> (d.test1, d.test2)
    (5, 3)
    '''

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def keys(self):
        return list(self.__dict__)

    def update(self, ** kwargs):
        self.__dict__.update(kwargs)


def printf(format_, *args):  # @ReservedAssignment
    sys.stdout.write(format_ % args)


def sub_dict_select(somedict, somekeys):
    '''
    Extracting a Subset from Dictionary

    Example
    --------
    # Update options dict from keyword arguments if
    # the keyword exists in options
    >>> opt = dict(arg1=2, arg2=3)
    >>> kwds = dict(arg2=100,arg3=1000)
    >>> sub_dict = sub_dict_select(kwds, opt)
    >>> opt.update(sub_dict)
    >>> opt == {'arg1': 2, 'arg2': 100}
    True

    See also
    --------
    dict_intersection
    '''
    # slower: validKeys = set(somedict).intersection(somekeys)
    return type(somedict)((k, somedict[k]) for k in somekeys if k in somedict)


def parse_kwargs(options, **kwargs):
    '''
    Update options dict from keyword arguments if the keyword exists in options

    Example
    >>> opt = dict(arg1=2, arg2=3)
    >>> opt = parse_kwargs(opt,arg2=100)
    >>> opt == {'arg1': 2, 'arg2': 100}
    True
    >>> opt2 = dict(arg2=101)
    >>> opt = parse_kwargs(opt,**opt2)

    See also sub_dict_select
    '''

    newopts = sub_dict_select(kwargs, options)
    if len(newopts) > 0:
        options.update(newopts)
    return options


def moving_average(x, L, axis=0):
    """
    Return moving average from data using a window of size 2*L+1.
    If 2*L+1 > len(x) then the mean is returned

    Parameters
    ----------
    x : vector or matrix of column vectors
        of data
    L : scalar, integer
        defines the size of the moving average window
    axis: scalar integer
        axis along which the moving average is computed. Default axis=0.

    Returns
    -------
    y : ndarray
        moving average

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> import numpy as np
    >>> exp = np.exp; cos = np.cos; randn = np.random.randn

    >>> x = np.linspace(0,1,200)
    >>> y = exp(x)+cos(5*2*pi*x)+1e-1*randn(x.size)
    >>> y0 = moving_average(y, 20)
    >>> np.allclose(y0[:4], [ 1.1189971,  1.1189971,  1.1189971,  1.1189971], atol=1e-1)
    True

    >>> x2 = np.linspace(1, 5, 5)
    >>> np.allclose(moving_average(x2, L=1), [2.,  2.,  3.,  4.,  4.])
    True
    >>> np.allclose(moving_average(x2, L=10), [3.,  3.,  3.,  3.,  3.])
    True
    >>> x3 = np.vstack((x2, x2+5))
    >>> np.allclose(moving_average(x3, L=1, axis=1), [[2.,  2.,  3.,  4.,  4.],
    ...                                               [7.,  7.,  8.,  9.,  9.]])
    True
    >>> np.allclose(moving_average(x3, L=10, axis=1), [[3.,  3.,  3.,  3.,  3.],
    ...                                                [8.,  8.,  8.,  8.,  8.]])
    True

    h = plt.plot(x, y, x, y0, 'r', x, exp(x), 'k', x, tr, 'm')
    plt.close('all')

    See also
    --------
    Reconstruct
    """
    _assert(0 < L, 'L must be positive')
    _assert(L == np.round(L), 'L must be an integer')

    x1 = np.atleast_1d(x)
    axes = np.arange(x.ndim)

    axes[0] = axis
    axes[axis] = 0

    x1 = np.transpose(x1, axes)
    y = np.empty_like(x1)

    n = x1.shape[0]
    if n < 2 * L + 1:  # only able to remove the mean
        y[:] = x1.mean(axis=0)
        return np.transpose(y, axes)

    mn = x1[0:2 * L + 1].mean(axis=0)
    y[0:L + 1] = mn

    ix = np.r_[L + 1:(n - L)]
    y[ix] = ((x1[ix + L] - x1[ix - L]) / (2 * L)).cumsum(axis=0) + mn
    y[n - L::] = y[n - L - 1]

    return np.transpose(y, axes)


def detrendma(x, L, axis=0):
    """
    Removes a trend from data using a moving average
           of size 2*L+1.  If 2*L+1 > len(x) then the mean is removed

    Parameters
    ----------
    x : vector or matrix of column vectors
        of data
    L : scalar, integer
        defines the size of the moving average window
    axis: scalar integer
        axis along which the moving average is computed. Default axis=0.

    Returns
    -------
    y : ndarray
        detrended data

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> import numpy as np
    >>> import wafo.misc as wm
    >>> exp = np.exp; cos = np.cos; randn = np.random.randn

    >>> x = np.linspace(0,1,200)
    >>> noise = 0.1*randn(x.size)
    >>> noise = 0.1*np.sin(100*x)
    >>> y = exp(x)+cos(5*2*pi*x) + noise
    >>> y0 = wm.detrendma(y, 20)
    >>> tr = y-y0
    >>> np.allclose(tr[:5],
    ...    [ 1.14134814,  1.14134814,  1.14134814,  1.14134814,  1.14134814])
    True
    >>> y1 = wm.detrendma(y, 200)
    >>> np.allclose((y-y1), 1.7239972279640454)
    True
    >>> x2 = np.linspace(1, 5, 5)
    >>> np.allclose(wm.detrendma(x2, L=1), [-1, 0, 0, 0, 1])
    True

    h = plt.plot(x, y, x, y0, 'r', x, exp(x), 'k', x, tr, 'm')
    plt.close('all')

    See also
    --------
    Reconstruct, moving_average
    """
    x1 = np.atleast_1d(x)
    trend = moving_average(x1, L, axis)
    return x1 - trend


def ecross(t, f, ind, v=0):
    '''
    Extracts exact level v crossings

    ECROSS interpolates t and f linearly to find the exact level v
    crossings, i.e., the points where f(t0) = v

    Parameters
    ----------
    t,f : vectors
        of arguments and functions values, respectively.
    ind : ndarray of integers
        indices to level v crossings as found by findcross.
    v : scalar or vector (of size(ind))
        defining the level(s) to cross.

    Returns
    -------
    t0 : vector
        of  exact level v crossings.

    Example
    -------
    >>> from matplotlib import pyplot as plt
    >>> import wafo.misc as wm
    >>> ones = np.ones
    >>> t = np.linspace(0,7*np.pi,250)
    >>> x = np.sin(t)
    >>> ind = wm.findcross(x,0.75)
    >>> np.allclose(ind, [  9,  25,  80,  97, 151, 168, 223, 239])
    True
    >>> t0 = wm.ecross(t,x,ind,0.75)
    >>> np.allclose(t0, [0.84910514, 2.2933879 , 7.13205663, 8.57630119,
    ...        13.41484739, 14.85909194, 19.69776067, 21.14204343])
    True

    a = plt.plot(t, x, '.', t[ind], x[ind], 'r.', t, ones(t.shape)*0.75,
                  t0, ones(t0.shape)*0.75, 'g.')
    plt.close('all')

    See also
    --------
    findcross
    '''
    # Tested on: Python 2.5
    # revised pab Feb2004
    # By pab 18.06.2001
    return (t[ind] + (v - f[ind]) * (t[ind + 1] - t[ind]) /
            (f[ind + 1] - f[ind]))


def _findcross(x, method='numba'):
    '''Return indices to zero up and downcrossings of a vector
    '''
    if clib is not None and method == 'clib':
        ind, m = clib.findcross(x, 0.0)  # pylint: disable=no-member
        return ind[:int(m)]
    return numba_misc.findcross(x)


def findcross(x, v=0.0, kind=None, method='clib'):
    '''
    Return indices to level v up and/or downcrossings of a vector

    Parameters
    ----------
    x : array_like
        vector with sampled values.
    v : scalar, real
        level v.
    kind : string
        defines type of wave or crossing returned. Possible options are
        'dw' : downcrossing wave
        'uw' : upcrossing wave
        'cw' : crest wave
        'tw' : trough wave
        'd'  : downcrossings only
        'u'  : upcrossings only
        None : All crossings will be returned

    Returns
    -------
    ind : array-like
        indices to the crossings in the original sequence x.

    Example
    -------
    >>> from matplotlib import pyplot as plt
    >>> import wafo.misc as wm
    >>> ones = np.ones
    >>> np.allclose(findcross([0, 1, -1, 1], 0), [0, 1, 2])
    True
    >>> v = 0.75
    >>> t = np.linspace(0,7*np.pi,250)
    >>> x = np.sin(t)
    >>> ind = wm.findcross(x,v) # all crossings
    >>> np.allclose(ind, [  9,  25,  80,  97, 151, 168, 223, 239])
    True

    >>> ind2 = wm.findcross(x,v,'u')
    >>> np.allclose(ind2, [  9,  80, 151, 223])
    True
    >>> ind3 = wm.findcross(x,v,'d')
    >>> np.allclose(ind3, [  25,  97, 168, 239])
    True
    >>> ind4 = wm.findcross(x,v,'d', method='2')
    >>> np.allclose(ind4, [  25,  97, 168, 239])
    True

    t0 = plt.plot(t,x,'.',t[ind],x[ind],'r.', t, ones(t.shape)*v)
    t0 = plt.plot(t[ind2],x[ind2],'o')
    plt.close('all')

    See also
    --------
    crossdef
    wavedef
    '''
    xn = np.int8(sign(atleast_1d(x).ravel() - v))  # @UndefinedVariable
    ind = _findcross(xn, method)
    if ind.size == 0:
        warnings.warn('No level v = %0.5g crossings found in x' % v)
        return ind

    if kind not in ('du', 'all', None):
        if kind == 'd':  # downcrossings only
            t_0 = int(xn[ind[0] + 1] > 0)
            ind = ind[t_0::2]
        elif kind == 'u':  # upcrossings  only
            t_0 = int(xn[ind[0] + 1] < 0)
            ind = ind[t_0::2]
        elif kind in ('dw', 'uw', 'tw', 'cw'):
            # make sure that the first is a level v down-crossing
            #   if kind=='dw' or kind=='tw'
            # or that the first is a level v up-crossing
            #    if kind=='uw' or kind=='cw'
            first_is_down_crossing = int(xn[ind[0]] > xn[ind[0] + 1])
            if xor(first_is_down_crossing, kind in ('dw', 'tw')):
                ind = ind[1::]

            n_c = ind.size  # number of level v crossings
            # make sure the number of troughs and crests are according to the
            # wavedef, i.e., make sure length(ind) is odd if dw or uw
            # and even if tw or cw
            is_odd = mod(n_c, 2)
            if xor(is_odd, kind in ('dw', 'uw')):
                ind = ind[:-1]
        else:
            raise ValueError('Unknown wave/crossing definition!'
                             ' ({})'.format(kind))
    return ind


def findextrema(x):
    '''
    Return indices to minima and maxima of a vector

    Parameters
    ----------
    x : vector with sampled values.

    Returns
    -------
    ind : indices to minima and maxima in the original sequence x.

    Examples
    --------
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> import wafo.misc as wm
    >>> t = np.linspace(0,7*np.pi,250)
    >>> x = np.sin(t)
    >>> ind = wm.findextrema(x)
    >>> np.allclose(ind, [ 18,  53,  89, 125, 160, 196, 231])
    True

    a = plt.plot(t,x,'.',t[ind],x[ind],'r.')
    plt.close('all')

    See also
    --------
    findcross
    crossdef
    '''
    dx = diff(np.atleast_1d(x).ravel())
    return findcross(dx, 0.0) + 1


def findpeaks(data, n=2, min_h=None, min_p=0.0):
    '''
    Find peaks of vector or matrix possibly rainflow filtered

    Parameters
    ----------
    data : matrix or vector
    n :
         The n highest peaks are found (if exist). (default 2)
    min_h :
        The threshold in the rainflowfilter (default 0.05*range(S(:))).
        A zero value will return all the peaks of S.
    min_p : 0..1
        Only the peaks that are higher than min_p*max(max(S))
        min_p*(the largest peak in S) are returned (default  0).

    Returns
    -------
    ix =
        linear index to peaks of S

    Example:

    Find highest 8 peaks that are not
    less that 0.3*"global max" and have
    rainflow amplitude larger than 5.
    >>> import numpy as np
    >>> import wafo.misc as wm
    >>> x = np.arange(0,10,0.01)
    >>> data = x**2+10*np.sin(3*x)+0.5*np.sin(50*x)
    >>> np.allclose(wm.findpeaks(data, n=8, min_h=5, min_p=0.3),
    ...            [908, 694, 481])
    True

    See also
    --------
    findtp
    '''
    data1 = np.atleast_1d(data)
    dmax = data1.max()
    if min_h is None:
        dmin = data1.min()
        min_h = 0.05 * (dmax - dmin)
    ndim = data1.ndim
    data1 = np.atleast_2d(data1)
    nrows, mcols = data1.shape

    # Finding turningpoints of the spectrum
    # Returning only those with rainflowcycle heights greater than h_min
    ind_p = []  # indices to peaks
    ind = []
    for iy in range(nrows):  # find all peaks
        tp = findtp(data1[iy], min_h)
        if len(tp):
            ind = tp[1::2]  # extract indices to maxima only
        else:  # did not find any , try maximum
            ind = np.atleast_1d(data1[iy].argmax())

        if ndim > 1:
            if iy == 0:
                ind2 = np.flatnonzero(data1[iy, ind] > data1[iy + 1, ind])
            elif iy == nrows - 1:
                ind2 = np.flatnonzero(data1[iy, ind] > data1[iy - 1, ind])
            else:
                ind2 = np.flatnonzero((data1[iy, ind] > data1[iy - 1, ind]) &
                                      (data1[iy, ind] > data1[iy + 1, ind]))

            if len(ind2):
                ind_p.append((ind[ind2] + iy * mcols))

    if ndim > 1:
        ind = np.hstack(ind_p) if len(ind_p) else []
    if len(ind) == 0:
        return []

    peaks = data1.take(ind)
    ind2 = peaks.argsort()[::-1]

    # keeping only the Np most significant peaks.
    nmax = min(n, len(ind))
    ind = ind[ind2[:nmax]]
    if (min_p > 0):
        # Keeping only peaks larger than min_p percent relative to the maximum
        # peak
        ind = ind[(data1.take(ind) > min_p * dmax)]

    return ind


def findrfc_astm(tp):
    """
    Return rainflow counted cycles

    Nieslony's Matlab implementation of the ASTM standard practice for rainflow
    counting ported to a Python C module.

    Parameters
    ----------
    tp : array-like
        vector of turningpoints (NB! Only values, not sampled times)

    Returns
    -------
    sig_rfc : array-like
        array of shape (n,3) with:
        sig_rfc[:,0] Cycles amplitude
        sig_rfc[:,1] Cycles mean value
        sig_rfc[:,2] Cycle type, half (=0.5) or full (=1.0)
    """
    return numba_misc.findrfc_astm(tp)
#     y1 = atleast_1d(tp).ravel()
#     sig_rfc, cnr = clib.findrfc3_astm(y1)
#     # the sig_rfc was constructed too big in rainflow.rf3, so
#     # reduce the sig_rfc array as done originally by a matlab mex c function
#     n = len(sig_rfc)
#     # sig_rfc = sig_rfc.__getslice__(0, n - cnr[0])
#     # sig_rfc holds the actual rainflow counted cycles, not the indices
#     return sig_rfc[:n - cnr[0]]


def findrfc(tp, h=0.0, method='clib'):
    '''
    Return indices to rainflow cycles of a sequence of TP.

    Parameters
    -----------
    tp : array-like
        vector of turningpoints (NB! Only values, not sampled times)
    h : real scalar
        rainflow threshold. If h>0, then all rainflow cycles with height
        smaller than h are removed.
    method : string, optional
        'clib' 'None'
        Specify 'clib' for calling the c_functions, otherwise fallback to
        the Python implementation.

    Returns
    -------
    ind : ndarray of int
        indices to the rainflow cycles of the original sequence TP.

    Example:
    --------
    >>> import matplotlib.pyplot as plt
    >>> import wafo.misc as wm
    >>> t = np.linspace(0,7*np.pi,250)
    >>> x = np.sin(t)+0.1*np.sin(50*t)
    >>> ind = wm.findextrema(x)
    >>> ti, tp = t[ind], x[ind]

    >>> ind1 = wm.findrfc(tp, 0.3)
    >>> np.allclose(ind1, [  0,   9,  32,  53,  74,  95, 116, 137])
    True
    >>> ind2 = wm.findrfc(tp, 0.3, method=0)
    >>> np.allclose(ind2, [  0,   9,  32,  53,  74,  95, 116, 137, 146])
    True
    >>> ind3 = wm.findrfc(tp, 0.3, method=1)
    >>> np.allclose(ind3, [  0,   9,  32,  53,  74,  95, 116, 137, 146])
    True
    >>> ind3 = wm.findrfc(tp, 0.3, method=2)
    >>> np.allclose(ind3, [  0,   9,  32,  53,  74,  95, 116, 137])
    True


    a = plt.plot(t,x,'.',ti,tp,'r.')
    a = plt.plot(ti[ind1],tp[ind1])
    plt.close('all')

    See also
    --------
    rfcfilter,
    findtp.
    '''
    y = atleast_1d(tp).ravel()

    t_start = int(y[0] > y[1])  # first is a max, ignore it
    y = y[t_start::]
    n = len(y)
    NC = np.floor(n // 2) - 1

    if (NC < 1):
        return zeros(0, dtype=np.int)  # No RFC cycles*/

    if (y[0] > y[1] and y[1] > y[2] or
            y[0] < y[1] and y[1] < y[2]):
        warnings.warn('This is not a sequence of turningpoints, exit')
        return zeros(0, dtype=np.int)

    if clib is not None and method == 'clib':
        ind, ix = clib.findrfc(y, h)  # pylint: disable=no-member
        ix = int(ix)
    else:
        if isinstance(method, str):
            method = 2
        ind = numba_misc.findrfc(y, h, method)
        ix = len(ind)

    return np.sort(ind[:ix]) + t_start


def rfcfilter(x, h, method=0):
    """
    Rainflow filter a signal.

    Parameters
    -----------
    x : vector
        Signal.   [nx1]
    h : real, scalar
        Threshold for rainflow filter.
    method : scalar, integer
        0 : removes cycles with range < h. (default)
        1 : removes cycles with range <= h.

    Returns
    --------
    y   = Rainflow filtered signal.

    Examples:
    ---------
    # 1. Filtered signal y is the turning points of x.
    >>> import wafo.data as data
    >>> import wafo.misc as wm
    >>> x = data.sea()
    >>> y = wm.rfcfilter(x[:,1], h=0, method=1)
    >>> np.allclose(y[0:5], [-1.2004945 , 0.83950546, -0.09049454, -0.02049454, -0.09049454])
    True
    >>> np.allclose(y.shape, (2172,))
    True

    # 2. This removes all rainflow cycles with range less than 0.5.
    >>> y1 = wm.rfcfilter(x[:,1], h=0.5)
    >>> np.allclose(y1.shape, (863,))
    True
    >>> np.allclose(y1[0:5], [-1.2004945 , 0.83950546, -0.43049454, 0.34950546, -0.51049454])
    True
    >>> ind = wm.findtp(x[:,1], h=0.5)
    >>> y2 = x[ind,1]
    >>> np.allclose(y2[0:5], [-1.2004945 ,  0.83950546, -0.43049454,  0.34950546, -0.51049454])
    True
    >>> np.allclose(y2[-5::], [ 0.83950546, -0.64049454,  0.65950546, -1.0004945 ,  0.91950546])
    True

    See also
    --------
    findrfc
    """
    y = atleast_1d(x).ravel()
    ix = numba_misc.findrfc(y, h, method)
    return y[ix]


def findtp(x, h=0.0, kind=None):
    '''
    Return indices to turning points (tp) of data, optionally rainflowfiltered.

    Parameters
    ----------
    x : vector
        signal
    h : real, scalar
        rainflow threshold
         if  h<0, then ind = range(len(x))
         if  h=0, then  tp  is a sequence of turning points (default)
         if  h>0, then all rainflow cycles with height smaller than
                  h  are removed.
    kind : string
        defines the type of wave or indicate the ASTM rainflow counting method.
        Possible options are 'astm' 'mw' 'Mw' or 'none'.
        If None all rainflow filtered min and max
        will be returned, otherwise only the rainflow filtered
        min and max, which define a wave according to the
        wave definition, will be returned.

    Returns
    -------
    ind : arraylike
        indices to the turning points in the original sequence.

    Example:
    --------
    >>> import matplotlib.pyplot as plt
    >>> import wafo.misc as wm
    >>> t = np.linspace(0,30,500).reshape((-1,1))
    >>> x = np.hstack((t, np.cos(t) + 0.3 * np.sin(5*t)))
    >>> x1 = x[0:100,:]
    >>> itp = wm.findtp(x1[:,1],0,'Mw')
    >>> itph = wm.findtp(x1[:,1],0.3,'Mw')
    >>> tp = x1[itp,:]
    >>> tph = x1[itph,:]
    >>> np.allclose(itp, [ 5, 18, 24, 38, 46, 57, 70, 76, 91, 98, 99])
    True
    >>> np.allclose(itph, 91)
    True

    a = plt.plot(x1[:,0],x1[:,1],
                 tp[:,0],tp[:,1],'ro',
                 tph[:,0],tph[:,1],'k.')
    plt.close('all')

    See also
    ---------
    findtc
    findcross
    findextrema
    findrfc
    '''
    n = len(x)
    if h < 0.0:
        return arange(n)

    ind = findextrema(x)

    if ind.size < 2:
        return None

    # In order to get the exact up-crossing intensity from rfc by
    # mm2lc(tp2mm(rfc))  we have to add the indices to the last value
    # (and also the first if the sequence of turning points does not start
    # with a minimum).

    if kind == 'astm':
        # the Nieslony approach always put the first loading point as the first
        # turning point.
        # add the first turning point is the first of the signal
        if ind[0] != 0:
            ind = np.r_[0, ind, n - 1]
        else:  # only add the last point of the signal
            ind = np.r_[ind, n - 1]
    else:
        if x[ind[0]] > x[ind[1]]:  # adds indices to  first and last value
            ind = np.r_[0, ind, n - 1]
        else:  # adds index to the last value
            ind = np.r_[ind, n - 1]

    if h > 0.0:
        ind1 = findrfc(x[ind], h)
        ind = ind[ind1]

    if kind in ('mw', 'Mw'):
        # make sure that the first is a Max if wdef == 'Mw'
        # or make sure that the first is a min if wdef == 'mw'
        first_is_max = (x[ind[0]] > x[ind[1]])

        remove_first = xor(first_is_max, kind.startswith('Mw'))
        if remove_first:
            ind = ind[1::]

        # make sure the number of minima and Maxima are according to the
        # wavedef. i.e., make sure Nm=length(ind) is odd
        if (mod(ind.size, 2)) != 1:
            ind = ind[:-1]
    return ind


def findtc(x_in, v=None, kind=None):
    """
    Return indices to troughs and crests of data.

    Parameters
    ----------
    x : vector
        surface elevation.
    v : real scalar
        reference level (default  v = mean of x).

    kind : string
        defines the type of wave. Possible options are
        'dw', 'uw', 'tw', 'cw' or None.
        If None indices to all troughs and crests will be returned,
        otherwise only the paired ones will be returned
        according to the wavedefinition.

    Returns
    --------
    tc_ind : vector of ints
        indices to the trough and crest turningpoints of sequence x.
    v_ind : vector of ints
        indices to the level v crossings of the original
        sequence x. (d,u)

    Example:
    --------
    >>> import matplotlib.pyplot as plt
    >>> import wafo.misc as wm
    >>> t = np.linspace(0,30,500).reshape((-1,1))
    >>> x = np.hstack((t, np.cos(t)))
    >>> x1 = x[0:200,:]
    >>> itc, iv = wm.findtc(x1[:,1],0,'dw')
    >>> tc = x1[itc,:]
    >>> np.allclose(itc, [ 52, 105])
    True
    >>> itc, iv = wm.findtc(x1[:,1],0,'uw')
    >>> np.allclose(itc, [ 105, 157])
    True

    a = plt.plot(x1[:,0],x1[:,1],tc[:,0],tc[:,1],'ro')
    plt.close('all')

    See also
    --------
    findtp
    findcross,
    wavedef
    """

    x = atleast_1d(x_in)
    if v is None:
        v = x.mean()

    v_ind = findcross(x, v, kind)
    n_c = v_ind.size
    if n_c <= 2:
        warnings.warn('There are no waves!')
        return zeros(0, dtype=np.int), zeros(0, dtype=np.int)

    # determine the number of trough2crest (or crest2trough) cycles
    is_even = mod(n_c + 1, 2)
    n_tc = int((n_c - 1 - is_even) / 2)

    # allocate variables before the loop increases the speed
    ind = zeros(n_c - 1, dtype=np.int)

    first_is_down_crossing = (x[v_ind[0]] > x[v_ind[0] + 1])
    if first_is_down_crossing:
        f1, f2 = np.argmin, np.argmax
    else:
        f1, f2 = np.argmax, np.argmin

    for i in range(n_tc):
        # trough or crest
        j = 2 * i
        ind[j] = f1(x[v_ind[j] + 1:v_ind[j + 1] + 1])
        # crest or trough
        ind[j + 1] = f2(x[v_ind[j + 1] + 1:v_ind[j + 2] + 1])

    if (2 * n_tc + 1 < n_c) and (kind in (None, 'tw', 'cw')):
        # trough or crest
        ind[n_c - 2] = f1(x[v_ind[n_c - 2] + 1:v_ind[n_c - 1] + 1])

    return v_ind[:n_c - 1] + ind + 1, v_ind


def findoutliers(x, zcrit=0.0, dcrit=None, ddcrit=None, verbose=False):
    """
    Return indices to spurious points of data

    Parameters
    ----------
    x : vector
        of data values.
    zcrit : real scalar
        critical distance between consecutive points.
    dcrit : real scalar
        critical distance of Dx used for determination of spurious
        points.  (Default 1.5 standard deviation of x)
    ddcrit : real scalar
        critical distance of DDx used for determination of spurious
        points.  (Default 1.5 standard deviation of x)

    Returns
    -------
    inds : ndarray of integers
        indices to spurious points.
    indg : ndarray of integers
        indices to the rest of the points.

    Notes
    -----
    Consecutive points less than zcrit apart  are considered as spurious.
    The point immediately after and before are also removed. Jumps greater than
    dcrit in Dxn and greater than ddcrit in D^2xn are also considered as
    spurious.
    (All distances to be interpreted in the vertical direction.)
    Another good choice for dcrit and ddcrit are:

        dcrit = 5*dT  and ddcrit = 9.81/2*dT**2

    where dT is the timestep between points.

    Examples
    --------
    >>> import numpy as np
    >>> import wafo.misc as wm
    >>> t = np.linspace(0,30,500).reshape((-1,1))
    >>> xx = np.hstack((t, np.cos(t)))
    >>> dt = np.diff(xx[:2,0])
    >>> dcrit = 5*dt
    >>> ddcrit = 9.81/2*dt*dt
    >>> zcrit = 0
    >>> inds, indg = wm.findoutliers(xx[:,1], verbose=True)
    Found 0 missing points
    dcrit is set to 1.05693
    ddcrit is set to 1.05693
    Found 0 spurious positive jumps of Dx
    Found 0 spurious negative jumps of Dx
    Found 0 spurious positive jumps of D^2x
    Found 0 spurious negative jumps of D^2x
    Found 0 consecutive equal values
    Found the total of 0 spurious points


    #waveplot(xx,'-',xx(inds,:),1,1,1)

    See also
    --------
    waveplot, reconstruct
    """

    def _find_nans(xn):
        i_missing = np.flatnonzero(np.isnan(xn))
        if verbose:
            print('Found %d missing points' % i_missing.size)
        return i_missing

    def _find_spurious_jumps(dxn, dcrit, name='Dx'):
        i_p = np.flatnonzero(dxn > dcrit)
        if i_p.size > 0:
            i_p += 1  # the point after the jump
        if verbose:
            print('Found {0:d} spurious positive jumps of {1}'.format(i_p.size,
                                                                      name))

        i_n = np.flatnonzero(dxn < -dcrit)  # the point before the jump
        if verbose:
            print('Found {0:d} spurious negative jumps of {1}'.format(i_n.size,
                                                                      name))
        if i_n.size > 0:
            return hstack((i_p, i_n))
        return i_p

    def _find_consecutive_equal_values(dxn, zcrit):

        mask_small = (np.abs(dxn) <= zcrit)
        i_small = np.flatnonzero(mask_small)
        if verbose:
            if zcrit == 0.:
                print('Found %d consecutive equal values' % i_small.size)
            else:
                print('Found %d consecutive values less than %g apart.' %
                      (i_small.size, zcrit))
        if i_small.size > 0:
            i_small += 1
            # finding the beginning and end of consecutive equal values
            i_step = np.flatnonzero((diff(mask_small))) + 1
            # indices to consecutive equal points
            # removing the point before + all equal points + the point after

            return hstack((i_step - 1, i_small, i_step, i_step + 1))
        return i_small

    xn = asarray(x).flatten()

    _assert(2 < xn.size, 'The vector must have more than 2 elements!')

    i_missing = _find_nans(xn)
    if np.any(i_missing):
        xn[i_missing] = 0.  # set NaN's to zero
    if dcrit is None:
        dcrit = 1.5 * xn.std()
        if verbose:
            print('dcrit is set to %g' % dcrit)

    if ddcrit is None:
        ddcrit = 1.5 * xn.std()
        if verbose:
            print('ddcrit is set to %g' % ddcrit)

    dxn = diff(xn)
    ddxn = diff(dxn)

    ind = np.hstack((_find_spurious_jumps(dxn, dcrit, name='Dx'),
                     _find_spurious_jumps(ddxn, ddcrit, name='D^2x'),
                     _find_consecutive_equal_values(dxn, zcrit)))

    indg = ones(xn.size, dtype=bool)
    if ind.size > 1:
        ind = unique(ind)
        indg[ind] = 0
    indg, = nonzero(indg)

    if verbose:
        print('Found the total of %d spurious points' % np.size(ind))

    return ind, indg


def common_shape(*args, ** kwds):
    """Return the common shape of a sequence of arrays.

    Parameters
    -----------
    *args : arraylike
        sequence of arrays
    **kwds :
        shape

    Returns
    -------
    shape : tuple
        common shape of the elements of args.

    Raises
    ------
    An error is raised if some of the arrays do not conform
    to the common shape according to the broadcasting rules in numpy.

    Examples
    --------
    >>> import numpy as np
    >>> import wafo.misc as wm
    >>> A = np.ones((4,1))
    >>> B = 2
    >>> C = np.ones((1,5))*5
    >>> np.allclose(wm.common_shape(A,B,C), (4, 5))
    True
    >>> np.allclose(wm.common_shape(A,B,C,shape=(3,4,1)), (3, 4, 5))
    True

    See also
    --------
    broadcast, broadcast_arrays

    """
    shape = kwds.get('shape')
    x0 = 1 if shape is None else np.ones(shape)
    return tuple(np.broadcast(x0, *args).shape)


def argsreduce(condition, * args):
    """ Return the elements of each input array that satisfy some condition.

    Parameters
    ----------
    condition : array_like
        An array whose nonzero or True entries indicate the elements of each
        input array to extract. The shape of 'condition' must match the common
        shape of the input arrays according to the broadcasting rules in numpy.
    arg1, arg2, arg3, ... : array_like
        one or more input arrays.

    Returns
    -------
    narg1, narg2, narg3, ... : ndarray
        sequence of extracted copies of the input arrays converted to the same
        size as the nonzero values of condition.

    Example
    -------
    >>> import wafo.misc as wm
    >>> import numpy as np
    >>> rand = np.random.random_sample
    >>> A = rand((4,5))
    >>> B = 2
    >>> C = rand((1,5))
    >>> cond = np.ones(A.shape)
    >>> [A1,B1,C1] = wm.argsreduce(cond,A,B,C)
    >>> np.allclose(B1.shape, (20,))
    True
    >>> cond[2,:] = 0
    >>> [A2,B2,C2] = wm.argsreduce(cond,A,B,C)
    >>> np.allclose(B2.shape, (15,))
    True

    See also
    --------
    numpy.extract
    """
    newargs = atleast_1d(*args)
    if not isinstance(newargs, list):
        newargs = [newargs, ]
    expand_arr = (condition == condition)
    return [extract(condition, arr1 * expand_arr) for arr1 in newargs]


def stirlerr(n):
    '''
    Return error of Stirling approximation,
        i.e., log(n!) - log( sqrt(2*pi*n)*(n/exp(1))**n )

    Example
    -------
    >>> import wafo.misc as wm
    >>> np.allclose(wm.stirlerr(2),  0.0413407)
    True
    >>> np.allclose(wm.stirlerr(5), 0.01664469)
    True
    >>> np.allclose(wm.stirlerr(8), 0.01041127)
    True
    >>> np.allclose(wm.stirlerr(12), 0.00694284)
    True
    >>> np.allclose(wm.stirlerr(25), 0.00333316)
    True
    >>> np.allclose(wm.stirlerr(70), 0.00119047)
    True
    >>> np.allclose(wm.stirlerr(100), 0.00083333)
    True


    See also
    ---------
    binom


    Reference
    -----------
    Catherine Loader (2000).
    Fast and Accurate Computation of Binomial Probabilities
    <http://lists.gnu.org/archive/html/octave-maintainers/2011-09/pdfK0uKOST642.pdf>
    '''

    S0 = 0.083333333333333333333  # /* 1/12 */
    S1 = 0.00277777777777777777778  # /* 1/360 */
    S2 = 0.00079365079365079365079365  # /* 1/1260 */
    S3 = 0.000595238095238095238095238  # /* 1/1680 */
    S4 = 0.0008417508417508417508417508  # /* 1/1188 */

    n1 = atleast_1d(n)

    y = gammaln(n1 + 1) - log(sqrt(2 * pi * n1) * (n1 / exp(1)) ** n1)

    nn = n1 * n1

    n500 = 500 < n1
    y[n500] = (S0 - S1 / nn[n500]) / n1[n500]
    n80 = logical_and(80 < n1, n1 <= 500)
    if np.any(n80):
        y[n80] = (S0 - (S1 - S2 / nn[n80]) / nn[n80]) / n1[n80]
    n35 = logical_and(35 < n1, n1 <= 80)
    if np.any(n35):
        nn35 = nn[n35]
        y[n35] = (S0 - (S1 - (S2 - S3 / nn35) / nn35) / nn35) / n1[n35]

    n15 = logical_and(15 < n1, n1 <= 35)
    if np.any(n15):
        nn15 = nn[n15]
        y[n15] = (
            S0 - (S1 - (S2 - (S3 - S4 / nn15) / nn15) / nn15) / nn15) / n1[n15]

    return y


def _get_max_deadweight(**ship_property):
    names = list(ship_property)
    _assert(len(ship_property) == 1, 'Only one ship property allowed!')
    name = names[0]
    value = np.array(ship_property[name])
    valid_props = dict(le='length', be='beam', dr='draught',
                       ma='max_deadweigth',
                       se='service_speed', pr='propeller_diameter')
    prop = valid_props[name[:2]]
    prop2max_dw = dict(length=lambda x: (x / 3.45) ** (2.5),
                       beam=lambda x: ((x / 1.78) ** (1 / 0.27)),
                       draught=lambda x: ((x / 0.8) ** (1 / 0.24)),
                       service_speed=lambda x: ((x / 1.14) ** (1 / 0.21)),
                       propeller_diameter=lambda x: (((x / 0.12) ** (4 / 3) /
                                                      3.45) ** (2.5)),
                       max_deadweight=lambda x: x
                       )
    max_deadweight = prop2max_dw.get(prop, lambda x: x)(value)
    return max_deadweight, prop


def getshipchar(**ship_property):
    '''
    Return ship characteristics from value of one ship-property

    Parameters
    ----------
    **ship_property : scalar
        the ship property used in the estimation. Options are:
           'max_deadweight','length','beam','draft','service_speed',
           'propeller_diameter'.
           The length was found from statistics of 40 vessels of size 85 to
           100000 tonn. An exponential curve through 0 was selected, and the
           factor and exponent that minimized the standard deviation of the
           relative error was selected. (The error returned is the same for
           any ship.) The servicespeed was found for ships above 1000 tonns
           only. The propeller diameter formula is from [1]_.

    Returns
    -------
    sc : dict
        containing estimated mean values and standard-deviations of ship
        characteristics:
            max_deadweight    [kkg], (weight of cargo, fuel etc.)
            length            [m]
            beam              [m]
            draught           [m]
            service_speed      [m/s]
            propeller_diameter [m]

    Example
    ---------
    >>> import wafo.misc as wm
    >>> true_sc = {'service_speedSTD': 0,
    ...        'lengthSTD': 2.0113098831942762,
    ...        'draught': 9.5999999999999996,
    ...        'propeller_diameterSTD': 0.20267047566705432,
    ...        'max_deadweight_std': 3096.9000000000001,
    ...        'beam': 29.0, 'length': 216.0,
    ...        'beamSTD': 2.9000000000000004,
    ...        'service_speed': 10.0,
    ...        'draughtSTD': 2.1120000000000001,
    ...        'max_deadweight': 30969.0,
    ...        'propeller_diameter': 6.761165385916601}
    >>> wm.getshipchar(service_speed=10) == true_sc
    True
    >>> sc = wm.getshipchar(service_speed=10)
    >>> sc == true_sc
    True

    Other units: 1 ft = 0.3048 m and 1 knot = 0.5144 m/s


    Reference
    ---------
    .. [1] Gray and Greeley, (1978),
    "Source level model for propeller blade rate radiation for the world's
    merchant fleet", Bolt Beranek and Newman Technical Memorandum No. 458.
    '''

    max_deadweight, prop = _get_max_deadweight(**ship_property)
    property_std = prop + 'STD'

    length = np.round(3.45 * max_deadweight ** 0.40)
    length_err = length ** 0.13

    beam = np.round(1.78 * max_deadweight ** 0.27 * 10) / 10
    beam_err = beam * 0.10

    draught = np.round(0.80 * max_deadweight ** 0.24 * 10) / 10
    draught_err = draught * 0.22

    # S    = round(2/3*(L)**0.525)
    speed = np.round(1.14 * max_deadweight ** 0.21 * 10) / 10
    speed_err = speed * 0.10

    p_diam = 0.12 * length ** (3.0 / 4.0)
    p_diam_err = 0.12 * length_err ** (3.0 / 4.0)

    max_deadweight = np.round(max_deadweight)
    max_deadweight_std = 0.1 * max_deadweight

    shipchar = dict(beam=beam, beamSTD=beam_err,
                    draught=draught, draughtSTD=draught_err,
                    length=length, lengthSTD=length_err,
                    max_deadweight=max_deadweight, max_deadweightSTD=max_deadweight_std,
                    propeller_diameter=p_diam, propeller_diameterSTD=p_diam_err,
                    service_speed=speed, service_speedSTD=speed_err)

    shipchar[property_std] = 0
    return shipchar


def binomln(z, w):
    '''
    Natural Logarithm of binomial coefficient.

    CALL binomln(z,w)

    BINOMLN computes the natural logarithm of the binomial
    function for corresponding elements of Z and W.   The arrays Z and
    W must be real and nonnegative. Both arrays must be the same size,
    or either can be scalar.  BETALOGE is defined as:

    y = LOG(binom(Z,W)) = gammaln(Z)-gammaln(W)-gammaln(Z-W)

    and is obtained without computing BINOM(Z,W). Since the binom
    function can range over very large or very small values, its
    logarithm is sometimes more useful.
    This implementation is more accurate than the log(BINOM(Z,W) implementation
    for large arguments

    Example
    -------

    >>> np.allclose(binomln(3,2), 1.09861229)
    True

    See also
    --------
    binom
    '''
    # log(n!) = stirlerr(n)  + log( sqrt(2*pi*n)*(n/exp(1))**n )
    # y = gammaln(z+1)-gammaln(w+1)-gammaln(z-w+1)
    zpw = z - w
    return (stirlerr(z + 1) - stirlerr(w + 1) - 0.5 * log(2 * pi) -
            (w + 0.5) * log1p(w) + (z + 0.5) * log1p(z) - stirlerr(zpw + 1) -
            (zpw + 0.5) * log1p(zpw) + 1)


def betaloge(z, w):
    '''
    Natural Logarithm of beta function.

    CALL betaloge(z,w)

    BETALOGE computes the natural logarithm of the beta
    function for corresponding elements of Z and W.   The arrays Z and
    W must be real and nonnegative. Both arrays must be the same size,
    or either can be scalar.  BETALOGE is defined as:

    y = LOG(BETA(Z,W)) = gammaln(Z)+gammaln(W)-gammaln(Z+W)

    and is obtained without computing BETA(Z,W). Since the beta
    function can range over very large or very small values, its
    logarithm is sometimes more useful.
    This implementation is more accurate than the BETALN implementation
    for large arguments

    Example
    -------
    >>> import wafo.misc as wm
    >>> np.allclose(wm.betaloge(3,2), -2.48490665)
    True

    See also
    --------
    betaln, beta
    '''
    zpw = z + w
    return (stirlerr(z) + stirlerr(w) + 0.5 * log(2 * pi) + (w - 0.5) * log(w)
            + (z - 0.5) * log(z) - stirlerr(zpw) - (zpw - 0.5) * log(zpw))

    # y = gammaln(z)+gammaln(w)-gammaln(z+w)
    # stirlings approximation:
    #  (-(zpw-0.5).*log(zpw) +(w-0.5).*log(w)+(z-0.5).*log(z) +0.5*log(2*pi))
    # return y


def gravity(phi=45):
    ''' Returns the constant acceleration of gravity

    GRAVITY calculates the acceleration of gravity
    using the international gravitational formulae [1]_:

      g = 9.78049*(1+0.0052884*sin(phir)**2-0.0000059*sin(2*phir)**2)
    where
      phir = phi*pi/180

    Parameters
    ----------
    phi : {float, int}
         latitude in degrees

    Returns
    --------
    g : ndarray
        acceleration of gravity [m/s**2]

    Examples
    --------
    >>> import wafo.misc as wm
    >>> import numpy as np
    >>> phi = np.linspace(0,45,5)
    >>> np.allclose(wm.gravity(phi),
    ...            [ 9.78049   ,  9.78245014,  9.78803583, 9.79640552,  9.80629387])
    True

    See also
    --------
    wdensity

    References
    ----------
    .. [1] Irgens, Fridtjov (1987)
            "Formelsamling i mekanikk:
            statikk, fasthetsl?re, dynamikk fluidmekanikk"
            tapir forlag, University of Trondheim,
            ISBN 82-519-0786-1, pp 19

    '''

    phir = phi * pi / 180.  # change from degrees to radians
    return 9.78049 * (1. + 0.0052884 * sin(phir) ** 2.
                      - 0.0000059 * sin(2 * phir) ** 2.)


def nextpow2(x):
    '''
    Return next higher power of 2

    Example
    -------
    >>> import wafo.misc as wm
    >>> wm.nextpow2(10)
    4
    >>> wm.nextpow2(np.arange(5))
    3
    '''
    t = isscalar(x) or len(x)
    if (t > 1):
        f, n = frexp(t)
    else:
        f, n = frexp(np.abs(x))

    if (f == 0.5):
        n = n - 1
    return n


def discretize(fun, a, b, tol=0.005, n=5, method='linear'):
    '''
    Automatic discretization of function

    Parameters
    ----------
    fun : callable
        function to discretize
    a,b : real scalars
        evaluation limits
    tol : real, scalar
        absoute error tolerance
    n : scalar integer
        number of values to start the discretization with.
    method : string
        defining method of gridding, options are 'linear' and 'adaptive'

    Returns
    -------
    x : discretized values
    y : fun(x)

    Example
    -------
    >>> import wafo.misc as wm
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> x,y = wm.discretize(np.cos, 0, np.pi)
    >>> np.allclose(x[:5], [0.,  0.19634954,  0.39269908,  0.58904862,  0.78539816])
    True

    >>> xa,ya = wm.discretize(np.cos, 0, np.pi, method='adaptive')
    >>> np.allclose(xa[:5], [0.,  0.19634954,  0.39269908,  0.58904862,  0.78539816])
    True

    t = plt.plot(x, y, xa, ya, 'r.')
    plt.show()
    plt.close('all')

    '''
    if method.startswith('a'):
        return _discretize_adaptive(fun, a, b, tol, n)
    else:
        return _discretize_linear(fun, a, b, tol, n)


def _discretize_linear(fun, a, b, tol=0.005, n=5):
    '''
    Automatic discretization of function, linear gridding
    '''
    x = linspace(a, b, n)
    y = fun(x)

    err0 = inf
    err = 10000
    nmax = 2 ** 20
    num_tries = 0
    while (num_tries < 5 and err > tol and n < nmax):
        err0 = err
        x0 = x
        y0 = y
        n = 2 * (n - 1) + 1
        x = linspace(a, b, n)
        y = fun(x)
        y00 = interp(x, x0, y0)
        err = 0.5 * amax(np.abs(y00 - y) / (np.abs(y00) + np.abs(y) + _TINY + tol))
        num_tries += int(abs(err - err0) <= tol / 2)
    return x, y


def _discretize_adaptive(fun, a, b, tol=0.005, n=5):
    '''
    Automatic discretization of function, adaptive gridding.
    '''
    n += (mod(n, 2) == 0)  # make sure n is odd
    x = linspace(a, b, n)
    fx = fun(x)

    n2 = (n - 1) // 2
    erri = hstack((zeros((n2, 1)), ones((n2, 1)))).ravel()
    err = erri.max()
    err0 = inf
    num_tries = 0
    # reltol = abstol = tol
    for j in range(50):
        if num_tries < 5 and err > tol:
            err0 = err
            # find top errors

            ix, = where(erri > tol)
            # double the sample rate in intervals with the most error
            y = (vstack(((x[ix] + x[ix - 1]) / 2,
                         (x[ix + 1] + x[ix]) / 2)).T).ravel()
            fy = fun(y)
            fy0 = interp(y, x, fx)

            abserr = np.abs(fy0 - fy)
            erri = 0.5 * (abserr / (np.abs(fy0) + np.abs(fy) + _TINY + tol))
            # converged = abserr <= np.maximum(abseps, releps * abs(fy))
            # converged = abserr <= np.maximum(tol, tol * abs(fy))
            err = erri.max()

            x = hstack((x, y))

            ix = x.argsort()
            x = x[ix]
            erri = hstack((zeros(len(fx)), erri))[ix]
            fx = hstack((fx, fy))[ix]
            num_tries += int(abs(err - err0) <= tol / 2)
        else:
            break
    else:
        warnings.warn('Recursion level limit reached j=%d' % j)

    return x, fx


def polar2cart(theta, rho, z=None):
    '''
    Transform polar coordinates into 2D cartesian coordinates.

    Returns
    -------
    x, y : array-like
        Cartesian coordinates, x = rho*cos(theta), y = rho*sin(theta)

    Examples
    --------
    >>> np.allclose(polar2cart(0, 1, 1), (1, 0, 1))
    True
    >>> np.allclose(polar2cart(0, 1), (1, 0))
    True

    See also
    --------
    cart2polar
    '''
    x, y = rho * cos(theta), rho * sin(theta)
    if z is None:
        return x, y
    return x, y, z


pol2cart = polar2cart


def cart2polar(x, y, z=None):
    ''' Transform 2D cartesian coordinates into polar coordinates.

    Returns
    -------
    theta : array-like
        radial angle, arctan2(y,x)
    rho : array-like
        radial distance, sqrt(x**2+y**2)

    Examples
    --------
    >>> np.allclose(cart2polar(1, 0, 1), (0, 1, 1))
    True
    >>> np.allclose(cart2polar(1, 0), (0, 1))
    True

    See also
    --------
    polar2cart
    '''
    t, r = arctan2(y, x), hypot(x, y)
    if z is None:
        return t, r
    return t, r, z


cart2pol = cart2polar


def ndgrid(*args, **kwargs):
    """
    Same as calling meshgrid with indexing='ij' (see meshgrid for
    documentation).

    Example
    -------
    >>> x, y = ndgrid([1,2,3],[4,5,6])
    >>> np.allclose(x, [[1, 1, 1],
    ...                 [2, 2, 2],
    ...                 [3, 3, 3]])
    True
    >>> np.allclose(y, [[4, 5, 6],
    ...                 [4, 5, 6],
    ...                 [4, 5, 6]])
    True
    """
    kwargs['indexing'] = 'ij'
    return meshgrid(*args, ** kwargs)


def trangood(x, f, min_n=None, min_x=None, max_x=None, max_n=inf):
    """
    Make sure transformation is efficient.

    Parameters
    ------------
    x, f : array_like
        input transform function, (x,f(x)).
    min_n : scalar, int
        minimum number of points in the good transform.
               (Default  x.shape[0])
    min_x : scalar, real
        minimum x value to transform. (Default  min(x))
    max_x : scalar, real
        maximum x value to transform. (Default  max(x))
    max_n : scalar, int
        maximum number of points in the good transform
              (default inf)
    Returns
    -------
    x, f : array_like
        the good transform function.

    TRANGOOD interpolates f linearly  and optionally
    extrapolate it linearly outside the range of x
    with X uniformly spaced.

    See also
    ---------
    tranproc,
    numpy.interp
    """
    xo, fo = atleast_1d(x, f)

    _assert(xo.ndim == 1, 'x must be a vector.')
    _assert(fo.ndim == 1, 'f  must be a vector.')

    i = xo.argsort()
    xo, fo = xo[i], fo[i]
    del i
    dx = diff(xo)
    _assert(all(dx > 0), 'Duplicate x-values not allowed.')

    nf = fo.shape[0]

    max_x = xo[-1] if max_x is None else max_x
    min_x = xo[0] if min_x is None else min_x
    min_n = nf if min_n is None else min_n
    min_n = max(min_n, 2)
    max_n = max(max_n, 2)

    ddx = diff(dx)
    xn = xo[-1]
    x0 = xo[0]
    L = float(xn - x0)
    if nf < min_n or max_n < nf or np.any(np.abs(ddx) > 10 * _EPS * L):
        # pab 07.01.2001: Always choose the stepsize df so that
        # it is an exactly representable number.
        # This is important when calculating numerical derivatives and is
        # accomplished by the following.
        dx = L / (min(min_n, max_n) - 1)
        dx = (dx + 2.) - 2.
        xi = arange(x0, xn + dx / 2., dx)
        # New call pab 11.11.2000: This is much quicker
        fo = interp(xi, xo, fo)
        xo = xi

    # x is now uniformly spaced
    dx = xo[1] - xo[0]

    # Extrapolate linearly outside the range of ff
    if min_x < xo[0]:
        x1 = dx * arange(floor((min_x - xo[0]) / dx), -2)
        f2 = fo[0] + x1 * (fo[1] - fo[0]) / (xo[1] - xo[0])
        fo = hstack((f2, fo))
        xo = hstack((x1 + xo[0], xo))

    if max_x > xo[-1]:
        x1 = dx * arange(1, ceil((max_x - xo[-1]) / dx) + 1)
        f2 = f[-1] + x1 * (f[-1] - f[-2]) / (xo[-1] - xo[-2])
        fo = hstack((fo, f2))
        xo = hstack((xo, x1 + xo[-1]))

    return xo, fo


def tranproc(x, f, x0, *xi):
    """
    Transforms process X and up to four derivatives
          using the transformation f.

    Parameters
    ----------
    x,f : array-like
        [x,f(x)], transform function, y = f(x).
    x0, x1,...,xn : vectors
        where xi is the i'th time derivative of x0. 0<=n<=4.

    Returns
    -------
    y0, y1,...,yn : vectors
        where yi is the i'th time derivative of y0 = f(x0).

    By the basic rules of derivation:
    Y1 = f'(X0)*X1
    Y2 = f''(X0)*X1^2 + f'(X0)*X2
    Y3 = f'''(X0)*X1^3 + f'(X0)*X3 + 3*f''(X0)*X1*X2
    Y4 = f''''(X0)*X1^4 + f'(X0)*X4 + 6*f'''(X0)*X1^2*X2
      + f''(X0)*(3*X2^2 + 4*X1*X3)

    The derivation of f is performed numerically with a central difference
    method with linear extrapolation towards the beginning and end of f,
    respectively.

    Example
    --------
    Derivative of g and the transformed Gaussian model.
    >>> import matplotlib.pyplot as plt
    >>> import wafo.misc as wm
    >>> import wafo.transform.models as wtm
    >>> tr = wtm.TrHermite()
    >>> x = np.linspace(-5, 5, 501)
    >>> g = tr(x)
    >>> gder = wm.tranproc(x, g, x, ones(g.shape[0]))
    >>> np.allclose(gder[1][:5],
    ... [ 1.09938766,  1.39779849,  1.39538745,  1.39298656,  1.39059575])
    True

    h = plt.plot(x, g, x, gder[1])
    plt.plot(x,pdfnorm(g)*gder[1],x,pdfnorm(x))
    plt.legend('Transformed model','Gaussian model')

    plt.close('all')

    See also
    --------
    trangood.
    """
    def _default_step(xo, num_derivatives):
        hn = xo[1] - xo[0]
        if hn ** num_derivatives < sqrt(_EPS):
            msg = ('Numerical problems may occur for the derivatives in ' +
                   'tranproc.\n' +
                   'The sampling of the transformation may be too small.')
            warnings.warn(msg)
        return hn

    def _diff(xo, fo, x0, num_derivatives):
        hn = _default_step(xo, num_derivatives)
        # Transform X with the derivatives of  f.
        fder = vstack((xo, fo))
        fxder = zeros((num_derivatives, x0.size))
        for k in range(num_derivatives):  # Derivation of f(x) using a difference method.
            n = fder.shape[-1]
            fder = vstack([(fder[0, 0:n - 1] + fder[0, 1:n]) / 2,
                           diff(fder[1, :]) / hn])
            fxder[k] = tranproc(fder[0], fder[1], x0)
        return fxder

    def _der_1(fxder, xi):
        """First time derivative of y: y1 = f'(x)*x1"""
        return fxder[0] * xi[0]

    def _der_2(fxder, xi):
        """Second time derivative of y: y2 = f''(x)*x1.^2+f'(x)*x2"""
        return fxder[1] * xi[0] ** 2. + fxder[0] * xi[1]

    def _der_3(fxder, xi):
        """Third time derivative of y:
        y3 = f'''(x)*x1.^3+f'(x)*x3 +3*f''(x)*x1*x2
        """
        return (fxder[2] * xi[0] ** 3 + fxder[0] * xi[2] +
                3 * fxder[1] * xi[0] * xi[1])

    def _der_4(fxder, xi):
        """Fourth time derivative of y:
            y4 = f''''(x)*x1.^4+f'(x)*x4 +
                 6*f'''(x)*x1^2*x2+f''(x)*(3*x2^2+4x1*x3)
        """
        return (fxder[3] * xi[0] ** 4. + fxder[0] * xi[3] +
                6. * fxder[2] * xi[0] ** 2. * xi[1] +
                fxder[1] * (3. * xi[1] ** 2. + 4. * xi[0] * xi[1]))

    xo, fo, x0 = atleast_1d(x, f, x0)
    xi = atleast_1d(*xi)
    if not isinstance(xi, list):
        xi = [xi, ]
    num_derivatives = len(xi)  # num_derivatives = number of derivatives
    nmax = ceil((xo.ptp()) * 10 ** (7. / max(num_derivatives, 1)))
    xo, fo = trangood(xo, fo, min_x=min(x0), max_x=max(x0), max_n=nmax)

    n = f.shape[0]
    xu = (n - 1) * (x0 - xo[0]) / (xo[-1] - xo[0])

    fi = asarray(floor(xu), dtype=int)
    fi = where(fi == n - 1, fi - 1, fi)

    xu = xu - fi
    y0 = fo[fi] + (fo[fi + 1] - fo[fi]) * xu

    y = y0
    if num_derivatives > 4:
        warnings.warn('Transformation of derivatives of order>4 is ' +
                      'not supported.')
        num_derivatives = 4
    if num_derivatives > 0:
        y = [y0]
        fxder = _diff(xo, fo, x0, num_derivatives)
        # Calculate the transforms of the derivatives of X.
        dfuns = [_der_1, _der_2, _der_3, _der_4]
        for dfun in dfuns[:num_derivatives]:
            y.append(dfun(fxder, xi))

    return y


# pylint: disable=redefined-builtin
def good_bins(data=None, range=None, num_bins=None, odd=False, loose=True):  # @ReservedAssignment
    ''' Return good bins for histogram

    Parameters
    ----------
    data : array-like
        the data
    range : (float, float)
        minimum and maximum range of bins (default data.min(), data.max())
    num_bins : scalar integer
        approximate number of bins wanted
        (default depending on num_data=len(data))
    odd : bool
        placement of bins (0 or 1) (default 0)
    loose : bool
        if True add extra space to min and max
        if False the bins are made tight to the min and max

    Example
    -------
    >>> import wafo.misc as wm
    >>> np.allclose(wm.good_bins(range=(0,5), num_bins=6),
    ...             [-1.,  0.,  1.,  2.,  3.,  4.,  5.,  6.])
    True
    >>> np.allclose(wm.good_bins(range=(0,5), num_bins=6, loose=False),
    ...             [ 0.,  1.,  2.,  3.,  4.,  5.])
    True
    >>> np.allclose(wm.good_bins(range=(0,5), num_bins=6, odd=True),
    ...            [-1.5, -0.5,  0.5,  1.5,  2.5,  3.5,  4.5,  5.5,  6.5])
    True
    >>> np.allclose(wm.good_bins(range=(0,5), num_bins=6, odd=True, loose=False),
    ...             [-0.5,  0.5,  1.5,  2.5,  3.5,  4.5,  5.5])
    True
    '''
    def _default_range(range_, x):
        return range_ if range_ else (x.min(), x.max())

    def _default_bins(num_bins, x):
        if num_bins is None:
            num_bins = np.ceil(4 * np.sqrt(np.sqrt(len(x))))
        return num_bins

    def _default_step(mn, mx, num_bins):
        d = float(mx - mn) / num_bins * 2
        e = np.floor(np.log(d) / np.log(10))
        m = np.clip(np.floor(d / 10 ** e), a_min=0, a_max=5)
        if 2 < m < 5:
            m = 2
        return m * 10 ** e

    if data is not None:
        data = np.atleast_1d(data)

    mn, mx = _default_range(range, data)
    num_bins = _default_bins(num_bins, data)
    d = _default_step(mn, mx, num_bins)
    mn = (np.floor(mn / d) - loose) * d - odd * d / 2
    mx = (np.ceil(mx / d) + loose) * d + odd * d / 2
    limits = np.arange(mn, mx + d / 2, d)
    return limits


def _make_bars(limits, bin_):
    limits.shape = (-1, 1)
    xx = limits.repeat(3, axis=1)
    xx.shape = (-1,)
    xx = xx[1:-1]
    bin_.shape = (-1, 1)
    yy = bin_.repeat(3, axis=1)
    # yy[0,0] = 0.0 # pdf
    yy[:, 0] = 0.0  # histogram
    yy.shape = (-1,)
    yy = np.hstack((yy, 0.0))
    return xx, yy


# pylint: disable=redefined-builtin
def _histogram(data, bins=None, range=None, normed=False, weights=None,  # @ReservedAssignment
               density=None):
    """
    Example
    -------
    >>> import numpy as np
    >>> data = np.linspace(0, 10)
    >>> xx, yy, limits = _histogram(data)
    >>> len(limits)
    12
    >>> xx, yy, limits = _histogram(data, bins=[0, 5, 11])
    >>> np.allclose(xx, [ 0,  0,  5,  5,  5, 11, 11])
    True
    >>> np.allclose(yy, [  0.,  25.,  25.,   0.,  25.,  25.,   0.])
    True
    >>> np.allclose(limits, [[ 0], [ 5], [11]])
    True

    """
    x = np.atleast_1d(data)
    if bins is None:
        bins = int(np.ceil(4 * np.sqrt(np.sqrt(len(x)))))
    bin_, limits = np.histogram(data, bins=bins, range=range, normed=normed,
                                weights=weights, density=density)
    xx, yy = _make_bars(limits, bin_)
    return xx, yy, limits


def plot_histgrm(data, bins=None, range=None,  # @ReservedAssignment
                 normed=False, weights=None, density=None, lintype='b-'):
    '''
    Plot histogram

    Parameters
    -----------
    data : array-like
        the data
    bins : int or sequence of scalars, optional
        If an int, it defines the number of equal-width
        bins in the given range (4 * sqrt(sqrt(len(data)), by default).
        If a sequence, it defines the bin edges, including the
        rightmost edge, allowing for non-uniform bin widths.
    range : (float, float), optional
        The lower and upper range of the bins.  If not provided, range
        is simply ``(data.min(), data.max())``.  Values outside the range are
        ignored.
    normed : bool, optional
        If False, the result will contain the number of samples in each bin.
        If True, the result is the value of the probability *density* function
        at the bin, normalized such that the *integral* over the range is 1.
    weights : array_like, optional
        An array of weights, of the same shape as `data`.  Each value in `data`
        only contributes its associated weight towards the bin count
        (instead of 1).  If `normed` is True, the weights are normalized,
        so that the integral of the density over the range remains 1
    lintype : specify color and lintype, see PLOT for possibilities.

    Returns
    -------
    h : list
        of plot-objects

    Example
    -------
    >>> import matplotlib.pyplot as plt
    >>> import wafo.misc as wm
    >>> import wafo.stats as ws
    >>> R = ws.weibull_min.rvs(2,loc=0,scale=2, size=100)
    >>> R = np.linspace(0,10)
    >>> bins = good_bins(R)
    >>> len(bins)
    13

    >>> x = np.linspace(-3,16,200)
    >>> pdf = ws.weibull_min.pdf(x,2,0,2)

    h0 = wm.plot_histgrm(R, 20, normed=True)
    h1 = plt.plot(x, pdf,'r')
    plt.close('all')

    See also
    --------
    wafo.misc.good_bins
    numpy.histogram
    '''

    xx, yy, limits = _histogram(data, bins, range, normed, weights, density)
    return plt.plot(xx, yy, lintype, limits, limits * 0)


def num2pistr(x, n=3, numerator_max=10, denominator_max=10):
    '''
    Convert a scalar to a text string in fractions of pi
        if the numerator is less than 10 and not equal 0
               and if the denominator is less than 10.

    Parameters
    ----------
    x   = a scalar
    n   = maximum digits of precision. (default 3)

    Returns
    -------
    xtxt = a text string in fractions of pi

    Example
    -------
    >>> import wafo.misc as wm
    >>> wm.num2pistr(np.pi*3/4)=='3\\pi/4'
    True
    >>> wm.num2pistr(-np.pi/4)=='-\\pi/4'
    True
    >>> wm.num2pistr(-np.pi)=='-\\pi'
    True
    >>> wm.num2pistr(-1/4)=='-0.25'
    True
    '''
    def _denominator_text(den):
        return '' if np.abs(den) == 1 else '/%d' % den

    def _numerator_text(num):
        if np.abs(num) == 1:
            return '-' if num == -1 else ''
        return '{:d}'.format(num)
    frac = fractions.Fraction.from_float(x / pi).limit_denominator(int(1e+13))
    num, den = frac.numerator, frac.denominator
    if (den < denominator_max) and (num < numerator_max) and (num != 0):
        return r'{0:s}\pi{1:s}'.format(_numerator_text(num),
                                       _denominator_text(den))
    fmt = '{:0.' + '{:d}'.format(n) + 'g}'
    return fmt.format(x)


def fourier(data, t=None, period=None, m=None, method='trapz'):
    '''
    Returns Fourier coefficients.

    Parameters
    ----------
    data : array-like
        vector or matrix of row vectors with data points shape p x n.
    t : array-like
        vector with n values indexed from 1 to n.
    period : real scalar, (default T = t[-1]-t[0])
        primitive period of signal, i.e., smallest period.
    m : scalar integer
        defines no of harmonics desired (default m = n)
    method : string
        integration method used

    Returns
    -------
    a,b  = Fourier coefficients size m x p

    FOURIER finds the coefficients for a Fourier series representation
    of the signal x(t) (given in digital form).  It is assumed the signal
    is periodic over T.  N is the number of data points, and M-1 is the
    number of coefficients.

    The signal can be estimated by using M-1 harmonics by:
                        M-1
     x[i] = 0.5*a[0] + sum (a[n]*c[n,i] + b[n]*s[n,i])
                       n=1
    where
       c[n,i] = cos(2*pi*(n-1)*t[i]/T)
       s[n,i] = sin(2*pi*(n-1)*t[i]/T)

    Note that a[0] is the "dc value".
    Remaining values are a[1], a[2], ... , a[M-1].

    Example
    -------
    >>> import wafo.misc as wm
    >>> import numpy as np
    >>> T = 2*np.pi
    >>> t = np.linspace(0,4*T)
    >>> x = np.sin(t)
    >>> a, b = wm.fourier(x, t, period=T, m=5)
    >>> np.allclose(a, 0)
    True
    >>> np.allclose(b.ravel(),
    ...             [ 0.,  4.,  0.,  0.,  0.])
    True

    See also
    --------
    fft
    '''
    x = np.atleast_2d(data)
    p, n = x.shape
    t = np.arange(n) if t is None else np.atleast_1d(t)

    n = len(t) if n is None else n
    m = n if m is None else m
    period = t[-1] - t[0] if period is None else period
    intfun = trapz if method.startswith('trapz') else simps

    # Define the vectors for computing the Fourier coefficients
    t.shape = (1, -1)
    a = zeros((m, p))
    b = zeros((m, p))
    a[0] = intfun(x, t, axis=-1)

    # Compute M-1 more coefficients
    tmp = 2 * pi * t / period
    for i in range(1, m):
        a[i] = intfun(x * cos(i * tmp), t, axis=-1)
        b[i] = intfun(x * sin(i * tmp), t, axis=-1)

    a = a / pi
    b = b / pi

    # Alternative:  faster for large M, but gives different results than above.
#    nper = diff(t([1 end]))/T; %No of periods given
#    if nper == round(nper):
#        N1 = n/nper
#    else:
#        N1 = n
#
#
#
# Fourier coefficients by fft
#    Fcof1 = 2*ifft(x(1:N1,:),[],1);
#    Pcor = [1; exp(sqrt(-1)*(1:M-1).'*t(1))] # correction term to get
#                                             # the correct integration limits
#    Fcof = Fcof1(1:M,:).*Pcor(:,ones(1,P));
#    a = real(Fcof(1:M,:));
#    b = imag(Fcof(1:M,:));

    return a, b


if __name__ == "__main__":
    from wafo.testing import test_docstrings
    test_docstrings(__file__)
