#!/usr/bin/env python
# vim: set ts=4 sw=4 expandtab :

# Copyright 2013 Mathew Odden <locke105@gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import argparse
import os
import pprint
import time

from mclib import mc_info

clear = lambda: os.system('cls' if os.name == 'nt' else 'clear')


class Opts(object):
    # container for args
    pass

opts = Opts()


def parse_args():
    p = argparse.ArgumentParser(
        description='Scrape info from a Minecraft server')
    p.add_argument('server', help='hostname or IP address of server to scrap')
    p.add_argument('-p', '--port', type=int, default=25565,
                   metavar='port', dest='port',
                   help=('TCPIP port server is listening on'
                         ' - defaults to 25565'))
    p.add_argument('-n', '--interval', type=int, default=15,
                   metavar='interval', dest='interval',
                   help='interval in seconds between scrapes')
    p.parse_args(namespace=opts)


def main():
    while True:
        info = mc_info.get_info(host=opts.server,
                                port=opts.port)
        clear()
        pprint.pprint(info)
        time.sleep(2)

if __name__ == '__main__':
    parse_args()
    main()
