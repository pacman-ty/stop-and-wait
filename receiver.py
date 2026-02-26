#!/usr/bin/env python3
"""
Receiver for the Stop-and-Wait RDT protocol.

Receives data packets from the sender (via the network emulator), writes the
reassembled file, and sends ACKs back through the emulator.  Handles duplicate
packets by only appending data for the next expected sequence number.

Usage:
    python3 receiver.py <emu_host> <emu_port> <recv_port> <output_file>
"""

import sys
import socket
from packet import (create_packet, parse_packet,
                    TYPE_DATA, TYPE_ACK, TYPE_EOT,
                    MAX_PACKET_SIZE)


def main():
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} <emu_host> <emu_port> <recv_port> "
              f"<output_file>")
        sys.exit(1)

    emu_host = sys.argv[1]
    emu_port = int(sys.argv[2])
    recv_port = int(sys.argv[3])
    output_file = sys.argv[4]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', recv_port))

    arrival_log = []
    received_data = []
    expected_seqnum = 1

    while True:
        raw, _ = sock.recvfrom(MAX_PACKET_SIZE)
        pkt_type, seqnum, length, data = parse_packet(raw)

        if pkt_type == TYPE_DATA:
            arrival_log.append(seqnum)

            # Only accept data from the next expected packet (discard duplicates)
            if seqnum == expected_seqnum:
                received_data.append(data)
                expected_seqnum += 1

            # ACK every data packet regardless (matching seqnum per spec)
            ack = create_packet(TYPE_ACK, seqnum)
            sock.sendto(ack, (emu_host, emu_port))

        elif pkt_type == TYPE_EOT:
            # Save the output file and log before exiting
            with open(output_file, 'w') as f:
                f.write(''.join(received_data))

            with open('arrival.log', 'w') as f:
                for s in arrival_log:
                    f.write(f"{s}\n")

            # Send EOT back to sender (via emulator)
            eot = create_packet(TYPE_EOT, 0)
            sock.sendto(eot, (emu_host, emu_port))
            break

    sock.close()


if __name__ == '__main__':
    main()
