"""
Shared packet module for the Stop-and-Wait RDT protocol.

Packet format (all integers are unsigned 32-bit, network byte order):
    integer type    -- 0: ACK, 1: Data, 2: EOT
    integer seqnum  -- sequence number
    integer length  -- number of bytes in the data field (0–500)
    String  data    -- payload (max 500 characters)
"""

import struct

TYPE_ACK = 0
TYPE_DATA = 1
TYPE_EOT = 2

HEADER_FORMAT = '!III'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # 12 bytes
MAX_DATA_LENGTH = 500
MAX_PACKET_SIZE = HEADER_SIZE + MAX_DATA_LENGTH


def create_packet(pkt_type, seqnum, data=""):
    # Serialize a packet into bytes ready to send over UDP.
    encoded_data = data.encode('utf-8')
    length = len(encoded_data)
    header = struct.pack(HEADER_FORMAT, pkt_type, seqnum, length)
    return header + encoded_data


def parse_packet(raw_bytes):
    # Deserialize raw bytes into (type, seqnum, length, data)
    pkt_type, seqnum, length = struct.unpack(HEADER_FORMAT, raw_bytes[:HEADER_SIZE])
    data = raw_bytes[HEADER_SIZE:HEADER_SIZE + length].decode('utf-8')
    return pkt_type, seqnum, length, data
