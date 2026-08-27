#!/Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7

import numpy
import sys

# arg1  numpy.random.seed(int(arg1))
# arg2  syn0 = z*numpy.random.random((2,2)) - zz
# arg3  nine=float(arg3)
# arg4  f = open(arg4+"l2", "a")
# arg5  syn1 = v*numpy.random.random((2,1)) - vv
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

def derivrelu(x):
    return numpy.where(x < 0, 0, 1)

def relu(x):
    return numpy.where(x < 0, 0, x)

def elu(x, alpha=1):
    return numpy.where(x < 0, (alpha * ((numpy.exp(x)) - 1)), x)

def derivelu(x, alpha=1):
    return numpy.where(x < 0, (alpha * ((numpy.exp(x)) - 1))+alpha, 1)

def witch_of_agnesi(x):
    return numpy.where(x < 0, 0.125/((x**2)+.25), 1-(0.125/((x**2)+.25)))

def sigmoid(x):
    return 1/(1+numpy.exp(-x))

def derivsigmoid(x):
    return (1/(1+numpy.exp(-x)))*(1-(1/(1+numpy.exp(-x))))

def tanh(x):
    return numpy.tanh(x)

def derivtanh(x):
    return 1-((numpy.tanh(x))**2)

def lin(x):
    return x

z=float(arg2)
zz=float(arg2)/2.0
v=float(arg5)
vv=float(arg5)/2.0
nine=float(arg3)
tenn=float(arg6)
one=1.0-float(arg3)

numpy.random.seed(int(arg1))

X = numpy.array([[0,0],[0,1],[1,0],[1,1]]) 
y = numpy.array([[0],[1],[1],[0]])

for k in range(30000000000):
# randomly initialize our weights with mean 0
 syn0 = z*numpy.random.random((2,2)) - zz
 syn1 = v*numpy.random.random((2,1)) - vv
# print(syn0)
# print(syn1)

# Feed forward through layers 0, 1, and 2
 l0 = X
 l1 = relu(numpy.dot(l0,syn0))
 l2 = relu(numpy.dot(l1,syn1))

# print(l2.T)
# print(syn0.T)
# print(syn1)
# print()
 if (l2[0]<=one) and (l2[1]>=nine) and (l2[2]>=nine) and (l2[3]<=one):
#if (l2[0]<=one) and (l2[1]>=nine) and (l2[1]<=tenn) and (l2[2]>=nine) and (l2[2]<=tenn) and (l2[3]<=one):
#if (l2[0]<=-0.5) and (l2[1]>=0.5)  and (l2[2]>=0.5) and (l2[3]<=-0.5):
#if (l2[1]>=0.999)  and (l2[2]>=0.999) and (l2[3]<=-0.999):
  print(l2.T)
  for j in range(1000000):

    # how much did we miss the target value?
   l2_error = y - l2
    
    # in what direction is the target value?
    # were we really sure? if so, don't change too much.
   l2_delta = l2_error * derivrelu(l2)

    # how much did each l1 value contribute to the l2 error (according to the weights)?
   l1_error = l2_delta.dot(syn1.T)
    
    # in what direction is the target l1?
    # were we really sure? if so, don't change too much.
   l1_delta = l1_error * derivrelu(l1)

   syn1 += l1.T.dot(l2_delta)
   syn0 += l0.T.dot(l1_delta)

        # Feed forward through layers 0, 1, and 2
   l0 = X
   l1 = relu(numpy.dot(l0,syn0))
   l2 = relu(numpy.dot(l1,syn1))   
 
  print(l2.T)
  print(syn0.T)
  print(syn1)
