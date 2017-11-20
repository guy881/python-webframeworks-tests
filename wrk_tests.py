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
framework_run_timeout = 3
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
    path = os.path.join(framework['path'])
    framework_proc = subprocess.Popen(command_with_params, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1,
                                      cwd=path)
    print("Waiting for framework to start")
    sleep(framework_run_timeout)
    print("Successfully launched {}".format(framework['name']))
    return framework_proc


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
    host = 'http://localhost'
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
                host_and_port = "{}:{}".format(host, framework['port'])
                result = run_wrk(host_and_port)
                results.append(result)

            print_test_results(test, results)

        kill(proc)  # using psutil, as gunicorn open also child proccesses
        sleep(1)
