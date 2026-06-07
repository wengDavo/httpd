# httpd

A minimal HTTP/1.1 server built from scratch in Python using raw sockets. No frameworks, no dependencies.

## Features

- TCP server with configurable host/port
- Request parsing (method, path, version, headers)
- Body assembly for POST/PUT (Content-Length and chunked transfer-encoding)
- Request logging with client address

## Usage

```bash
python server.py              # starts on 0.0.0.0:80
python server.py 127.0.0.1    # starts on 127.0.0.1:80
python server.py 0.0.0.0 8080 # starts on 0.0.0.0:8080
```

```bash
curl http://localhost/
curl -X POST http://localhost/ -d "hello"
```
