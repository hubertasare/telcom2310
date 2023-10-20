import sys
import time
import argparse
import socket
from util import *

RECV_BUFFER_SIZE = 2048


def get_args(argv):
    parser = argparse.ArgumentParser(description="Selective Repeat Server")
    parser.add_argument('-p', '--port', required=False,
                        default=12000, type=int)
    parser.add_argument('-f', '--filename', required=False,
                        default="received_file.txt")
    parser.add_argument('-t', '--final-timeout',
                        required=False, default=2.0, type=float)
    return parser.parse_args()


def main(argv):
    args = get_args(argv)
    final_timeout = args.final_timeout

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', args.port))

    outfile = open(args.filename, 'wb')
    start_time = None
    bytes_recvd = 0
    expected_seq = 0
    pkt_buffer = {}

    while True:
        try:
            pkt, addr = server_socket.recvfrom(RECV_BUFFER_SIZE)
            pkt_header = PacketHeader(pkt[:PacketHeader.header_len])
            data = pkt[PacketHeader.header_len:PacketHeader.header_len +
                       pkt_header.length]

            if not start_time:
                start_time = time.time()

            if pkt_header.seq_num not in pkt_buffer:
                pkt_buffer[pkt_header.seq_num] = data
                server_socket.sendto(bytes(pkt_header), addr)

                while expected_seq in pkt_buffer:
                    data = pkt_buffer.pop(expected_seq)
                    outfile.write(data)
                    bytes_recvd += len(data)
                    expected_seq += 1

                    if pkt_header.seq_num % 1000 == 0:
                        cur_time = time.time()
                        elapsed_time = cur_time - start_time
                        throughput = (bytes_recvd * 8) / \
                            (elapsed_time) / 1000000
                        print("Packet {}\tBytes Recvd {}\tTime Elapsed {}\tThroughput {} Mbps".format(
                            pkt_header.seq_num, bytes_recvd, elapsed_time, throughput))

                if pkt_header.type == PacketHeader.TYPE_END:
                    print("Got last packet with seq {}. Waiting {} sec and then quitting".format(
                        pkt_header.seq_num, final_timeout))
                    outfile.close()
                    end_time = time.time()
                    server_socket.settimeout(final_timeout)

        except socket.timeout as e:
            print("Final wait time expired. Exiting...")
            break

    server_socket.close()

    elapsed_time = end_time - start_time
    throughput = (bytes_recvd * 8) / elapsed_time
    print("Bytes transferred: {}".format(bytes_recvd))
    print("Time Elapsed: {} sec".format(elapsed_time))
    print("Throughput: {} Mbps".format(throughput/1000000.0))


if __name__ == "__main__":
    main(sys.argv[1:])
