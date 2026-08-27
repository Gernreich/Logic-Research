#!/usr/bin/python

firstthree = [2,4,5,7,8,10,11,13]
#for p in range (16):
#  for q in range (16):
#    firstthree.append(0)
#    firstthree.append(15^((q^15)|p))
#    firstthree.append(p&q)
#    firstthree.append(q)
#    firstthree.append(15^((p^15)|q))
#    firstthree.append(p^q)
#    firstthree.append(p)
#    firstthree.append(p|q)
#    firstthree.append(15^(p|q))
#    firstthree.append(p^15)
#    firstthree.append(15^(p^q))
#    firstthree.append((p^15)|q)
#    firstthree.append(q^15)
#    firstthree.append(15^(p&q))
#    firstthree.append((q^15)|p)
#    firstthree.append(15)
print len(firstthree)
firstfive = []
for p in firstthree:
  for q in [3,6,9,12]:
#    firstfive.append(0)
#    firstfive.append(15^((q^15)|p))
    firstfive.append(p&q)
#    firstfive.append(q)
    firstfive.append(15^((p^15)|q))
    firstfive.append(p^q)
#    firstfive.append(p)
    firstfive.append(p|q)
    firstfive.append(15^(p|q))
#    firstfive.append(p^15)
    firstfive.append(15^(p^q))
    firstfive.append((p^15)|q)
#    firstfive.append(q^15)
    firstfive.append(15^(p&q))
#    firstfive.append((q^15)|p)
#    firstfive.append(15)
print len(firstfive)
firstseven = []
for p in firstfive:
  for q in [3,6,9,12]:
#    firstseven.append(0)
#    firstseven.append(15^((q^15)|p))
    firstseven.append(p&q)
#    firstseven.append(q)
    firstseven.append(15^((p^15)|q))
    firstseven.append(p^q)
#    firstseven.append(p)
    firstseven.append(p|q)
    firstseven.append(15^(p|q))
#    firstseven.append(p^15)
    firstseven.append(15^(p^q))
    firstseven.append((p^15)|q)
#    firstseven.append(q^15)
    firstseven.append(15^(p&q))
#    firstseven.append((q^15)|p)
#    firstseven.append(16)
print len(firstseven)
with open('FirstSeven', 'w') as f:
    for s in firstseven:
        f.write(str(s) + '\n')

#with open('Tau', 'w') as f:
#  for i in range (268435457):
#    if firstseven[i] == 15:
#      f.write(oct(i) + '\n')
