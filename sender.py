#!/usr/bin/env python3
"""
sender.py - Stop-and-Wait RDT sender
CS 436 Assignment 1

Usage: python3 sender.py <emulator_host> <emulator_port> <sender_port> <timeout_ms> <filename>
"""

import socket
import sys
import struct
import time

# Packet types
TYPE_ACK  = 0
TYPE_DATA = 1
TYPE_EOT  = 2

PACKET_HEADER_SIZE = 12   # 3 x 4-byte integers
MAX_DATA_SIZE      = 500


def make_packet(ptype, seqnum, data=b''):
    """
    Build a packet: | type (4B) | seqnum (4B) | length (4B) | data |
    """
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
    if len(sys.argv) != 6:
        print("Usage: python3 sender.py <emulator_host> <emulator_port> "
              "<sender_port> <timeout_ms> <filename>")
        sys.exit(1)

    emulator_host = sys.argv[1]
    emulator_port = int(sys.argv[2])
    sender_port   = int(sys.argv[3])
    timeout_ms    = int(sys.argv[4])
    filename      = sys.argv[5]

    timeout_sec = timeout_ms / 1000.0

    # Read the file and split into chunks of MAX_DATA_SIZE bytes
    try:
        with open(filename, 'rb') as f:
            file_bytes = f.read()
    except FileNotFoundError:
        print(f"Error: file '{filename}' not found.")
        sys.exit(1)

    # Split into chunks
    chunks = []
    for i in range(0, max(1, len(file_bytes)), MAX_DATA_SIZE):
        chunks.append(file_bytes[i:i + MAX_DATA_SIZE])
    if len(file_bytes) == 0:
        chunks = [b'']

    # Open UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', sender_port))

    seqnum_log = []
    ack_log    = []

    seqnum = 1   # First packet seqnum is 1

    for chunk in chunks:
        packet = make_packet(TYPE_DATA, seqnum, chunk)
        while True:
            # Send packet
            sock.sendto(packet, (emulator_host, emulator_port))
            seqnum_log.append(seqnum)

            # Wait for ACK with timeout
            sock.settimeout(timeout_sec)
            try:
                raw, _ = sock.recvfrom(PACKET_HEADER_SIZE + MAX_DATA_SIZE)
                parsed = parse_packet(raw)
                if parsed is None:
                    continue
                ptype, aseqnum, _, _ = parsed
                if ptype == TYPE_ACK and aseqnum == seqnum:
                    ack_log.append(aseqnum)
                    seqnum += 1
                    break
                # Wrong ACK or unexpected packet — retransmit
            except socket.timeout:
                # Timer expired — retransmit (loop continues)
                pass

    # Send EOT
    eot_packet = make_packet(TYPE_EOT, 0, b'')
    sock.sendto(eot_packet, (emulator_host, emulator_port))

    # Wait for EOT from receiver (assumed never lost per spec)
    sock.settimeout(10.0)
    while True:
        try:
            raw, _ = sock.recvfrom(PACKET_HEADER_SIZE + MAX_DATA_SIZE)
            parsed = parse_packet(raw)
            if parsed and parsed[0] == TYPE_EOT:
                break
        except socket.timeout:
            # Resend EOT just in case
            sock.sendto(eot_packet, (emulator_host, emulator_port))

    sock.close()

    # Write log files
    with open('seqnum.log', 'w') as f:
        for n in seqnum_log:
            f.write(f"{n}\n")

    with open('ack.log', 'w') as f:
        for n in ack_log:
            f.write(f"{n}\n")

    print("Transmission complete. Logs saved to seqnum.log and ack.log.")


if __name__ == '__main__':
    main()
