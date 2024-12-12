import mimetypes
import pathlib
import socket
import urllib.parse
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from multiprocessing import Process
from pymongo import MongoClient

HTTP_SERVER_PORT = 3000
SOCKET_SERTVER_IP = '127.0.0.1'
SOCKET_SERVER_PORT = 5000
mongo_client = MongoClient("mongodb://mongo:27017/")

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(data, (SOCKET_SERTVER_IP, SOCKET_SERVER_PORT))
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

def run_http_server():
    http = HTTPServer(('', HTTP_SERVER_PORT), HttpHandler)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def run_socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SOCKET_SERTVER_IP, SOCKET_SERVER_PORT))
    try:
        while True:
            data, address = sock.recvfrom(1024)
            data_parse = urllib.parse.unquote_plus(data.decode())
            message = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
            message['date'] = str(datetime.now())
            db = mongo_client.feedback_db
            db.messages.insert_one(message)
    except KeyboardInterrupt:
        logging.info(f'Destroy server')
    finally:
        sock.close()

if __name__ == '__main__':
    logging.basicConfig(filename='logs.txt')
    http_process = Process(target=run_http_server)
    socket_process = Process(target=run_socket_server)
    http_process.start()
    socket_process.start()
    http_process.join()
    socket_process.join()
