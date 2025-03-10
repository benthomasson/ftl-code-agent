import importlib
import os
import types
import inspect


class Bunch:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def get_functions(code_file):

    # Load module from file path
    if not code_file.endswith(".py"):
        raise Exception("Expects a python file")
    module_name = os.path.basename(code_file[:-3])
    spec = importlib.util.spec_from_file_location(module_name, code_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    fns = []

    # Find and instantiate the Tool class
    for item_name in dir(module):
        item = getattr(module, item_name)
        if isinstance(item, types.FunctionType):
            fns.append(item)

    return module, fns


def get_function_code(fn):
    return inspect.getsource(fn)
