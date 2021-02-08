import socket


HOST = 'localhost'
PORT = 1337
HTTP_PORT = 80
# This timeout speeds up some waiting that is otherwise done when waiting
# for recv() to receive an empty packet
TIMEOUT_IN_SECONDS = 3
TROLLY_URL = b'http://zebroid.ida.liu.se/fakenews/trolly.jpg'


def init_proxy_server():
    """
    Initiates a stream socket with host and port defined at the top of this
    file. This socket will keep reusing the same port if multiple instances
    were to be run. This socket will act as a server and wait for a client to
    connect to it.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    return sock


def init_proxy_client(remote_address):
    """
    Initiates a stream socket and connects to the remote address passed as
    argument to this function. This socket will keep reusing the same port if
    multiple instances were to be run. This socket will act as the client part
    of the proxy and connect to a remote server.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect(remote_address)
    return sock


def listen_on_socket(sock):
    """
    Listenes and accepts connections that a browser/client tries to innitiate.
    """
    print('Listening...')
    sock.listen(1)
    conn, browser_address = sock.accept()
    print('Connected to', browser_address)
    return conn, browser_address


def receive_over_connection(conn):
    """
    Will receive data over connection 'conn' until either a timeout occurs,
    no data is received or the received data indicates it is the last in
    a sequence.
    """
    print('Receiving data...')
    full_data = b''
    while True:
        # This speeds up some waiting
        conn.settimeout(3)
        try:
            data = conn.recv(2048)
        except socket.error:
            data = b''
        # This prior section is the only one we want to timeout
        conn.settimeout(None)
        full_data += data
        if not data \
                or data.endswith(b'\r\n\r\n') \
                or data.endswith(b'\x00\x00'):
            print('No more data to receive.')
            return full_data


def send_over_connection(conn, data):
    """
    Sends all data 'data' over the connection 'conn'.
    """
    print('Sending data...')
    print('Sent data:', data)
    conn.sendall(data)


def replace_smiley_url(data, index):
    """
    In this lab we want to replace images of smiley with images of trolly,
    so each instance of a smiley image will be replaced with the trolly url
    at the top of this file.
    """
    print('data to replace:', data)
    start_index = index
    end_index = index
    # Search for the end of an url, which so far has been denoted by a space or
    # quotation marks
    while (end_index < len(data)-1) \
            and (data[end_index] != ord(' ')) \
            and (data[end_index] != ord('"')):
        print(data[end_index])
        end_index += 1
    # Same as above but for the start of a url
    while (start_index > 0) \
            and (data[start_index - 1] != ord(' ')) \
            and (data[start_index - 1] != ord('"')):
        start_index -= 1
    return data.replace(data[start_index:end_index], TROLLY_URL)


def replace_forbidden(data):
    """
    Searches through 'data' for instances of a smiley image with suffix
    '.jpg', '.png' or '.gif', or text instances of 'Smiley' to be replaced with
    'Trolly' and text instances of 'Stockholm' to be replaced with 'Linköping'.
    """
    # These keep track of which parts of the data have been searched through
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
    """
    This main function is run when python runs this file. This function
    runs initiation functions and handles the mains loops.
    """
    # This loop is run once per connection
    while True:
        server_sock = init_proxy_server()
        browser_conn, address = listen_on_socket(server_sock)
        browser_data = receive_over_connection(browser_conn)

        if browser_data:
            host_index = browser_data.index(b'Host: ') + len(b'Host: ')
            host = browser_data[host_index:].split(b'\r\n')[0]

            host_conn = init_proxy_client((host, HTTP_PORT))

        # This loop runs multiple times per connection and handles data sent
        # back and forth on this one connection
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
