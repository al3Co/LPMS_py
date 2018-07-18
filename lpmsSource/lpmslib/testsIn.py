try:
    from LpmsConfig import *
    print("Hi")
except ImportError:
	from .LpmsConfig import *
	print("Hi 2")