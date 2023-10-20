import sys, time, argparse
import socket
from util import *


RECV_BUFFER_SIZE = 2048

def get_args(argv):
    parser = argparse.ArgumentParser(description="Selective Repeat Client")
    parser.add_argument('-p', '--port', required=False, default=12000, type=int)
    parser.add_argument('-a', '--address', required=True)
    parser.add_argument('-f', '--filename', required=False, default="test_file.txt")
    parser.add_argument('-w', '--window-size', required=False, default=4, type=int)
    parser.add_argument('-b', '--packet-size', required=False, default=1000, type=int)
    parser.add_argument('-t', '--timeout-interval', required=False, default=1.0, type=float)
    parser.add_argument('-o', '--output-filename', required=False, default="received_file.txt")
    return parser.parse_args()

def main(argv):
    args = get_args(argv)

    packet_size = args.packet_size
    timeout = args.timeout_interval
    window_size = args.window_size
    bytes_sent = 0
    seq = 0
    sent_packets = {}
    window = []

    infile = open(args.filename, 'rb')
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(timeout)
    outfile = open(args.output_filename, 'wb')

    start_time = time.time()
    data = infile.read(packet_size)
    
    while data or window:
        # Send packets within the window
        while data and len(window) < window_size:
            pkt_header = PacketHeader(type=PacketHeader.TYPE_DATA, seq_num=seq, length=len(data))
            pkt = pkt_header / data
            client_socket.sendto(bytes(pkt), (args.address, args.port))
            bytes_sent += len(data)
            sent_packets[seq] = (pkt, time.time())
            window.append(seq)
            seq += 1
            data = infile.read(packet_size)

        # Handle incoming acknowledgments
        try:
            pkt, address = client_socket.recvfrom(RECV_BUFFER_SIZE)
            recv_header = PacketHeader(pkt[:PacketHeader.header_len])
            ack = recv_header.seq_num

            if ack in window:
                window.remove(ack)
                del sent_packets[ack]

        except socket.timeout as e:
            # Handle timeouts by retransmitting unacknowledged packets
            current_time = time.time()
            for seq, (pkt, sent_time) in sent_packets.items():
                if current_time - sent_time >= timeout:
                    client_socket.sendto(bytes(pkt), (args.address, args.port))
                    sent_packets[seq] = (pkt, current_time)

    end_time = time.time()
    client_socket.close()
    infile.close()
    outfile.close()

    elapsed_time = end_time - start_time
    throughput = (bytes_sent * 8) / elapsed_time
    print("\n=== Final Stats ===")
    print("Bytes transferred: {}".format(bytes_sent))
    print("Time Elapsed: {} sec".format(elapsed_time))
    print("Throughput: {} Mbps".format(throughput / 1000000.0))

if __name__ == "__main__":
    main(sys.argv[1:])
