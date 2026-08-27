#!/Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7

import numpy
import sys

#22 2.4666 .99 a 2
# arg1  numpy.random.seed(int(arg1))
# arg2  syn0 = z*numpy.random.random((2,2)) - zz
# arg3  nine=float(arg3)
# arg4  f = open(arg4+"l2", "a")
# arg5  syn1 = y*numpy.random.random((2,1)) - yy
# arg6  tenn=float(arg6)

# arg1 arg1
# arg2 arg2
# arg3 arg5
# arg4 arg3
# arg5 arg6
# arg6 arg4

# seednumber, syn0 range, syn1 range, lower bound of true, upper bound of true, filename to write to

arg1 = sys.argv[1]
arg2 = sys.argv[2]
arg5 = sys.argv[3]
arg3 = sys.argv[4]
arg6 = sys.argv[5]
arg4 = sys.argv[6]

def elu(x, alpha=1):
    return numpy.where(x < 0, alpha * (numpy.exp(x) - 1), x)

def witch_of_agnesi(x):
    return numpy.where(x < 0, 0.125/((x**2)+.25), 1-(0.125/((x**2)+.25)))

def sigmoid(x):
    return 1/(1+numpy.exp(-x))

def tanh(x):
    return numpy.tanh(x)

def lin(x):
    return x

z=float(arg2)
zz=float(arg2)/2.0
y=float(arg5)
yy=float(arg5)/2.0
nine=float(arg3)
tenn=float(arg6)
one=1.0-float(arg3)

X = numpy.array([[0,0],[0,1],[1,0],[1,1]])
numpy.random.seed(int(arg1))

for k in range(30000000000):
# randomly initialize our weights with mean 0
 syn0 = z*numpy.random.random((2,2)) - zz
 syn1 = y*numpy.random.random((2,1)) - yy

# Feed forward through layers 0, 1, and 2
 l0 = X
 l1 = witch_of_agnesi(numpy.dot(l0,syn0))
 l2 = witch_of_agnesi(numpy.dot(l1,syn1))

#print(l2.T)
 if (l2[0]<=one) and (l2[1]>=nine) and (l2[2]>=nine) and (l2[3]<=one):
#if (l2[0]<=one) and (l2[1]>=nine) and (l2[1]<=tenn) and (l2[2]>=nine) and (l2[2]<=tenn) and (l2[3]<=one):
#if (l2[0]<=-0.5) and (l2[1]>=0.5)  and (l2[2]>=0.5) and (l2[3]<=-0.5):
#if (l2[1]>=0.999)  and (l2[2]>=0.999) and (l2[3]<=-0.999):

  f = open(arg4+"l2", "a")
  g = open(arg4+"syn0", "a")
  h = open(arg4+"syn1", "a")
  print(l2.T, file=f)
  print(syn0, file=g)
  print(syn1.T, file=h)
  f.close()
  g.close()
  h.close()
  print(l2.T)
#  print(syn0)
#  print(syn1)
#  print()
