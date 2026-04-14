#!/usr/bin/env python3

import socket

# This script is a minimal UDP broadcast listener for debugging purposes.
# It helps determine if broadcast packets (like Go/Stop) are reaching the OS
# on the correct port (15730) after the main application has registered itself.

PORT = 15730 # Port where the Marklin box sends broadcasts and status updates
HOST = '0.0.0.0' # Listen on all interfaces

def listen_loop():
    """Creates a socket and enters a loop to listen for UDP broadcasts."""
    # Create a UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # Allow receiving broadcast packets
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Allow reusing addresses, helpful for quick restarts
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        print(f"Listening for UDP broadcasts on port {PORT}...")
        while True:
            data, addr = s.recvfrom(1024)
            print(f"Received packet from {addr}: {data.hex()}")
    except KeyboardInterrupt:
        print("\nExiting.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    listen_loop()