#!/usr/bin/python
position = [1,2,3,4,5]
with open('Tau', 'w') as f:
    for s in position:
        f.write(str(s) + '\n')
