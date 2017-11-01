import statistics
import subprocess

import sys


def run_wrk(host):
    result = subprocess.run(["wrk", "-d3s", host], stdout=subprocess.PIPE)

    if result.returncode != 0:
        raise Exception("Error: Wrk exited with non zero code :/")

    result = result.stdout.decode(sys.stdout.encoding)
    lines = result.split('\n')
    for line in lines:
        print(line)
        # line = line.decode('utf-8')
        if line.startswith('Requests/sec:'):
            rps = float(line.split()[-1])
            return rps

    raise Exception("Error: couldn't find amount of requests/sec in wrk response")


def run_framework(framework_path):
    result = subprocess.run(["wrk", "-d3s", host], stdout=subprocess.PIPE)

    if result.returncode != 0:
        raise Exception("Error: Wrk exited with non zero code :/")


def print_framework_results(framework, results):
    print("Framework: {}".format(framework['name']))
    print("Running on: {} server".format(framework['server']))
    median = statistics.median_grouped(results)
    stdev = round(statistics.stdev(results), 2)
    p = round((stdev / median) * 100, 2)
    print('median:', median, 'stdev:', stdev, '%', p)


if __name__ == '__main__':

    host = 'http://localhost:8080'
    framework_path = 'frameworks/weppy_test/app.py'
    frameworks = [
        {'name': 'Django', 'server': 'own', 'command': 'python manage.py runserver'}
    ]
    for framework in frameworks:
        framework_path = framework.pop('command')
        run_framework(framework_path)
        results = []
        for i in range(10):
            results.append(run_wrk(host))

        print_framework_results(framework, results)



