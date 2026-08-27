#!/Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7
import numpy as np
import sys

firstarg = sys.argv[1]
sndlyr = sys.argv[2]

# sigmoid function
def nonlin(x,deriv=False):
    if(deriv==True):
        return x*(1-x)
    return 1/(1+np.exp(-x))
    
X = np.array([  [0,0,0,0],
                [0,0,0,1],
                [0,0,1,0],
                [0,0,1,1],
                [0,1,0,0],
                [0,1,0,1],
                [0,1,1,0],
                [0,1,1,1],
                [1,0,0,0],
                [1,0,0,1],
                [1,0,1,0],
                [1,0,1,1],
                [1,1,0,0],
                [1,1,0,1],
                [1,1,1,0],
                [1,1,1,1] ])

y = np.array([[0.0,0.067,0.133,0.2,0.267,0.333,0.4,0.467,0.533,0.6,0.667,0.733,0.8,0.867,0.933,1.0]]).T

# seed random numbers to make calculation
# deterministic (just a good practice)
np.random.seed(int(firstarg))

# initialize weights randomly with mean 0
syn0 = 2*np.random.random((4,int(sndlyr))) - 1
syn1 = 2*np.random.random((int(sndlyr),1)) - 1
for iter in range(1000000):
    # forward propagation
    l0 = X
    l1 = nonlin(np.dot(l0,syn0))
    l2 = nonlin(np.dot(l1,syn1))
        # how much did we miss the target value?
    l2_error = y - l2

    # in what direction is the target value?
    # were we really sure? if so, don't change too much.
    l2_delta = l2_error*nonlin(l2,deriv=True)

    # how much did each l1 value contribute to the l2 error (according to the weights)?
    l1_error = l2_delta.dot(syn1.T)

    # in what direction is the target l1?
    # were we really sure? if so, don't change too much.
    l1_delta = l1_error * nonlin(l1,deriv=True)
    
    syn1 += l1.T.dot(l2_delta)
    syn0 += l0.T.dot(l1_delta)

#    # how much did we miss?
#    l1_error = y - l1
#
#    # multiply how much we missed by the 
#    # slope of the sigmoid at the values in l1
#    l1_delta = l1_error * nonlin(l1,True)
#
#    # update weights
#    syn0 += np.dot(l0.T,l1_delta)


#print(syn0)
#print(syn1)
#print(l2)
for boop in range(15):
 #   print(boop)
    print((l2[boop+1]*15)-(l2[boop]*15))
#print(f'{l1:.20f}')
#print(f'{l1:.2f}')
#print('{:.20f}%'.format(l1))
#list(map('{:.2f}%'.format,l1))
