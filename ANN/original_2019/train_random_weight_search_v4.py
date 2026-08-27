#!/Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7

import numpy
import sys

arg1 = sys.argv[1]
arg2 = sys.argv[2]
arg3 = sys.argv[3]

def nonlin(x,deriv=False):
	if(deriv==True):
		return x*(1-x)

	return 1/(1+numpy.exp(-x))
z=int(arg2)
zz=int(arg2/2)
n=arg3
o=1-arg3
X = numpy.array([[0,0],[0,1],[1,0],[1,1]]) 
#y = numpy.array([[1],[0],[0],[0]])
numpy.random.seed(int(arg1))
for k in range(30000000000):
# randomly initialize our weights with mean 0
 syn0 = z*numpy.random.random((2,2)) - zz
 syn1 = z*numpy.random.random((2,1)) - zz
# Feed forward through layers 0, 1, and 2
 l0 = X
 l1 = nonlin(numpy.dot(l0,syn0))
 l2 = nonlin(numpy.dot(l1,syn1))

 if (l2[0]<=o) and (l2[1]>=n) and (l2[2]>=n) and (l2[3]<=o):
  print(l2.T)
  print(syn0)
  print(syn1.T)
