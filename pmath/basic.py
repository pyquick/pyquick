def pow(x, y):
    for i in range(y):
        x *= x
    return x
def sqrt(x):
    return x**0.5
def abs(a):
    if(a<0):
        a+=-2*a
    if(a>=0):
        a=a
    return a
