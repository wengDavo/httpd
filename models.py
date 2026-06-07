import socket


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


class StatusLine:
    def __init__(self, status_code=None, version="HTTP/1.1") -> None:
        self.version = version
        self.status_code = status_code

    @property
    def reason(self):
        if self.status_code is None:
            return ""
        status_codes = {
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        }
        return status_codes.get(int(self.status_code), "Unknown")


class HTTPRequest:
    def __init__(self, method, path, status_line: StatusLine, headers, body=""):
        self.method = method
        self.path = path
        self.status_line = status_line
        self.headers = headers
        self.body = body


class HTTPResponse:
    def __init__(
        self,
        status_line: StatusLine,
        headers: dict[str, str] | None = None,
        body: str = "",
    ) -> None:
        self.status_line = status_line
        self.headers = headers
        self.body = body

    def encode(self) -> bytes:
        body_bytes = self.body.encode("utf-8")
        content_type = (self.headers or {}).get("Content-Type", "text/plain")

        lines = [
            f"{self.status_line.version} {self.status_line.status_code} {self.status_line.reason}"
        ]
        lines.append(f"Content-Length: {len(body_bytes)}")
        lines.append(f"Content-Type: {content_type}")
        if self.headers:
            for k, v in self.headers.items():
                lines.append(f"{k}: {v}")
        lines.append("")
        return "\r\n".join(lines).encode() + b"\r\n" + body_bytes
