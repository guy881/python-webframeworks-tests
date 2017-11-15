import atexit
import json
import re
import select
import statistics
import subprocess
import sys
from time import sleep

import os
import psutil

test_duration = 3  # seconds
frameworks_processes = set()


def run_wrk(host):
    wrk = subprocess.run(["wrk", "-d{}s".format(test_duration), host], stdout=subprocess.PIPE)
    if wrk.returncode != 0:
        raise Exception("Error: Wrk exited with non zero code :/")

    result = wrk.stdout.decode(sys.stdout.encoding)
    match = re.search(r'Requests/sec:\s*(\d+\.\d+)', result)
    if match:
        requests_per_second = match.groups(0)[0]
        return float(requests_per_second)

    raise Exception("Error: couldn't find amount of requests/sec in wrk response")


def run_framework(framework):
    command_with_params = framework['command'].split(' ')
    ready_output = framework['ready_output']  # this is printed when server is ready and we can continue
    dir_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(dir_path, framework['path'])
    framework_proc = subprocess.Popen(command_with_params, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1,
                                      cwd=path)
    succes_message = "Successfully launched {}".format(framework['name'])
    print("Running framework server, use ctrl + c if it doesn't work after a while")
    # read line without blocking

    stdout_poll = select.poll()
    stdout_poll.register(framework_proc.stdout, select.POLLIN)

    while True:  # wait until framework runs
        stdout_ready = stdout_poll.poll(1)
        if stdout_ready:
            for line in iter(framework_proc.stdout.readline, b''):
                if ready_output in line.decode():
                    print(succes_message)
                    return framework_proc
        else:
            print("Waiting for framework to start")
            sleep(1)
            continue


def print_framework_details(framework):
    print("Framework: {}".format(framework['name']))
    print("Running on: {} server".format(framework['server']))


def print_test_results(test, results):
    print("\nTest: {}".format(test['name']))
    median = statistics.median_grouped(results)
    stdev = round(statistics.stdev(results), 2)
    p = round((stdev / median) * 100, 2)
    print('median:', median, 'stdev:', stdev, '%', p, '\n')


def kill(proc):
    process = psutil.Process(proc.pid)
    for child_proc in process.children(recursive=True):
        child_proc.kill()
    process.kill()
    frameworks_processes.remove(proc)


def cleanup():
    for p in frameworks_processes:
        if p.poll():
            print("Killing open process")
            kill(p)


if __name__ == '__main__':
    atexit.register(cleanup)  # cleanup after exit
    host = 'http://localhost:8080'
    test_iterations = 2
    frameworks_data = open('frameworks.json').read()
    frameworks = json.loads(frameworks_data)

    for framework in frameworks:
        print_framework_details(framework)
        proc = run_framework(framework)
        frameworks_processes.add(proc)
        results = []

        tests = framework['tests']
        for test in tests:
            for i in range(test_iterations):
                result = run_wrk(host)
                results.append(result)

            print_test_results(test, results)

        kill(proc)  # using psutil, as gunicorn open also child proccesses
        sleep(1)
