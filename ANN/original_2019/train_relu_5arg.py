#!/Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7

import numpy
import sys

arg1 = sys.argv[1]
arg2 = sys.argv[2]
arg3 = sys.argv[3]
arg4 = sys.argv[4]
arg5 = sys.argv[5]

def nonlin(x,deriv=False):
	if(deriv==True):
		return x*(1-x)

#	return 1/(1+numpy.exp(-x))
	return x * (x > 0)

z=float(arg2)
zz=float(arg2)/2.0
y=float(arg5)
yy=float(arg5)/2.0
nine=float(arg3)
one=1.0-float(arg3)
X = numpy.array([[0,0],[0,1],[1,0],[1,1]]) 
#y = numpy.array([[1],[0],[0],[0]])
numpy.random.seed(int(arg1))
for k in range(30000000000):
# randomly initialize our weights with mean 0
 syn0 = z*numpy.random.random((2,2)) - zz
 syn1 = y*numpy.random.random((2,1)) - yy
# Feed forward through layers 0, 1, and 2
 l0 = X
 l1 = nonlin(numpy.dot(l0,syn0))
 l2 = nonlin(numpy.dot(l1,syn1))

 if (l2[0]<=one) and (l2[1]>=nine) and (l2[2]>=nine) and (l2[3]<=one):

  f = open(arg4+"l2", "a")
  g = open(arg4+"syn0", "a")
  h = open(arg4+"syn1", "a")
  print(l2.T, file=f)
  print(syn0, file=g)
  print(syn1.T, file=h)
  f.close()
  g.close()
  h.close()
#  print(l2.T)
#  print(syn0)
#  print(syn1)
#  print()
