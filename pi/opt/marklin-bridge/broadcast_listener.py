import socket

# This script is a minimal UDP broadcast listener for debugging purposes.
# It helps determine if broadcast packets are reaching the OS, independent
# of the main marklin-bridge application.

PORT = 15731
HOST = '0.0.0.0' # Listen on all interfaces

# Create a UDP socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Allow receiving broadcast packets
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Allow reusing addresses, helpful for quick restarts
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
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