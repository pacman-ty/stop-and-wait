"""
Network emulator for the Stop-and-Wait RDT protocol.

Sits between the sender and receiver, forwarding packets over UDP.
Data packets from the sender are dropped with a configurable probability;
ACK and EOT packets are never dropped.

Usage:
    python3 nEmulator.py <emu_port> <recv_host> <recv_port> \
                         <sender_host> <sender_port> <probability> <verbose>
"""

import sys
import socket
import random
from packet import parse_packet, TYPE_DATA, TYPE_ACK, TYPE_EOT, MAX_PACKET_SIZE


def main():
    if len(sys.argv) != 8:
        print(f"Usage: {sys.argv[0]} <emu_port> <recv_host> <recv_port> "
              f"<sender_host> <sender_port> <probability> <verbose>")
        sys.exit(1)

    emu_port = int(sys.argv[1])
    recv_host = sys.argv[2]
    recv_port = int(sys.argv[3])
    sender_host = sys.argv[4]
    sender_port = int(sys.argv[5])
    drop_prob = float(sys.argv[6])
    verbose = int(sys.argv[7]) == 1

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', emu_port))

    # Addresses used when forwarding packets
    recv_forward = (recv_host, recv_port)
    sender_forward = (sender_host, sender_port)

    # We learn the actual (ip, port) of each endpoint from the first packet
    # they send, so that EOT direction can be determined reliably
    sender_addr = None
    receiver_addr = None

    while True:
        raw, addr = sock.recvfrom(MAX_PACKET_SIZE)
        pkt_type, seqnum, _, _ = parse_packet(raw)

        if pkt_type == TYPE_DATA:
            sender_addr = addr
            if verbose:
                print(f"receiving Packet {seqnum}", flush=True)
            if random.random() < drop_prob:
                if verbose:
                    print(f"discarding Packet {seqnum}", flush=True)
            else:
                sock.sendto(raw, recv_forward)
                if verbose:
                    print(f"forwarding Packet {seqnum}", flush=True)

        elif pkt_type == TYPE_ACK:
            receiver_addr = addr
            if verbose:
                print(f"receiving ACK {seqnum}", flush=True)
                print(f"forwarding ACK {seqnum}", flush=True)
            sock.sendto(raw, sender_forward)

        elif pkt_type == TYPE_EOT:
            if addr == sender_addr:
                if verbose:
                    print("receiving EOT", flush=True)
                    print("forwarding EOT", flush=True)
                sock.sendto(raw, recv_forward)
            elif addr == receiver_addr:
                if verbose:
                    print("receiving EOT", flush=True)
                    print("forwarding EOT", flush=True)
                sock.sendto(raw, sender_forward)


if __name__ == '__main__':
    main()
