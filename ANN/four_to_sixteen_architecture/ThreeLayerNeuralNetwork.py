#!/Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7

import numpy

def nonlin(x,deriv=False):
	if(deriv==True):
		return x*(1-x)

	return 1/(1+numpy.exp(-x))

X = numpy.array([[0,0],[0,1],[1,0],[1,1]]) 
y = numpy.array([[1],[1],[1],[0]])

syn0 = numpy.zeros((2, 3))
syn1 = numpy.zeros((3, 1))

#syn0[0, 0] = 6.00715026
#syn0[0, 1] = -6.00375169
#syn0[0, 2] = -5.99797357
#syn0[1, 0] = 6.00805653
#syn0[1, 1] = -6.0064955
#syn0[1, 2] = -5.99122022
#syn1[0, 0] = -4.08013521
#syn1[1, 0] = 6.08128524
#syn1[2, 0] = 6.07917662

#[[ 1. -1. -1.]
# [ 1. -1. -1.]]
#[[-1.]
# [ 1.]
# [ 1.]]

syn0[0, 0] = 0
syn0[0, 1] = 0
syn0[0, 2] = 0
syn0[1, 0] = 0
syn0[1, 1] = 0
syn0[1, 2] = 0
print(syn0)

syn1[0, 0] = .7
syn1[1, 0] = 0
syn1[2, 0] = .7
print(syn1)

#for j in range(300000000):
for j in range(30000000):

	# Feed forward through layers 0, 1, and 2
  l0 = X
  l1 = nonlin(numpy.dot(l0,syn0))
  l2 = nonlin(numpy.dot(l1,syn1))

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
 
print(l2)
print(syn0)
print(syn1)
