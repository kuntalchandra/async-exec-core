import aiozmq
import aiozmq.rpc
import asyncio
import traceback, sys
import zmq
import aioprocessing


class Actor(aiozmq.rpc.AttrHandler):

    def __init__(self, pool, func, is_generator=True):
        self.pool = pool
        self.func = func
        self.is_generator = is_generator
        self.client = None

    async def start(self):
        server = await aiozmq.rpc.serve_rpc(self, bind='ipc://*:*')
        self.client = await aiozmq.rpc.connect_rpc(
            connect=list(server.transport.bindings())[0])
        return self.client

    @aiozmq.rpc.method
    def handler(self, *args, **kwargs):
        if not self.func:
            raise Exception("Actor does not have the method configured")
        try:
            future = self.pool.submit(self.func, *args, **kwargs)
            if self.is_generator:
                res = future.result()
                return res
            else:
                return None
        except Exception as e:
            print('Error Occurred in Actor', e)
            traceback.print_exc(file=sys.stdout)
            exit(1)

from collections import deque

class Communicator(object):

    def __init__(self):
        self.queue  = asyncio.Queue()
        #self.router = asyncio.get_event_loop().run_until_complete(aiozmq.create_zmq_stream(zmq.ROUTER, bind='ipc://*:*'))
        #self.addr = list(self.router.transport.bindings())[0]
        #self.dealer = asyncio.get_event_loop().run_until_complete(aiozmq.create_zmq_stream(zmq.DEALER, connect=self.addr))
        #self.closed = False
        #self.first = True

    async def publish(self):
        #data = await self.router.read()
        #self.router.write(data)
        #return data[1].decode('utf-8')
        responses = []
        while not self.queue.empty():
            data = await self.queue.get()
            responses.append(data)
        return responses

    async def publish_nowait(self):
        raise Exception("Not implemented")

    def empty(self):
        return self.queue.empty()

    async def consume(self, data):
        await self.queue.put(data)
        #print('dealer:', data)
        #self.dealer.write((data.encode('utf-8'),))
        #u = await self.dealer.read()
        #print(u)
