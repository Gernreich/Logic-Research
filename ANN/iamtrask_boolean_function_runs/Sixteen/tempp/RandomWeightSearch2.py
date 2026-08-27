#!/Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7

import numpy as np

def nonlin(x,deriv=False):
	if(deriv==True):
		return x*(1-x)

	return 1/(1+np.exp(-x))

X = np.array([[0,0],[0,1],[1,0],[1,1]]) 
y = np.array([[1],[0],[0],[0]])
#f = open("R9NOR_l2", "a")
#g = open("R9NOR_syn0", "a")
#h = open("R9NOR_syn1", "a")
for k in range(4294967295):
 np.random.seed(4294967295-k)
 #f = open("R9NOR_l2", "a")
 #g = open("R9NOR_syn0", "a")
 #h = open("R9NOR_syn1", "a")
# randomly initialize our weights with mean 0
 syn0 = 20*np.random.random((2,3)) - 10
 syn1 = 20*np.random.random((3,1)) - 10

# for j in range(3000000):

	# Feed forward through layers 0, 1, and 2
 l0 = X
 l1 = nonlin(np.dot(l0,syn0))
 l2 = nonlin(np.dot(l1,syn1))

# if (l2[0] >= 0.9) and (l2[1] <= 0.1) and (l2[2] <= 0.1) and (l2[3] <= 0.1):
#  f = open("R9NOR__l2", "a")
#  g = open("R9NOR__syn0", "a")
#  h = open("R9NOR__syn1", "a")   
#  print(l2.T, file=f)
#  print(syn0, file=g)
#  print(syn1.T, file=h)
#  f.close() 
#  g.close()
#  h.close()

# if (l2[0] >= 0.9) and (l2[1] >= 0.9) and (l2[2] >= 0.9) and (l2[3] <= 0.1):
#  f = open("R9NAND__l2b", "a")
#  g = open("R9NAND__syn0b", "a")
#  h = open("R9NAND__syn1b", "a")   
#  print(l2.T, file=f)
#  print(syn0, file=g)
#  print(syn1.T, file=h)
#  f.close() 
#  g.close()
#  h.close()

# if (l2[0] >= 0.9) and (l2[1] <= 0.1) and (l2[2] >= 0.9) and (l2[3] >= 0.9):
#  f = open("R9IMPLICATION__l2", "a")
#  g = open("R9IMPLICATION__syn0", "a")
#  h = open("R9IMPLICATION__syn1", "a")   
#  print(l2.T, file=f)
#  print(syn0, file=g)
#  print(syn1.T, file=h)
#  f.close() 
#  g.close()
#  h.close()

 if (l2[0] <= 0.1) and (l2[1] >= 0.9) and (l2[2] >= 0.9) and (l2[3] <= 0.1):
  f = open("R9XOR__l2b", "a")
  g = open("R9XOR__syn0b", "a")
  h = open("R9XOR__syn1b", "a")   
  print(l2.T, file=f)
  print(syn0, file=g)
  print(syn1.T, file=h)
  f.close() 
  g.close()
  h.close()

 if (l2[0] >= 0.9) and (l2[1] <= 0.1) and (l2[2] <= 0.1) and (l2[3] >= 0.9):
  f = open("R9IFF__l2b", "a")
  g = open("R9IFF__syn0b", "a")
  h = open("R9IFF__syn1b", "a")   
  print(l2.T, file=f)
  print(syn0, file=g)
  print(syn1.T, file=h)
  f.close() 
  g.close()
  h.close()

# if (l2[0] <= 0.1) and (l2[1] <= 0.1) and (l2[2] >= 0.9) and (l2[3] <= 0.1):
#  f = open("R9PminusQ__l2", "a")
#  g = open("R9PminusQ__syn0", "a")
#  h = open("R9PminusQ__syn1", "a")   
#  print(l2.T, file=f)
#  print(syn0, file=g)
#  print(syn1.T, file=h)
#  f.close() 
#  g.close()
#  h.close()

















    # how much did we miss the target value?
#  l2_error = y - l2
    
    # in what direction is the target value?
    # were we really sure? if so, don't change too much.
#  l2_delta = l2_error*nonlin(l2,deriv=True)

    # how much did each l1 value contribute to the l2 error (according to the weights)?
#  l1_error = l2_delta.dot(syn1.T)
    
    # in what direction is the target l1?
    # were we really sure? if so, don't change too much.
#  l1_delta = l1_error * nonlin(l1,deriv=True)

#  syn1 += l1.T.dot(l2_delta)
#  syn0 += l0.T.dot(l1_delta)
 
# f = open("NOR_l2", "a")
# g = open("NOR_syn0", "a")
# h = open("NOR_syn1", "a")

# print(l2.T, file=f)
# print(syn0, file=g)
# print(syn1.T, file=h)
# f.close()
# g.close()
# h.close()
