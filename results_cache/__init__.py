import shelve
import inspect
import numpy

__all__ = ['cached']

def tuplify(value):
    """Recursively peruse value and change any immutable objects
    (dicts, lists) into sorted, mutable objects with the same content
    (tuple of tuples, tuple). Useful to create unique hashes."""
    if isinstance(value, dict):
        return tuple(sorted([(tuplify(k), tuplify(v)) for k,v in value.iteritems()]))
    elif isinstance(value, list):
        return tuple([tuplify(x) for x in value])
    elif isinstance(value, numpy.ndarray):
        return tuple([tuplify(x) for x in value])
    else:
        return value

# Decorator to be used on functions whose return values can be cached
def cached(cache_filename=None):
    """Decorator to transparently cache data from a function using a
    key-value storage (python's shelve) with hashes of the arguments
    as keys. The cache_filename can be specified as an optional
    argument. Otherwise a hidden file called '.cache_[functionname]'
    is used.
    """
    def cached_function_factory(function):
        # Get argument names and default values into a dictionary
        argnames,_,_,argdefs = inspect.getargspec(function)
        defs = [None]*len(argnames)
        if not argdefs is None:
            for i in range(len(argdefs)):
                defs[i-len(argdefs)] = argdefs[i]
        argvalues = {a:b for a,b in zip(argnames, defs)}
        
        def cached_function(*args, **kwargs):
            # Copy the default argument values dictionary and update it
            # with the actual given arguments
            argvals = dict(argvalues)
            for i in range(len(args)):
                argvals[argnames[i]] = args[i]
            argvals.update(kwargs)

            # Generate a key by tuplifying and hashing the arguments
            key = repr(hash(tuplify(argvals)))

            try:
                return res_cache_shelve[key]['data']
            except KeyError:
                result_data = function(**argvals)
                res_cache_shelve[key] = {'arguments': argvals,
                                         'data': result_data}
                res_cache_shelve.sync()
                return result_data

        cached_function.__doc__ = function.__doc__
        return cached_function

    # Use .cache_[functionname] as the default cache name if none was
    # specified.
    if cache_filename is None:
        cache_filename = ".cache_" + function.__name__
    res_cache_shelve = shelve.open(cache_filename, 'c')

    return cached_function_factory
