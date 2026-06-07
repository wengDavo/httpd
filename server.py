import socket
import sys


class Socket:
    def __init__(self, inet=socket.AF_INET, stream=socket.SOCK_STREAM) -> None:
        self.socket = socket.socket(inet, stream)
        self.buffer = 1024

    def bind(self, hostname: str, port: int):
        self.socket.bind((hostname, port))

    def listen(self):
        self.socket.listen(1)

    def accept(self):
        return self.socket.accept()


class HttpServer:
    def __init__(self, hostname, port) -> None:
        self.hostname = hostname
        self.port = port
        self.socket = Socket()
        self.socket.bind(self.hostname, self.port)
        self.socket.listen()

    def read_chunked_body(self, conn, initial_buffer: bytes):
        full_body = b""
        buffer = initial_buffer

        def get_line():
            nonlocal buffer
            while b"\r\n" not in buffer:
                new_data = conn.recv(1024)
                if not new_data:
                    break
                buffer += new_data

            if b"\r\n" in buffer:
                line, buffer = buffer.split(b"\r\n", 1)
                return line
            return b""

        while True:
            line = get_line()
            if not line:
                break

            try:
                chunk_size = int(line.strip(), 16)
            except ValueError:
                break

            if chunk_size == 0:
                break

            while len(buffer) < chunk_size:
                buffer += conn.recv(max(chunk_size - len(buffer), 1024))

            full_body += buffer[:chunk_size]
            buffer = buffer[chunk_size:]

            if buffer.startswith(b"\r\n"):
                buffer = buffer[2:]
            else:
                conn.recv(2)

        return full_body.decode("utf-8")

    def run(self):
        while True:
            conn, addr = self.socket.accept()
            raw_data = conn.recv(self.socket.buffer)

            header_end_idx = raw_data.find(b"\r\n\r\n")
            if header_end_idx == -1:
                conn.close()
                continue

            header_part = raw_data[:header_end_idx].decode()
            partial_body = raw_data[header_end_idx + 4 :]

            lines = header_part.split("\r\n")

            request_line = lines[0]
            method, path, version = request_line.split()
            print(f"{addr[0]}:{addr[1]} - {method} {path}")

            headers = {}
            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip()] = value.strip()

            transfer_encoding = headers.get("Transfer-Encoding", "").lower()
            final_body = ""
            if method in ["POST", "PUT"]:
                if transfer_encoding == "chunked":
                    final_body = self.read_chunked_body(conn, partial_body)
                else:
                    content_length = int(headers.get("Content-Length", 0))
                    body_bytes = partial_body
                    while len(body_bytes) < content_length:
                        body_bytes += conn.recv(self.socket.buffer)
                    final_body = body_bytes.decode()

            conn.send(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok")
            conn.close()


if __name__ == "__main__":
    hostname = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    print(f"Starting on {hostname}:{port}")
    server = HttpServer(hostname, port)
    server.run()
