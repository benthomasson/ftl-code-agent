

from redbaron import RedBaron

def test_1():
    code = '''
def add(a: int, b: int) -> int:
    """ 
    Adds a and b together

    Args:
        a: a number
        b: another number

    Returns:
        The sum of the numbers
    """ 
    return a + b 

complete()
    '''
    red = RedBaron(code)
    for o in red:
        print(o.name, o.type)
    assert False

