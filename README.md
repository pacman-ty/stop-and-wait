Stop-and-Wait File Transfer Protocol
============================================================

Overview
--------
Implements a Stop-and-Wait reliable data transfer (RDT) protocol that
reliably transfers a text file from a sender to a receiver over an
unreliable network emulated by nEmulator.  The sender transmits one
data packet at a time and waits for an ACK before sending the next.
Lost packets are recovered via timeout-based retransmission.

Language and Requirements
-------------------------
- Language : Python 3 (version 3.6 or later)
- Packages: standard library only (socket, struct, sys, random)
- No Makefile is required.

Files
-----
  packet.py    — Shared packet serialization / deserialization module.
  sender.py    — Sender program.
  receiver.py  — Receiver program.
  nEmulator.py — Network emulator.
  README       — This file.

How to Run
----------
Start the three programs on **three different machines** in this order:

### 1. Network Emulator

    python3 nEmulator.py <emu_port> <recv_host> <recv_port> \
                         <sender_host> <sender_port> <probability> <verbose>

    Parameters:
      emu_port     – UDP port for the emulator to listen on
      recv_host    – hostname or IP of the receiver machine
      recv_port    – UDP port the receiver listens on
      sender_host  – hostname or IP of the sender machine
      sender_port  – UDP port the sender listens on (for ACKs)
      probability  – probability of dropping a data packet (float, 0.0–1.0)
      verbose      – 1 = print internal processing, 0 = silent

### 2. Receiver

    python3 receiver.py <emu_host> <emu_port> <recv_port> <output_file>

    Parameters:
      emu_host    – hostname or IP of the emulator machine
      emu_port    – UDP port of the emulator
      recv_port   – UDP port the receiver listens on
      output_file – name of the file to write received data to

### 3. Sender

    python3 sender.py <emu_host> <emu_port> <sender_port> <timeout_ms> <input_file>

    Parameters:
      emu_host    – hostname or IP of the emulator machine
      emu_port    – UDP port of the emulator
      sender_port – UDP port the sender uses to receive ACKs
      timeout_ms  – retransmission timeout in milliseconds (recommended: 500+)
      input_file  – name of the text file to transfer (10 KB – 15 KB)

Example Execution (in order)
-----------------
    On host1:  python3 nEmulator.py 9991 host2 9994 host3 9992 0.3 1
    On host2:  python3 receiver.py  host1 9991 9994 output.txt
    On host3:  python3 sender.py    host1 9991 9992 1000 input.txt
    
    More Specifically,

    ubuntu2404-002 : python3 nEmulator.py 9991 129.97.167.157 9994 129.97.167.171  9992 0.3 1
    ubuntu2404-012 : python3 receiver.py 129.97.167.158 9991 9994 output.txt
    ubuntu2404-004 : python3 sender.py 129.97.167.158 9991 9992 1000 input.txt

Output Files
------------
After a successful transfer the following log files are created:

  seqnum.log   – sequence numbers of every packet sent by the sender
                 (includes retransmissions), one number per line.
  ack.log      – sequence numbers of every ACK received by the sender,
                 one number per line.
  arrival.log  – sequence numbers of every data packet received by the
                 receiver, one number per line.
  <output_file> – the reassembled file content.


