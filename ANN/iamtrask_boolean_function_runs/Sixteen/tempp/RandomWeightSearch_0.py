#!/Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7

import numpy

def nonlin(x,deriv=False):
	if(deriv==True):
		return x*(1-x)

	return 1/(1+numpy.exp(-x))
z=2.6
zz=1.3
n=0.9
o=0.1
X = numpy.array([[0,0],[0,1],[1,0],[1,1]]) 
#y = numpy.array([[1],[0],[0],[0]])
numpy.random.seed(0)
for k in range(30000000000):
# randomly initialize our weights with mean 0
 syn0 = z*numpy.random.random((2,3)) - zz
 syn1 = z*numpy.random.random((3,1)) - zz
# Feed forward through layers 0, 1, and 2
 l0 = X
 l1 = nonlin(numpy.dot(l0,syn0))
 l2 = nonlin(numpy.dot(l1,syn1))
 #print(k)

 if (l2[0]>=n) and (l2[1]>=n) and (l2[2]>=n) and (l2[3]>=n):
  f = open("R9TRUE__l2", "a")
  g = open("R9TRUE__syn0", "a")
  h = open("R9TRUE__syn1", "a")   
  print(l2.T, file=f)
  print(syn0, file=g)
  print(syn1.T, file=h)
  f.close() 
  g.close()
  h.close()

 if (l2[0]<=o) and (l2[1]<=o) and (l2[2]<=o) and (l2[3]<=o):
  f = open("R9FALSE__l2", "a")
  g = open("R9FALSE__syn0", "a")
  h = open("R9FALSE__syn1", "a")   
  print(l2.T, file=f)
  print(syn0, file=g)
  print(syn1.T, file=h)
  f.close() 
  g.close()
  h.close()

 if (l2[0]<=o) and (l2[1]<=o) and (l2[2]<=o) and (l2[3]>=n):
  f = open("R9AND__l2", "a")
  g = open("R9AND__syn0", "a")
  h = open("R9AND__syn1", "a")   
  print(l2.T, file=f)
  print(syn0, file=g)
  print(syn1.T, file=h)
  f.close() 
  g.close()
  h.close()

 if (l2[0]<=o) and (l2[1]>=n) and (l2[2]>=n) and (l2[3]>=n):
  f = open("R9OR__l2", "a")
  g = open("R9OR__syn0", "a")
  h = open("R9OR__syn1", "a")   
  print(l2.T, file=f)
  print(syn0, file=g)
  print(syn1.T, file=h)
  f.close() 
  g.close()
  h.close()

 if (l2[0]<=o) and (l2[1]<=o) and (l2[2]>=n) and (l2[3]>=n):
  f = open("R9P__l2", "a")
  g = open("R9P__syn0", "a")
  h = open("R9P__syn1", "a")   
  print(l2.T, file=f)
  print(syn0, file=g)
  print(syn1.T, file=h)
  f.close() 
  g.close()
  h.close()

 if (l2[0]<=o) and (l2[1]>=n) and (l2[2]<=o) and (l2[3]>=n):
  f = open("R9Q__l2", "a")
  g = open("R9Q__syn0", "a")
  h = open("R9Q__syn1", "a")   
  print(l2.T, file=f)
  print(syn0, file=g)
  print(syn1.T, file=h)
  f.close() 
  g.close()
  h.close()

 if (l2[0]>=n) and (l2[1]>=n) and (l2[2]<=o) and (l2[3]<=o):
  f = open("R9NOTP__l2", "a")
  g = open("R9NOTP__syn0", "a")
  h = open("R9NOTP__syn1", "a")   
  print(l2.T, file=f)
  print(syn0, file=g)
  print(syn1.T, file=h)
  f.close() 
  g.close()
  h.close()

 if (l2[0]>=n) and (l2[1]<=o) and (l2[2]>=n) and (l2[3]<=o):
  f = open("R9NOTQ__l2", "a")
  g = open("R9NOTQ__syn0", "a")
  h = open("R9NOTQ__syn1", "a")   
  print(l2.T, file=f)
  print(syn0, file=g)
  print(syn1.T, file=h)
  f.close() 
  g.close()
  h.close()

 if (l2[0]<=o) and (l2[1]>=n) and (l2[2]<=o) and (l2[3]<=o):
  f = open("R9QminusP__l2", "a")
  g = open("R9QminusP__syn0", "a")
  h = open("R9QminusP__syn1", "a")
  print(l2.T, file=f)
  print(syn0, file=g)
  print(syn1.T, file=h)
  f.close()
  g.close()
  h.close()

 if (l2[0]>=n) and (l2[1]>=n) and (l2[2]<=o) and (l2[3]>=n):
  f = open("R9REVIMPLICATION__l2", "a")
  g = open("R9REVIMPLICATION__syn0", "a")
  h = open("R9REVIMPLICATION__syn1", "a")
  print(l2.T, file=f)
  print(syn0, file=g)
  print(syn1.T, file=h)
  f.close()
  g.close()
  h.close()
