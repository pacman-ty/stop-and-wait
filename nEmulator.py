#!/usr/bin/env python3
"""
nEmulator.py - Simple network emulator for CS 436 A1
Forwards packets from sender to receiver (dropping data with given probability).
Forwards ACKs from receiver to sender (never dropped).
EOT packets from sender are never dropped.

Usage:
  python3 nEmulator.py <emulator_port> <receiver_host> <receiver_port>
                       <sender_host> <sender_port> <probability> <verbose>

  verbose: 1 = print internal processing, 0 = silent
"""

import socket
import sys
import struct
import random

TYPE_ACK  = 0
TYPE_DATA = 1
TYPE_EOT  = 2

PACKET_HEADER_SIZE = 12
MAX_DATA_SIZE      = 500


def parse_packet(raw):
    if len(raw) < PACKET_HEADER_SIZE:
        return None
    ptype, seqnum, length = struct.unpack('!III', raw[:PACKET_HEADER_SIZE])
    data = raw[PACKET_HEADER_SIZE: PACKET_HEADER_SIZE + length]
    return ptype, seqnum, length, data


def main():
    if len(sys.argv) != 8:
        print("Usage: python3 nEmulator.py <emulator_port> <receiver_host> <receiver_port> "
              "<sender_host> <sender_port> <probability> <verbose>")
        sys.exit(1)

    emulator_port = int(sys.argv[1])
    receiver_host = sys.argv[2]
    receiver_port = int(sys.argv[3])
    sender_host   = sys.argv[4]
    sender_port   = int(sys.argv[5])
    drop_prob     = float(sys.argv[6])
    verbose       = int(sys.argv[7]) == 1

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', emulator_port))
    sock.settimeout(None)

    print(f"nEmulator listening on port {emulator_port}")
    print(f"  -> Receiver: {receiver_host}:{receiver_port}")
    print(f"  -> Sender:   {sender_host}:{sender_port}")
    print(f"  Drop probability: {drop_prob}")

    while True:
        raw, addr = sock.recvfrom(PACKET_HEADER_SIZE + MAX_DATA_SIZE)
        parsed = parse_packet(raw)
        if parsed is None:
            continue

        ptype, seqnum, length, data = parsed
        sender_addr   = (sender_host,   sender_port)
        receiver_addr = (receiver_host, receiver_port)

        # Classify by packet type:
        #   Data (TYPE_DATA) and EOT (TYPE_EOT) come FROM sender → forward to receiver
        #   ACK (TYPE_ACK) and receiver EOT come FROM receiver → forward to sender
        #
        # The receiver's EOT reply is also TYPE_EOT; we distinguish by packet type and
        # which party just sent it. Since both EOTs are TYPE_EOT with seqnum=0, we use
        # the source address to route: if it came from receiver_port → send to sender.

        if ptype == TYPE_ACK:
            # From receiver → forward to sender (never dropped)
            if verbose:
                print(f"forwarding ACK seqnum {seqnum} to sender")
            sock.sendto(raw, sender_addr)

        elif ptype == TYPE_EOT:
            # Could be from sender (forward to receiver) or receiver (forward to sender)
            if addr[1] == receiver_port:
                # Receiver's EOT reply → forward to sender
                if verbose:
                    print(f"forwarding EOT from receiver to sender")
                sock.sendto(raw, sender_addr)
            else:
                # Sender's EOT → forward to receiver (never dropped)
                if verbose:
                    print(f"forwarding EOT from sender to receiver")
                sock.sendto(raw, receiver_addr)

        elif ptype == TYPE_DATA:
            # Data from sender → possibly drop
            should_drop = (random.random() < drop_prob)
            if should_drop:
                if verbose:
                    print(f"discarding Packet seqnum {seqnum}")
            else:
                if verbose:
                    print(f"forwarding Packet seqnum {seqnum}")
                sock.sendto(raw, receiver_addr)

        else:
            if verbose:
                print(f"unknown packet type {ptype}, discarding")


if __name__ == '__main__':
    main()
