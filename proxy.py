import socket

HOST = 'localhost'
PORT = 1337
HTTP_PORT = 80


def init_proxy_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    return sock


def init_proxy_client(remote_address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect(remote_address)
    return sock


def listen_on_socket(sock):
    print('Listening...')
    sock.listen(1)
    conn, browser_address = sock.accept()
    print('Connected to', browser_address)
    return conn, browser_address


def receive_over_connection(conn):
    print('Receiving data...')
    full_data = b''
    while True:
        data = conn.recv(2048)
        print(data)
        full_data += data
        if not data or data.endswith(b'\r\n\r\n') or data.endswith(b'\x00\x00'):
            print('No more data to receive.')
            return full_data


def send_over_connection(conn, data):
    print('Sending data...')
    conn.sendall(data)


def run_proxy():
    while True:
        server_sock = init_proxy_server()
        browser_conn, address = listen_on_socket(server_sock)
        browser_data = receive_over_connection(browser_conn)

        # Do stuff with data
        if browser_data:
            host_index = browser_data.index(b'Host: ') + len(b'Host: ')
            host = browser_data[host_index:].split(b'\r\n')[0]

            host_conn = init_proxy_client((host, HTTP_PORT))

        while browser_data:
            send_over_connection(host_conn, browser_data)
            host_data = receive_over_connection(host_conn)

            print(host_data)

            if not host_data:
                break
            send_over_connection(browser_conn, host_data)
            browser_data = receive_over_connection(browser_conn)

            print(browser_data)

        server_sock.close()
        browser_conn.close()
        host_conn.close()


run_proxy()
