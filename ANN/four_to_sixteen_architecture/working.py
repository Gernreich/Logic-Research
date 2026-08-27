#!/Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7

import numpy

def nonlin(x,deriv=False):
	if(deriv==True):
		return x*(1-x)

	return 1/(1+numpy.exp(-x))

X = numpy.array([[0,0,0,0],[0,0,0,1],[0,0,1,0],[0,0,1,1],[0,1,0,0],[0,1,0,1],[0,1,1,0],[0,1,1,1],[1,0,0,0],[1,0,0,1],[1,0,1,0],[1,0,1,1],[1,1,0,0],[1,1,0,1],[1,1,1,0],[1,1,1,1]])
y = numpy.array([[0],[1],[2],[3],[4],[5],[6],[7],[8],[9],[10],[11],[12],[13],[14],[15]])

syn0 = numpy.zeros((16, 1))

numpy.random.seed(1)

# randomly initialize our weights with mean 0
 syn0 = 2*numpy.random.random((3,1)) - 1


for iter in xrange(10000):

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

print "Output After Training:"
print l1




# for j in range(10000):
#
#        # Feed forward through layers 0, 1, and 2
#  l0 = X
#  l1 = nonlin(numpy.dot(l0,syn0))
#
#    # how much did we miss the target value?
#  l1_error = y - l2
#
#    # in what direction is the target value?
#    # were we really sure? if so, don't change too much.
#  l1_delta = l1_error*nonlin(l1,deriv=True)
#
#  syn0 += l0.T.dot(l1_delta)
#
### print(syn0.T)
