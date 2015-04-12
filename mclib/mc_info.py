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

from cStringIO import StringIO
import json
import logging
import socket
import struct
import traceback

logging.basicConfig()
LOG = logging.getLogger(__name__)


def get_info(host='localhost', port=25565):
    return MCServer(host=host, port=port).get_info()


# Strings in the minecraft protocol are encoded as big-endian UCS-2,
# prefixed with a short giving its length in characters.
def pack_string(string):
    return struct.pack('>h', len(string)) + string.encode('utf-16be')


# shared socket connect functionality
def _get_info(host, port, protocol):
    # Set up our socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(20) # seconds
    s.connect((host, port))

    s.sendall(protocol._get_message(host, port))

    data = StringIO()
    got_bytes = True
    while got_bytes:
        in_bytes = s.recv(1024)
        if len(in_bytes) > 0:
            data.write(in_bytes)
        else:
            got_bytes = False

    s.shutdown(socket.SHUT_RDWR)
    s.close()

    info = protocol.parse_resp(data.getvalue())
    return info


class MCServer(object):

    def __init__(self, host='localhost', port=25565, protocols=None):
        self.host = host
        self.port = port
        if protocols is None:
            self.protocols = ['MC17', 'MC16', 'MC15']
        else:
            self.protocols = protocols

    def get_info(self):
        for protocol in self.protocols:
            klass = globals()[protocol]
            protocol_cls = klass()
            try:
                return protocol_cls.get_info(self.host, self.port)
            except Exception:
                LOG.warn("Failed to get_info with protocol %s" % protocol)
                LOG.info(traceback.format_exc())


class MC15(object):

    def _get_message(self, host, port):
        # Send 0xFE: Server list ping
        return '\xfe\x01'

    def get_info(self, host='localhost', port=25565):
        return _get_info(host, port, self)

    def parse_resp(self, d):
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


class MC16(MC15):

    def _get_message(self, host, port):
        msg = StringIO()

        # Send 0xFE: Server list ping
        msg.write('\xfe\x01')

        # Send 0xFA: Plugin message
        msg.write('\xfa')                           # ident
        msg.write(struct.pack_string('MC|PingHost'))       # message identifier
        msg.write(struct.pack('>h', 7 + 2*len(host)))      # payload length
        msg.write(struct.pack('b', 78))                    # protocol version
        msg.write(struct.pack_string(host))                # hostname
        msg.write(struct.pack('>i', port))                 # port

        return msg.getvalue()

class MC17(object):

    def unpack_varint(self, s):
        d = 0
        for i in range(5):
            b = ord(s.recv(1))
            d |= (b & 0x7F) << 7*i
            if not b & 0x80:
                break
        return d

    def pack_varint(self, d):
        o = ""
        while True:
            b = d & 0x7F
            d >>= 7
            o += struct.pack("B", b | (0x80 if d > 0 else 0))
            if d == 0:
                break
        return o

    def pack_data(self, d):
        return self.pack_varint(len(d)) + d

    def pack_port(self, i):
        return struct.pack('>H', i)

    def get_info(self, host='localhost', port=25565):

        # Connect
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))

        # Send handshake + status request
        s.send(self.pack_data("\x00\x00" +
               self.pack_data(host.encode('utf8')) +
               self.pack_port(port) + "\x01"))
        s.send(self.pack_data("\x00"))

        # Read response
        self.unpack_varint(s)     # Packet length
        self.unpack_varint(s)     # Packet ID
        l = self.unpack_varint(s) # String length

        d = ""
        while len(d) < l:
            d += s.recv(1024)

        # Close our socket
        s.shutdown(socket.SHUT_RDWR)
        s.close()

        # Load json and return
        return json.loads(d.decode('utf8'))
