#!/usr/bin/env python3
"""
receiver.py - Stop-and-Wait RDT receiver
CS 436 Assignment 1

Usage: python3 receiver.py <emulator_host> <emulator_port> <receiver_port> <output_filename>
"""

import socket
import sys
import struct

# Packet types
TYPE_ACK  = 0
TYPE_DATA = 1
TYPE_EOT  = 2

PACKET_HEADER_SIZE = 12
MAX_DATA_SIZE      = 500


def make_packet(ptype, seqnum, data=b''):
    """Build a packet: | type (4B) | seqnum (4B) | length (4B) | data |"""
    length = len(data)
    header = struct.pack('!III', ptype, seqnum, length)
    return header + data


def parse_packet(raw):
    """Parse a raw packet and return (type, seqnum, length, data)."""
    if len(raw) < PACKET_HEADER_SIZE:
        return None
    ptype, seqnum, length = struct.unpack('!III', raw[:PACKET_HEADER_SIZE])
    data = raw[PACKET_HEADER_SIZE: PACKET_HEADER_SIZE + length]
    return ptype, seqnum, length, data


def main():
    if len(sys.argv) != 5:
        print("Usage: python3 receiver.py <emulator_host> <emulator_port> "
              "<receiver_port> <output_filename>")
        sys.exit(1)

    emulator_host = sys.argv[1]
    emulator_port = int(sys.argv[2])
    receiver_port = int(sys.argv[3])
    output_file   = sys.argv[4]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', receiver_port))
    sock.settimeout(None)  # Block indefinitely waiting for packets

    received_data = []   # Ordered list of data chunks
    arrival_log  = []

    expected_seqnum = 1  # First expected packet seqnum

    while True:
        raw, addr = sock.recvfrom(PACKET_HEADER_SIZE + MAX_DATA_SIZE)
        parsed = parse_packet(raw)
        if parsed is None:
            continue

        ptype, seqnum, length, data = parsed

        if ptype == TYPE_EOT:
            # Send EOT back and exit
            eot_packet = make_packet(TYPE_EOT, 0, b'')
            sock.sendto(eot_packet, (emulator_host, emulator_port))
            break

        elif ptype == TYPE_DATA:
            arrival_log.append(seqnum)

            if seqnum == expected_seqnum:
                # In-order packet: accept it
                received_data.append(data)
                # Send ACK
                ack = make_packet(TYPE_ACK, seqnum, b'')
                sock.sendto(ack, (emulator_host, emulator_port))
                expected_seqnum += 1
            else:
                # Out-of-order or duplicate: re-ACK the last correctly received packet
                # (send ACK for expected_seqnum - 1)
                if expected_seqnum > 1:
                    ack = make_packet(TYPE_ACK, expected_seqnum - 1, b'')
                    sock.sendto(ack, (emulator_host, emulator_port))
                # If expected_seqnum == 1 we haven't received anything yet; drop silently

    sock.close()

    # Write received data to output file
    with open(output_file, 'wb') as f:
        for chunk in received_data:
            f.write(chunk)

    # Write arrival log
    with open('arrival.log', 'w') as f:
        for n in arrival_log:
            f.write(f"{n}\n")

    print(f"File saved to '{output_file}'. Arrival log saved to arrival.log.")


if __name__ == '__main__':
    main()
