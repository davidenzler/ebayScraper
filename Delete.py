import random

size = 100
mm_bag = []
face_up = 100

for i in range(size):
    mm_bag.append(1)
    face_up = mm_bag.count(1)

while face_up > 0:
    iterations = 1
    new_bag = []
    for i in range(size):
        new_bag.append(random.randint(0, 1))
        face_up = new_bag.count(1)
    print("{} : remaining {}".format(iterations, face_up))
    size = face_up
    iterations = iterations + 1

