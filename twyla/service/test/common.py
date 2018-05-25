
_content_schema = {
    '$schema': 'http://json-schema.org/draft-06/schema#',
    'title': 'Request',
    'description': 'A test request',
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'text': {'type': 'string'}
    }
}

_content_schema_set = {
    'a-domain.an-event': _content_schema,
    'other-domain.to-be-listened': _content_schema,
    'another-event': 'another-event-content-schema'
}

_context_schema = {
    '$schema': 'http://json-schema.org/draft-06/schema#',
    'title': 'ShopContext',
    'description': 'A test context',
    'type': 'object',
    'properties': {
        'channel': {'type': 'string'},
        'channel_user': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'id': {'type': 'number'}
            }
        }
    }
}


def schemata_fixtures():
    return _content_schema_set, _context_schema

QUEUE_CONFIG = {'amqp_host': 'localhost',
                'amqp_port': '5672',
                'amqp_user': 'guest',
                'amqp_pass': 'guest',
                'amqp_vhost': '/'}
