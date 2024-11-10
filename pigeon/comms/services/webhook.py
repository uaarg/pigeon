import datetime
from typing import Dict, List, Callable, Any
import asyncio

from websockets.asyncio.server import serve

class Message:
    type: str
    time: datetime.datetime
    data: Dict


class Connection:
    subscribers: List[Callable] = []

    def start(self) -> Any:
        raise NotImplementedError()

    def subscribe(self, subscriber: Callable) -> None:
        self.subscribers.append(subscriber)

    def send(self, msg: Message) -> None:
        raise NotImplementedError()

    def close(self) -> None:
        raise NotImplementedError()

    def __str__(self) -> str:
        raise NotImplementedError()



class WebsocketsConnection(Connection):

    def __init__(self, port=8001) -> None:
        self.port = port

    async def handler(self, websocket):
        try:
            async for message in websocket:
                print(message)        
        except:
            print("connection closed")
           
    async def start(self):
        async with serve(self.handler, "", self.port):
            await asyncio.get_running_loop().create_future()  # run forever
 
