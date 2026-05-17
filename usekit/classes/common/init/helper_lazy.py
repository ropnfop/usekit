# Path: usekit.classes.common.init.helper_lazy
# ----------------------------------------------------------------------------------------------- 
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# ----------------------------------------------------------------------------------------------- 

from typing import Callable, Any, Optional, List
from functools import wraps
import threading
from concurrent.futures import ThreadPoolExecutor, Future

class LazyValue:
    """Wrapper for deferred (lazy) evaluation of a value."""
    
    def __init__(self, factory: Callable[[], Any]):
        self._factory = factory
        self._value = None
        self._computed = False
        self._lock = threading.Lock()
        self._future: Optional[Future] = None
    
    def __call__(self) -> Any:
        """Compute and return the value (only once)."""
        if not self._computed:
            with self._lock:
                if not self._computed:
                    # If background loading is in progress, wait for it
                    if self._future is not None:
                        self._value = self._future.result()
                        self._future = None
                    else:
                        self._value = self._factory()
                    self._computed = True
        return self._value
    
    def force(self) -> Any:
        """Force the computation of the value."""
        return self()
    
    @property
    def is_computed(self) -> bool:
        """Check whether the value has been computed."""
        return self._computed
    
    @property
    def is_loading(self) -> bool:
        """Check whether the value is being loaded in background."""
        return self._future is not None and not self._future.done()
    
    def start_background_load(self, executor: Optional[ThreadPoolExecutor] = None):
        """Start loading the value in background."""
        if not self._computed and self._future is None:
            with self._lock:
                if not self._computed and self._future is None:
                    if executor is None:
                        executor = ThreadPoolExecutor(max_workers=1)
                    self._future = executor.submit(self._factory)
    
    def reset(self):
        """Reset the computed value."""
        with self._lock:
            self._value = None
            self._computed = False
            if self._future is not None:
                self._future.cancel()
                self._future = None

class ParallelLazyLoader:
    """Parallel background loader for multiple LazyValue objects."""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lazy_values: List[LazyValue] = []
    
    def add(self, *lazy_values: LazyValue):
        """Add LazyValue objects to the loader."""
        self._lazy_values.extend(lazy_values)
        return self
    
    def start_all(self):
        """Start loading all registered LazyValue objects in parallel."""
        for lv in self._lazy_values:
            lv.start_background_load(self.executor)
        return self
    
    def wait_all(self, timeout: Optional[float] = None) -> List[Any]:
        """Wait for all lazy values to be computed and return their values."""
        return [lv.force() for lv in self._lazy_values]
    
    def is_all_loaded(self) -> bool:
        """Check if all lazy values have been computed."""
        return all(lv.is_computed for lv in self._lazy_values)
    
    def shutdown(self, wait: bool = True):
        """Shutdown the executor."""
        self.executor.shutdown(wait=wait)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

class lazy:
    """Utility class for lazy loading and evaluation."""
    
    @staticmethod
    def value(factory: Callable[[], Any]) -> LazyValue:
        """
        Create a lazily evaluated value.
        
        Example:
            expensive = lazy.value(lambda: compute_expensive_value())
            result = expensive()  # Computed only on first call
        """
        return LazyValue(factory)
    
    @staticmethod
    def property(func: Callable) -> property:
        """
        Lazy-loading property decorator.
        
        Example:
            class MyClass:
                @lazy.property
                def expensive_attr(self):
                    return compute_expensive_value()
        """
        attr_name = f'_lazy_{func.__name__}'
        
        @wraps(func)
        def wrapper(self):
            if not hasattr(self, attr_name):
                setattr(self, attr_name, func(self))
            return getattr(self, attr_name)
        
        return property(wrapper)
    
    @staticmethod
    def function(func: Callable) -> Callable:
        """
        Decorator for caching the result of a function with no arguments.
        
        Example:
            @lazy.function
            def get_config():
                return load_config_file()
        """
        result = {}
        lock = threading.Lock()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = 'result'
            if key not in result:
                with lock:
                    if key not in result:
                        result[key] = func(*args, **kwargs)
            return result[key]
        
        wrapper.reset = lambda: result.clear()
        return wrapper
    
    @staticmethod
    def import_module(module_name: str):
        """
        Lazily import a module.
        
        Example:
            numpy = lazy.import_module('numpy')
            arr = numpy().array([1, 2, 3])
        """
        def factory():
            import importlib
            return importlib.import_module(module_name)
        return LazyValue(factory)
    
    @staticmethod
    def chain(*lazy_values: LazyValue) -> LazyValue:
        """
        Chain multiple LazyValue objects together.
        
        Example:
            result = lazy.chain(lazy1, lazy2, lazy3)
            values = result()  # [lazy1(), lazy2(), lazy3()]
        """
        def factory():
            return [lv() for lv in lazy_values]
        return LazyValue(factory)
    
    @staticmethod
    def parallel(*lazy_values: LazyValue, max_workers: Optional[int] = None) -> ParallelLazyLoader:
        """
        Create a parallel loader for multiple LazyValue objects.
        
        Example:
            loader = lazy.parallel(lazy1, lazy2, lazy3)
            loader.start_all()
            # Do other work...
            results = loader.wait_all()
        """
        return ParallelLazyLoader(max_workers=max_workers).add(*lazy_values)
    
    @staticmethod
    def preload(*lazy_values: LazyValue, max_workers: Optional[int] = None):
        """
        Immediately start loading multiple LazyValue objects in background.
        
        Example:
            lazy.preload(lazy1, lazy2, lazy3)
            # Values are loading in background
            # Access them later with lazy1(), lazy2(), lazy3()
        """
        loader = ParallelLazyLoader(max_workers=max_workers)
        loader.add(*lazy_values)
        loader.start_all()
        return loader

class LazyDict(dict):
    """Dictionary that supports lazy loading of values."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._factories = {}
    
    def set_lazy(self, key: str, factory: Callable[[], Any]):
        """Register a key–value pair for lazy evaluation."""
        self._factories[key] = factory
    
    def __getitem__(self, key):
        if key in self._factories and key not in self:
            self[key] = self._factories[key]()
            del self._factories[key]
        return super().__getitem__(key)
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
    
    def preload_all(self, max_workers: Optional[int] = None):
        """Preload all lazy values in parallel."""
        lazy_values = [lazy.value(factory) for factory in self._factories.values()]
        keys = list(self._factories.keys())
        
        with ParallelLazyLoader(max_workers=max_workers) as loader:
            loader.add(*lazy_values).start_all()
            results = loader.wait_all()
        
        for key, value in zip(keys, results):
            self[key] = value
            del self._factories[key]

class LazyList(list):
    """List that supports lazy element computation."""
    
    def __init__(self, *factories: Callable[[], Any]):
        super().__init__()
        self._factories = list(factories)
        self._computed_indices = set()
    
    def __getitem__(self, index):
        if index not in self._computed_indices:
            if index < len(self._factories):
                while len(self) <= index:
                    self.append(None)
                list.__setitem__(self, index, self._factories[index]())
                self._computed_indices.add(index)
        return super().__getitem__(index)
    
    def force_all(self):
        """Force the computation of all elements."""
        for i in range(len(self._factories)):
            _ = self[i]
        return self
    
    def preload_all(self, max_workers: Optional[int] = None):
        """Preload all elements in parallel."""
        lazy_values = [lazy.value(factory) for factory in self._factories]
        
        with ParallelLazyLoader(max_workers=max_workers) as loader:
            loader.add(*lazy_values).start_all()
            results = loader.wait_all()
        
        for i, value in enumerate(results):
            while len(self) <= i:
                self.append(None)
            list.__setitem__(self, i, value)
            self._computed_indices.add(i)
        
        return self

# Convenience functions
def lz(factory: Callable[[], Any]) -> LazyValue:
    """Shortcut for lazy.value."""
    return lazy.value(factory)

def lzm(module_name: str) -> LazyValue:
    """Shortcut for lazy.import_module."""
    return lazy.import_module(module_name)

def lzp(*lazy_values: LazyValue, max_workers: Optional[int] = None) -> ParallelLazyLoader:
    """Shortcut for lazy.parallel."""
    return lazy.parallel(*lazy_values, max_workers=max_workers)

__all__ = [
    'lazy', 'LazyValue', 'LazyDict', 'LazyList', 
    'ParallelLazyLoader', 'lz', 'lzm', 'lzp'
]

# ----------------------------------------------------------------------------------------------- 
#  [ withropnfop@gmail.com ] 
# -----------------------------------------------------------------------------------------------