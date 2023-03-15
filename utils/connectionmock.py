"""
A simple echo server over TCP sockets (borrowed from [1]) for testing the
UAVSocket class.

[1]: https://docs.python.org/3/library/asyncio-protocol.html#tcp-echo-server

Can be run normally with `python ./utils/connectionmock.py`.
Then the echo server will be started on localhost:1234 and all output will be
printed to stdout.

This can be run in conjunction with the pigeon GUI to view all data being sent
as part of the socket protocol.
"""

import asyncio

class EchoServerProtocol(asyncio.Protocol):
    def connection_made(self, transport: asyncio.Transport):
        peername = transport.get_extra_info('peername')
        print(f'Connection from {peername}')
        self.transport = transport

    def data_received(self, data):
        print(f'Data received: {data!r}')

        print(f'Send: {data!r}')
        self.transport.write(data)

async def main():
    loop = asyncio.get_running_loop()
    server = await loop.create_server(lambda: EchoServerProtocol(), '127.0.0.1', 1234)
    async with server:
        await server.serve_forever()

asyncio.run(main())
