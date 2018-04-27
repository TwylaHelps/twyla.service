from urllib.parse import urljoin

import requests
from requests.auth import HTTPBasicAuth

class RabbitRest:

    BASE = 'http://localhost:15672/api/'
    RABBIT_AUTH = HTTPBasicAuth('guest', 'guest')

    def queues(self):
        return requests.get(urljoin(self.BASE, 'queues/%2F'), auth=self.RABBIT_AUTH).json()

    def exchanges(self):
        return requests.get(urljoin(self.BASE, 'exchanges/%2F'), auth=self.RABBIT_AUTH).json()

    def create_queue(self, queue_name, bind_to, routing_key):
        body = {"auto_delete": True ,"durable": False}
        resp = requests.put(urljoin(self.BASE, f'queues/%2F/{queue_name}'),
                            auth=self.RABBIT_AUTH,
                            json=body)
        resp = requests.post(urljoin(self.BASE, f"/api/bindings/%2F/e/{bind_to}/q/{queue_name}"),
                             auth=self.RABBIT_AUTH,
                             json={'routing_key': routing_key})


    def delete_queue(self, queue_name):
        url = urljoin(self.BASE, f'queues/%2f/{queue_name}')
        requests.delete(url, auth=self.RABBIT_AUTH)

    def delete_exchange(self, exchange_name):
        url = urljoin(self.BASE, f'exchanges/%2f/{exchange_name}')
        requests.delete(url, auth=self.RABBIT_AUTH)

    def queue_bindings(self, queue_name):
        return requests.get(urljoin(self.BASE, f'queues/%2F/{queue_name}/bindings'),
                            auth=self.RABBIT_AUTH).json()


    def get_messages(self, queue_name):
        url = urljoin(self.BASE, f'queues/%2f/{queue_name}/get')
        body = {'count': 10, "ackmode":"ack_requeue_false", 'encoding': 'auto'}
        resp = requests.post(url, json=body, auth=self.RABBIT_AUTH)
        return resp.json()

    def publish_message(self, exchange_name, routing_key, payload):
        url = urljoin(self.BASE, f'exchanges/%2f/{exchange_name}/publish')
        body = {"properties": {},
                "routing_key": "my key",
                "payload": "my body",
                "payload_encoding": "string"}
        resp = requests.post(url, json=body, auth=self.RABBIT_AUTH)
        return resp.json()
