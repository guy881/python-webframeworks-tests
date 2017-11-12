import argparse
import sys
import asyncio as aio
import os
from asyncio.subprocess import PIPE, STDOUT
import statistics

import uvloop
import psutil

from misc import cpu


def run_wrk(loop, host='http://localhost:8080'):
    print("host", host)
    wrk_fut = aio.create_subprocess_exec('wrk', '-d10s', host, stdout=PIPE, stderr=STDOUT)
    print(wrk_fut)

    wrk = loop.run_until_complete(wrk_fut)

    lines = []
    while 1:
        line = loop.run_until_complete(wrk.stdout.readline())
        if line:
            line = line.decode('utf-8')
            lines.append(line)
            if line.startswith('Requests/sec:'):
                rps = float(line.split()[-1])
                print(rps)
                return rps
        else:
            break

    retcode = loop.run_until_complete(wrk.wait())
    if retcode != 0:
        print('\r\n'.join(lines))
        raise Exception("Error: Wrk exited with non zero code :/")


def cpu_usage(p):
    return p.cpu_percent() + sum(c.cpu_percent() for c in p.children())


def connections(process):
    return len(
        set(c.fd for c in process.connections()) |
        set(c.fd for p in process.children() for c in p.connections()))


def memory(p):
    return p.memory_percent('uss') \
           + sum(c.memory_percent('uss') for c in p.children())


if __name__ == '__main__':
    loop = uvloop.new_event_loop()

    argparser = argparse.ArgumentParser('do_wrk')
    argparser.add_argument('-s', dest='server', default='')
    argparser.add_argument('-e', dest='endpoint')
    argparser.add_argument('--pid', dest='pid', type=int)

    args = argparser.parse_args(sys.argv[1:])

    aio.set_event_loop(loop)

    if not args.endpoint:
        framework_path = 'frameworks/weppy_test/app.py'
        os.putenv('PYTHONPATH', 'src')
        server_fut = aio.create_subprocess_exec(
            'python', framework_path, *args.server.split())
        server = loop.run_until_complete(server_fut)
        os.unsetenv('PYTHONPATH')
    if not args.endpoint:
        process = psutil.Process(server.pid)
    elif args.pid:
        process = psutil.Process(args.pid)
    else:
        process = None

    for i in range(1):
        cpu_p = psutil.cpu_percent(interval=1)
        print('CPU usage in 1 sec:', cpu_p)

    results = []
    cpu_usages = []
    process_cpu_usages = []
    mem_usages = []
    conn_cnt = []
    if process:
        cpu_usage(process)
    for _ in range(10):
        results.append(run_wrk(loop))
        cpu_usages.append(psutil.cpu_percent())
        if process:
            process_cpu_usages.append(cpu_usage(process))
            conn_cnt.append(connections(process))
            mem_usages.append(round(memory(process), 2))
        print('.', end='')
        sys.stdout.flush()

    if not args.endpoint:
        server.terminate()
        loop.run_until_complete(server.wait())

    if args.cpu_change:
        cpu.change('ondemand')

    print()
    print('RPS', results)
    print('Mem', mem_usages)
    print('Conn', conn_cnt)
    print('Server', process_cpu_usages)
    print('System', cpu_usages)
    median = statistics.median_grouped(results)
    stdev = round(statistics.stdev(results), 2)
    p = round((stdev / median) * 100, 2)
    print('median:', median, 'stdev:', stdev, '%', p)
