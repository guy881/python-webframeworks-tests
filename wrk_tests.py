import atexit
import json
import re
import select
import statistics
import subprocess
import sys
from time import sleep
import asyncio
from asyncio.subprocess import PIPE, STDOUT


import psutil
import uvloop

test_duration = 3  # seconds
frameworks_processes = set()


def run_wrk(host):
    # wrk = subprocess.run(["wrk", "-d{}s".format(test_duration), host], stdout=subprocess.PIPE)
    max_iters = 1000
    for i in range(max_iters):
        wrk_fut = asyncio.create_subprocess_exec("wrk", "-d{}s".format(test_duration), host, stdout=PIPE, stderr=STDOUT)
        wrk = loop.run_until_complete(wrk_fut)

        returncode = loop.run_until_complete(wrk.wait())
        if returncode != 0:
            if i == max_iters - 1:
                raise Exception("Error: Wrk exited with non zero code :/")
            continue
        else:
            break

    while True:
        line = loop.run_until_complete(wrk.stdout.readline())
        line = line.decode(sys.stdout.encoding)
        match = re.search(r'Requests/sec:\s*(\d+\.\d+)', line)
        if match:
            requests_per_second = match.groups(0)[0]
            return float(requests_per_second)

    raise Exception("Error: couldn't find amount of requests/sec in wrk response")


def run_framework(framework):
    command_with_params = framework['command'].split(' ')
    # command_with_params = framework['command']
    ready_output = framework['ready_output']  # this is printed when server is ready and we can continue
    path = framework['path']
    # framework_proc = subprocess.Popen(command_with_params, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1,
    #                                   cwd=path)
    print("Running framework server, use ctrl + c if it doesn't work after a while")
    # read line without blocking

    server_fut = asyncio.create_subprocess_exec(*command_with_params, stdout=PIPE, stderr=sys.stderr, cwd=path)
    server = loop.run_until_complete(server_fut)

    # stdout_poll = select.poll()
    # stderr_poll = select.poll()
    # stdout_poll.register(framework_proc.stdout, select.POLLIN)
    # stderr_poll.register(framework_proc.stderr, select.POLLIN)
    success_message = "Successfully launched {}".format(framework['name'])

    while True:  # wait until framework runs
        line = loop.run_until_complete(server.stdout.readline())
        # stdout_ready = stdout_poll.poll(1)
        # stderr_ready = stderr_poll.poll(1)
        # if stdout_ready:
        #     for line in iter(framework_proc.stdout.readline, b''):
        #         if ready_output in line.decode():
        #             print(success_message)
        #             return framework_proc
        # if stderr_ready:
        #     for line in iter(framework_proc.stderr.readline, b''):
        #         if ready_output in line.decode():
        #             print(success_message)
        #             return framework_proc
        if line:
            if ready_output in line.decode():
                print(success_message)
                return server
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


def cleanup():
    for p in frameworks_processes:
        print("Killing open process")
        kill(p)


if __name__ == '__main__':
    atexit.register(cleanup)  # cleanup after exit
    host = 'http://localhost:8080'
    test_iterations = 2
    frameworks_data = open('frameworks.json').read()
    frameworks = json.loads(frameworks_data)

    for framework in frameworks:
        loop = uvloop.new_event_loop()
        asyncio.set_event_loop(loop)
        print_framework_details(framework)
        proc = run_framework(framework)
        psutil_proc = psutil.Process(proc.pid)
        frameworks_processes.add(psutil_proc)
        results = []

        tests = framework['tests']
        for test in tests:
            for i in range(test_iterations):
                result = run_wrk(host)
                results.append(result)

            print_test_results(test, results)

        kill(proc)  # using psutil, as gunicorn open also child proccesses
        frameworks_processes.remove(psutil_proc)
        sleep(1)
