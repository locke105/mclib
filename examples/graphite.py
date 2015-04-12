#!/usr/bin/python

import sys
import time
import socket

from mclib import mc_info

# replace with your graphite/carbon server info
CARBON_SERVER = '127.0.0.1'
CARBON_PORT = 2003
DELAY = 60

# replace with your MC server info
mc_server = {'host': 'minecraft.example.com',
             'port': 25565}

mc_server['reverse_host'] = '.'.join(mc_server['host'].split('.')[::-1])


def get_metric():
    info = mc_info.get_info(host=mc_server['host'],
                            port=mc_server['port'])
    curr_players = info['players']['online']
    metric_name_fmt = 'minecraft.%(reverse_host)s.%(port)s.players.count'

    return (metric_name_fmt % mc_server, curr_players)


def run(sock, delay):
    while True:
        now = int(time.time())
        message = "%s %s %d\n" % (get_metric() + (now,))
        sock.sendall(message)
        time.sleep(delay)

def main():
    delay = DELAY
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.isdigit():
            delay = int(arg)
        else:
            sys.stderr.write("Ignoring non-integer argument. Using default: %ss\n" % delay)

    sock = socket.socket()
    try:
        sock.connect( (CARBON_SERVER, CARBON_PORT) )
    except socket.error:
        raise SystemExit("Couldn't connect to %(server)s on port %(port)d, is carbon-cache.py running?" % { 'server':CARBON_SERVER, 'port':CARBON_PORT })

    try:
        run(sock, delay)
    except KeyboardInterrupt:
        sys.stderr.write("\nExiting on CTRL-c\n")
        return 0

if __name__ == "__main__":
    sys.exit(main())
