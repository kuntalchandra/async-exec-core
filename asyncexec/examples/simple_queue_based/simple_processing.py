import sys
sys.path.insert(0, '../../../')

from asyncexec.exec import  AsyncExecutor
'''
    "redis": {
        "host": "172.17.0.3",
        "port": 6379
    }
    "rabbitmq": {
        "host": "172.17.0.2",
        "port": 5672,
        "username": "guest",
        "password": "guest"
    }
'''

async_executor = AsyncExecutor({
    'process_info': {
        'workers': 10,
        'pool': 'process'
    },
    "redis": {
        "host": "172.17.0.3",
        "port": 6379
    }
    
})

import time
@async_executor.handler('redis', 'in_q1', 'out_q1')
def test_method1(data):
    print ("Called 1", data)
    return 'result'

@async_executor.handler('redis', 'in_q2', 'out_q2')
def test_method2(data):
    print ("Called 2", data)
    return 'result'

async_executor.start()
