import socket
import select

HOST = 'localhost'
PORT = 1337
HTTP_PORT = 80
TIMEOUT_IN_SECONDS = 3
TROLLY_URL = b'http://zebroid.ida.liu.se/fakenews/trolly.jpg'


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
        conn.settimeout(3)
        try:
            data = conn.recv(2048)
        except socket.error:
            data = b''
        conn.settimeout(None)
        full_data += data
        if not data \
                or data.endswith(b'\r\n\r\n') \
                or data.endswith(b'\x00\x00'):
            print('No more data to receive.')
            return full_data


def send_over_connection(conn, data):
    print('Sending data...')
    print('Sent data:', data)
    conn.sendall(data)


def replace_smiley_url(data, index):
    print('data to replace:', data)
    start_index = index
    end_index = index
    while (end_index < len(data)-1) and (data[end_index] != ord(' ')) and (data[end_index] != ord('"')):
        print(data[end_index])
        end_index += 1
    while (start_index > 0) and (data[start_index - 1] != ord(' ')) and (data[start_index - 1] != ord('"')):
        start_index -= 1
    print(start_index, end_index)
    print(data[start_index:end_index])
    return data.replace(data[start_index:end_index], TROLLY_URL)


def replace_forbidden(data):
    jpg_index = 0
    png_index = 0
    gif_index = 0
    while True:
        found_replaceable = False

        jpg_index = data.find(b'smiley.jpg', jpg_index)
        if jpg_index != -1:
            data = replace_smiley_url(data, jpg_index)
            found_replaceable = True

        png_index = data.find(b'smiley.png', png_index)
        if png_index != -1:
            data = replace_smiley_url(data, png_index)
            found_replaceable = True

        gif_index = data.find(b'smiley.gif')
        if gif_index != -1:
            data = replace_smiley_url(data, gif_index)
            found_replaceable = True

        if not found_replaceable:
            break

    data = data.replace(b'Smiley',
                        b'Trolly') \
               .replace(b'Stockholm',
                        bytes('Linköping', 'utf-8'))
    return data


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
            if not host_data:
                break
            host_data = replace_forbidden(host_data)

            send_over_connection(browser_conn, host_data)
            browser_data = receive_over_connection(browser_conn)
            browser_data = replace_forbidden(browser_data)

        server_sock.close()
        browser_conn.close()
        host_conn.close()


run_proxy()
