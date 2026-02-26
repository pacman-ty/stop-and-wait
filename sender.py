#!/usr/bin/env python3
"""
Sender for the Stop-and-Wait RDT protocol.

Reads a text file and reliably transfers it to the receiver via the network
emulator.  Implements timeout-based retransmission: one packet is sent at a
time and the next packet is only sent after its ACK is received.

Usage:
    python3 sender.py <emu_host> <emu_port> <sender_port> <timeout_ms> <filename>
"""

import sys
import socket
from packet import (create_packet, parse_packet,
                    TYPE_DATA, TYPE_ACK, TYPE_EOT,
                    MAX_DATA_LENGTH, MAX_PACKET_SIZE)


def main():
    if len(sys.argv) != 6:
        print(f"Usage: {sys.argv[0]} <emu_host> <emu_port> <sender_port> "
              f"<timeout_ms> <filename>")
        sys.exit(1)

    emu_host = sys.argv[1]
    emu_port = int(sys.argv[2])
    sender_port = int(sys.argv[3])
    timeout_s = int(sys.argv[4]) / 1000.0
    filename = sys.argv[5]

    with open(filename, 'r') as f:
        content = f.read()

    # Split file content into chunks of up to 500 characters
    chunks = [content[i:i + MAX_DATA_LENGTH]
              for i in range(0, len(content), MAX_DATA_LENGTH)]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', sender_port))

    seqnum_log = []
    ack_log = []

    # Stop-and-Wait data transfer
    for i, chunk in enumerate[str](chunks):
        seqnum = i + 1
        packet = create_packet(TYPE_DATA, seqnum, chunk)

        while True:
            sock.sendto(packet, (emu_host, emu_port))
            seqnum_log.append(seqnum)

            sock.settimeout(timeout_s)
            try:
                raw, _ = sock.recvfrom(MAX_PACKET_SIZE)
                pkt_type, ack_seqnum, _, _ = parse_packet(raw)

                if pkt_type == TYPE_ACK:
                    ack_log.append(ack_seqnum)
                    if ack_seqnum == seqnum:
                        break  # correct ACK,move to next packet
                # wrong or unexpected packet, fall through and retransmit
            except socket.timeout:
                pass  # timeout, retransmit

    # EOT
    eot = create_packet(TYPE_EOT, 0)
    sock.sendto(eot, (emu_host, emu_port))

    # Wait for the receiver's EOT (never lost, per spec)
    sock.settimeout(None)
    while True:
        raw, _ = sock.recvfrom(MAX_PACKET_SIZE)
        pkt_type, _, _, _ = parse_packet(raw)
        if pkt_type == TYPE_EOT:
            break

    # write logs
    with open('seqnum.log', 'w') as f:
        for s in seqnum_log:
            f.write(f"{s}\n")

    with open('ack.log', 'w') as f:
        for a in ack_log:
            f.write(f"{a}\n")

    sock.close()


if __name__ == '__main__':
    main()
