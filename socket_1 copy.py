import concurrent.futures
import threading
import http.client
import socket
# Create a lock for synchronizing output
output_lock = threading.Lock()

def is_port_open(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            sock.connect((host, port))
            return port
    except socket.timeout:
        return None
    except (socket.error, OSError):
        return None

def identify_server_info(host, port, proxy=None):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            sock.connect((host, port))

            if port == 80:  # HTTP
                conn = http.client.HTTPConnection(host, port)
                conn.request("GET", "/")
                response = conn.getresponse()
                server_info = response.getheader("Server", "Unknown Server")
            else:  # For other ports, send an empty request
                sock.send(b"\r\n")
                data = sock.recv(4096).decode("utf-8")
                server_info = data.split('\n')[0]

        with output_lock:
            if proxy:
                print(f"Host: {host}, Port: {port}, Proxy: {proxy} - Server: {server_info}")
            else:
                print(f"Host: {host}, Port: {port} - Server: {server_info}")
    except (socket.error, OSError):
        pass


def get_ports_from_user():
    while True:
        try:
            choice = input("Enter 'L' for a list of ports or 'R' for a range of ports: ").upper()

            if choice == 'L':
                ports_input = input("Enter a comma-separated list of ports to check (e.g., 80, 443, 8080): ")
                ports = [int(p.strip()) for p in ports_input.split(',')]
                return ports
            elif choice == 'R':
                start_port = int(input("Enter the starting port: "))
                end_port = int(input("Enter the ending port: "))
                return list(range(start_port, end_port + 1))
            else:
                print("Invalid choice. Please enter 'L' or 'R'.")
        except ValueError:
            print("Invalid input. Please enter valid integers.")

def get_max_workers_from_user():
    while True:
        try:
            max_workers = int(input("Enter the number of max_workers for thread pool: "))
            if max_workers > 0:
                return max_workers
            else:
                print("Please enter a positive integer.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

def get_proxy_from_user():
    use_proxy = input("Do you want to use a proxy? (yes/no): ").lower()
    if use_proxy == 'yes':
        proxy_host = input("Enter proxy host: ")
        proxy_port = int(input("Enter proxy port: "))
        return (proxy_host, proxy_port)
    else:
        return None

def scan_ports(host, ports_to_check, max_workers, proxy=None):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for port in ports_to_check:
            future = executor.submit(is_port_open, host, port)
            future.add_done_callback(lambda f: identify_server_info(host, f.result(), proxy) if f.result() is not None else None)

# Example usage
host_to_check = input("Enter the host to check: ")
ports_to_check = get_ports_from_user()
max_workers = get_max_workers_from_user()
proxy_settings = get_proxy_from_user()

scan_ports(host_to_check, ports_to_check, max_workers, proxy=proxy_settings)