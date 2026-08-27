#!/Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7

import numpy
import sys

firstarg = sys.argv[1]

def nonlin(x, deriv=False):
    if deriv is True:
        return x * (1 - x)

    return 1 / (1 + numpy.exp(-x))


X = numpy.array([[0, 0], [0, 1], [1, 0], [1, 1]])

n = 0.98274
o = 1.0 - n
numpy.random.seed(int(firstarg))

syn0 = numpy.zeros((2, 3))
syn1 = numpy.zeros((3, 1))

for k in range(30000000000):

    syn0[0, 0] = numpy.random.sample() * (6.1 - 4.5) + 4.5
    syn0[0, 1] = numpy.random.sample() * (-4.9 + 6.0) - 6.0
    syn0[0, 2] = numpy.random.sample() * (-4.9 + 6.0) - 6.0
    syn0[1, 0] = numpy.random.sample() * (6.1 - 4.5) + 4.5
    syn0[1, 1] = numpy.random.sample() * (-4.9 + 6.0) - 6.0
    syn0[1, 2] = numpy.random.sample() * (-4.9 + 6.0) - 6.0
    # print(syn0)

    syn1[0, 0] = numpy.random.sample() * (-3.9 + 4.1) - 4.1
    syn1[1, 0] = numpy.random.sample() * (6.1 - 5.9) + 5.9
    syn1[2, 0] = numpy.random.sample() * (6.1 - 5.9) + 5.9
    # print(syn1)
#    syn1[0, 0] = -4.09965575
#    syn1[1, 0] = 6.085
#    syn1[2, 0] = 6.085

    l0 = X
    l1 = nonlin(numpy.dot(l0, syn0))
    l2 = nonlin(numpy.dot(l1, syn1))

    if (l2[0] >= n) and (l2[1] <= o) and (l2[2] <= o) and (l2[3] <= o):
#        f = open("R9NAND__l2ziz", "a")
#        g = open("R9NAND__syn0ziz", "a")
#        h = open("R9NAND__syn1ziz", "a")
#        print(l2.T, file=f)
#        print(syn0, file=g)
#        print(syn1.T, file=h)
#        f.close()
#        g.close()
#        h.close()
        print(l2.T)
        print(syn0)
        print(syn1.T)
        print()
