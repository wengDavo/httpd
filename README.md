# httpd

A minimal HTTP/1.1 server built from scratch in Python using raw sockets. No frameworks, no dependencies.

## Features

- TCP server with configurable host/port via CLI args
- Request parsing (method, path, version, headers, body)
- Body assembly for POST/PUT (Content-Length and chunked transfer-encoding)
- Routing system — register handlers by method + path
- Thread-per-connection concurrent handling
- Graceful shutdown on Ctrl+C
- Error handling with proper status codes (400, 404, 500)
- Request logging with client address

## Project structure

```
models.py    — HTTPRequest, HTTPResponse, StatusLine, Socket
server.py    — HttpServer with routing and connection handling
```

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
