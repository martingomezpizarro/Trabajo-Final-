import os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'processed', 'test.txt')
with open(p, 'w') as f:
    f.write('python works')
