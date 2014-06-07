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

# parts of this were re-used from
# https://gist.github.com/barneygale/1209061

import logging
import socket
from struct import pack
import traceback

logging.basicConfig()
LOG = logging.getLogger(__name__)


def get_info(host='localhost', port=25565):
    trial_and_error = ['MC16', 'MC15']

    for version in trial_and_error:
        klass = globals()[version]
        obj = klass()
        try:
            return obj.get_info(host, port)
        except Exception:
            LOG.warn("Failed to get_info with version %s" % version)
            LOG.info(traceback.format_exc())

    raise Exception("Couldn't get_info!")


class MC16(object):
    # Strings in the minecraft protocol are encoded as big-endian UCS-2,
    # prefixed with a short giving its length in characters.
    @staticmethod
    def pack_string(string):
        return pack('>h', len(string)) + string.encode('utf-16be')

    def get_info(self, host='localhost', port=25565):
        # Set up our socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10) # seconds
        s.connect((host, port))

        # Send 0xFE: Server list ping
        s.send('\xfe\x01')

        # Send 0xFA: Plugin message
        s.send('\xfa')                           # ident
        s.send(self.pack_string('MC|PingHost'))  # message identifier
        s.send(pack('>h', 7 + 2*len(host)))      # payload length
        s.send(pack('b', 78))                    # protocol version
        s.send(self.pack_string(host))           # hostname
        s.send(pack('>i', port))                 # port

        # Done sending! Read some data and close the socket
        d = s.recv(1024)

        # consume extra bytes to avoid server end of stream error
        s.recv(1024)
        s.close()

        # Check we've got a 0xFF Disconnect
        assert d[0] == '\xff'

        # Remove the packet ident (0xFF) and the
        # short containing the length of the string
        # Decode UCS-2 string
        d = d[3:].decode('utf-16be')

        # Check the first 3 characters of the string are what we expect
        assert d[:3] == u'\xa7\x31\x00'

        # Split
        d = d[3:].split('\x00')

        # Return a dict of values
        return {'protocol_version': int(d[0]),
                'server_version':       d[1],
                'motd':                 d[2],
                'players':          int(d[3]),
                'max_players':      int(d[4])}


class MC15(object):
    def get_info(self, host='localhost', port=25565):
        # Set up our socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))

        # Send 0xFE: Server list ping
        s.send('\xfe\x01')

        # Read some data
        d = s.recv(1024)
        s.close()

        # Check we've got a 0xFF Disconnect
        assert d[0] == '\xff'

        # Remove the packet ident (0xFF) and the
        # short containing the length of the string
        # Decode UCS-2 string
        d = d[3:].decode('utf-16be')

        # Check the first 3 characters of the string are what we expect
        assert d[:3] == u'\xa7\x31\x00'

        # Split
        d = d[3:].split('\x00')

        # Return a dict of values
        return {'protocol_version': int(d[0]),
                'server_version':       d[1],
                'motd':                 d[2],
                'players':          int(d[3]),
                'max_players':      int(d[4])}
