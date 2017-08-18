import asyncio
import uvloop
from collections import defaultdict
from asyncexec.workers.flow_builder import Flow


class AsyncExecutor(object):

    def __init__(self, configurations):
        self.channel_configurations = {}
        self.flows = []

        if 'rabbitmq' in configurations:
            rabbitmq = configurations['rabbitmq']
            host = rabbitmq['host']
            port = rabbitmq['port']
            username = rabbitmq.get('username', 'guest')
            password = rabbitmq.get('password', 'guest')
            self.channel_configurations['rabbitmq'] = (host, port, username, password)

        if 'redis' in configurations:
            redis = configurations['redis']
            host = redis['host']
            port = redis['port']
            username = redis.get('user', 'guest')
            password = redis.get('password', 'guest')
            self.channel_configurations['redis'] = (host, port, username, password)

        if 'http' in configurations:
            http = configurations['http']
            port = http['port']
            self.channel_configurations['http'] = (None, port, None, None)

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        self.loop = uvloop.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def start(self):
        futures = []
        for ix, flow in enumerate(self.flows):
            print(ix)
            future = self.loop.run_until_complete(flow.start())
            futures.append(future)
        for future in asyncio.gather(*futures):
            print(self.loop.run_until_complete(future))


    def publisher(self, out_channel, out_queue):
        def decorator(func):
            print ("Registering handler {} for channel: {} on queues ({})".format(
                func.__name__, out_channel, out_queue))
            assert out_channel in self.channel_configurations
            host, port, username, password = self.channel_configurations[out_channel]
            config = {
                'max_workers': None,
                'middlewares': {
                    out_channel: {
                        'host': host,
                        'port': port,
                        'username': username,
                        'password': password
                    }
                }
            }
            flow = Flow(config, loop=self.loop) \
                .add_generator(func) \
                .add_publisher(out_channel, out_queue)
            self.flows.append(flow)
            print('flow', out_channel, out_queue, 'ready')

            return func
        return decorator

    def listener(self, in_channel, in_queue, max_workers=4):
        def decorator(func):
            print ("Registering handler {} for channel: {} on queues ({})".format(
                func.__name__, in_channel, in_queue))
            assert in_channel in self.channel_configurations
            host, port, username, password = self.channel_configurations[in_channel]
            config = {
                'max_workers': max_workers,
                'middlewares': {
                    in_channel: {
                        'host': host,
                        'port': port,
                        'username': username,
                        'password': password
                    }
                }
            }
            flow = Flow(config, loop=self.loop)\
                .add_listener(in_channel, in_queue)\
                .add_sink(func)
            self.flows.append(flow)
            print('flow', in_channel, in_queue, 'ready')

            return func
        return decorator

    def handler(self, channel, queue_request, queue_response, max_workers=4):
        def decorator(func):
            print ("Registering handler {} for channel: {} on queues ({}, {})".format(
                func.__name__, channel, queue_request, queue_response
            ))
            assert channel in self.channel_configurations
            host, port, username, password = self.channel_configurations[channel]
            config = {
                'max_workers': max_workers,
                'middlewares': {
                    channel: {
                        'host': host,
                        'port': port,
                        'username': username,
                        'password': password
                    }
                }
            }
            flow = Flow(config, loop=self.loop)
            flow.add_listener(channel, queue_request)
            if queue_response is None:
                flow.add_sink(func)
            else:
                flow.add_worker(func).add_publisher(channel, queue_response)
            self.flows.append(flow)
            print('flow', channel, queue_request, queue_response, 'ready')

            return func
        return decorator
