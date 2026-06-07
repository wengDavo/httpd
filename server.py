import sys
import threading

from models import Socket, HTTPRequest, HTTPResponse, StatusLine


class HttpServer:
    def __init__(self, hostname, port) -> None:
        self.hostname = hostname
        self.port = port
        self.socket = Socket()
        self.socket.bind(self.hostname, self.port)
        self.socket.listen()
        self.socket.socket.settimeout(1.0)
        self.routes = {}

    def read_chunked_body(self, conn, initial_buffer: bytes):
        full_body = b""
        buffer = initial_buffer

        def get_line():
            nonlocal buffer
            while b"\r\n" not in buffer:
                try:
                    new_data = conn.recv(1024)
                except ConnectionResetError:
                    return b""
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
                try:
                    chunk = conn.recv(max(chunk_size - len(buffer), 1024))
                except ConnectionResetError:
                    return full_body.decode("utf-8")
                if not chunk:
                    return full_body.decode("utf-8")
                buffer += chunk

            full_body += buffer[:chunk_size]
            buffer = buffer[chunk_size:]

            if buffer.startswith(b"\r\n"):
                buffer = buffer[2:]
            else:
                try:
                    conn.recv(2)
                except ConnectionResetError:
                    pass

        return full_body.decode("utf-8")

    def _send_response(self, conn, http_response: HTTPResponse):
        try:
            conn.sendall(http_response.encode())
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            conn.close()

    def route(self, method, path, handler):
        self.routes[(method, path)] = handler

    def dispatch(self, request):
        handler = self.routes.get((request.method, request.path))
        if handler:
            return handler(request)
        else:
            return HTTPResponse(StatusLine(404))

    def _handle_client(self, conn, addr):
        try:
            raw_data = conn.recv(self.socket.buffer)
            if not raw_data:
                conn.close()
                return

            header_end_idx = raw_data.find(b"\r\n\r\n")
            if header_end_idx == -1:
                conn.close()
                return

            try:
                header_part = raw_data[:header_end_idx].decode("utf-8")
            except UnicodeDecodeError:
                self._send_response(conn, HTTPResponse(StatusLine(400)))
                return

            partial_body = raw_data[header_end_idx + 4 :]

            lines = header_part.split("\r\n")

            try:
                request_line = lines[0]
                method, path, version = request_line.split()
            except (ValueError, IndexError):
                self._send_response(
                    conn, HTTPResponse(StatusLine(400), body="Bad Request Line")
                )
                return

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
                    try:
                        content_length = int(headers.get("Content-Length", 0))
                    except (ValueError, TypeError):
                        self._send_response(
                            conn,
                            HTTPResponse(
                                StatusLine(400), body="Bad Content-Length"
                            ),
                        )
                        return
                    body_bytes = partial_body
                    while len(body_bytes) < content_length:
                        try:
                            chunk = conn.recv(self.socket.buffer)
                        except ConnectionResetError:
                            break
                        if not chunk:
                            break
                        body_bytes += chunk
                    final_body = body_bytes.decode("utf-8", errors="replace")

            request = HTTPRequest(
                method, path, StatusLine(version=version), headers, final_body
            )
            http_response = self.dispatch(request)
            self._send_response(conn, http_response)

        except Exception:
            try:
                http_response = HTTPResponse(
                    StatusLine(500), body="Internal Server Error"
                )
                self._send_response(conn, http_response)
            except Exception:
                conn.close()

    def run(self):
        try:
            while True:
                try:
                    conn, addr = self.socket.accept()
                except OSError:
                    continue

                t = threading.Thread(target=self._handle_client, args=(conn, addr))
                t.start()

        except KeyboardInterrupt:
            print("\nShutting down...")
            self.socket.socket.close()


if __name__ == "__main__":
    hostname = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    print(f"Starting on {hostname}:{port}")
    server = HttpServer(hostname, port)

    server.route(
        "GET",
        "/",
        lambda request: HTTPResponse(
            StatusLine(200),
            {"Content-Type": "text/html"},
            body=f"""
                <html>
                    <head>
                        <title>Home</title>
                    </head>
                    <body>
                        <h1>Home</h1>
                        {request.method}
                    </body>
                </html>
            """,
        ),
    )

    server.run()
