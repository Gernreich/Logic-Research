#!/Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7
import numpy as np
import sys

arg1 = sys.argv[1]
arg2 = sys.argv[2]
#arg3 = sys.argv[3]

# sigmoid function
def nonlin(x,deriv=False):
    if(deriv==True):
        return x*(1-x)
    return 1/(1+np.exp(-x))
    
X = np.array([  [0,0],
                [0,1],
                [1,0],
                [1,1] ])

y = np.array([[.5,.51,.51,0.0]]).T

# seed random numbers to make calculation
# deterministic (just a good practice)
np.random.seed(int(arg1))

# initialize weights randomly with mean 0
syn0 = 100 * np.random.random((2,1)) - 50
for iter in range(int(arg2)):
    # forward propagation
    l0 = X
    l1 = nonlin(np.dot(l0,syn0))

    # how much did we miss?
    l1_error = y - l1

    # multiply how much we missed by the 
    # slope of the sigmoid at the values in l1
    l1_delta = l1_error * nonlin(l1,True)

    # update weights
    syn0 += np.dot(l0.T,l1_delta)

print(syn0)
print()
print(l1)
