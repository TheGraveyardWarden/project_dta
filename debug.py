_debug = True

def debug(x: str):
    if _debug:
        print(x)

def debug_set(val: bool):
    _debug = val
