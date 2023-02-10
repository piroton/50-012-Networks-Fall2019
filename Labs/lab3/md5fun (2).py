import hashlib
import string
import os
import random
import time
from multiprocessing import Process, Queue, cpu_count, get_context

# for password in passwords:
#   hash_pass = hashlib.md5(password.encode("UTF-8")).hexdigest()
#   if hash_pass in hashes:
#     brute_md[hash_pass] = password

cwd = os.getcwd()
with open(cwd + "/hash5.txt", "r") as hash5_file:
    hashes = hash5_file.readlines()
    hashes = [i.strip() for i in hashes]
num_hashes = len(hashes)
print("number of hashes", num_hashes)


def brute_force(q, starts=[0, 0, 0, 0, 0], ends=[36, 36, 36, 36, 36]):
    buffer = {}
    cwd = os.getcwd()
    with open(cwd + "/hash5.txt", "r") as hash5_file:
        hashes = hash5_file.readlines()
        hashes = [i.strip() for i in hashes]

    printable = [i for i in string.printable[:36]]

    for first in range(starts[0], ends[0]):
        for second in range(starts[1], ends[1]):
            for third in range(starts[2], ends[2]):
                for fourth in range(starts[3], ends[3]):
                    for fifth in range(starts[4], ends[4]):
                        test_string = printable[first] + printable[second] + \
                            printable[third] + \
                            printable[fourth] + printable[fifth]
                        hash_pass = hashlib.md5(
                            test_string.encode("UTF-8")).hexdigest()
                        if hash_pass in hashes:
                            q.put((hash_pass, test_string))


results = []

cpu_count = 9  # did not use cpu_count()=8 since 36/9=4 just nice
print("Using", cpu_count, "threads")

threads = []
queues = []

start_time = time.time()
print("Started at", start_time)

q = Queue()

for i in range(cpu_count):
    start, end = 4*i, 4*(i+1)
    print("From", start, "to", end)
    p = Process(target=brute_force, args=(q,
                                          [start, 0, 0, 0, 0],
                                          [end, 36, 36, 36, 36]))
    p.start()
    threads.append(p)

for p in threads:
    p.join()

end_time = time.time()
print("Ended at", end_time)

for i in range(num_hashes):
    results.append(q.get())

print("Time taken:", int(end_time-start_time), "seconds")

print(results)
