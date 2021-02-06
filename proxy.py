import socket
import select

HOST = 'localhost'
PORT = 1337
HTTP_PORT = 80
TIMEOUT_IN_SECONDS = 3
TROLLY_URL = 'http://zebroid.ida.liu.se/fakenews/trolly.jpg'


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
        print(data)
        full_data += data
        if not data \
                or data.endswith(b'\r\n\r\n') \
                or data.endswith(b'\x00\x00'):
            print('No more data to receive.')
            return full_data


def send_over_connection(conn, data):
    print('Sending data...')
    conn.sendall(data)


def replace_smiley_url(data, index):
    start_index = index
    end_index = index
    while data[end_index + 1] != ' ':
        end_index += 1
    while data[start_index - 1] != ' ':
        start_index -= 1
    return data.replace(data[start_index:end_index], TROLLY_URL)


def replace_forbidden(data):
    data = str(data)

    jpg_index = 0
    png_index = 0
    gif_index = 0
    while True:
        found_replaceable = False

        jpg_index = data.find('smiley.jpg', jpg_index)
        if jpg_index != -1:
            data = replace_smiley_url(data, jpg_index)
            found_replaceable = True

        png_index = data.find('smiley.png', png_index)
        if png_index != -1:
            data = replace_smiley_url(data, png_index)
            found_replaceable = True

        gif_index = data.find('smiley.gif')
        if gif_index != -1:
            data = replace_smiley_url(data, gif_index)
            found_replaceable = True

        if not found_replaceable:
            break

    data = data.replace('Smiley',
                        'Trolly') \
               .replace('Stockholm',
                        'Linköping')
    return bytes(data, 'utf-8')


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
            # host_data = replace_forbidden(host_data)
            print(host_data)

            send_over_connection(browser_conn, host_data)
            browser_data = receive_over_connection(browser_conn)
            # browser_data = replace_forbidden(browser_data)
            print(browser_data)

        server_sock.close()
        browser_conn.close()
        host_conn.close()


run_proxy()
