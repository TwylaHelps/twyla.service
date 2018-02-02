import json
import datetime
import uuid

from json import JSONEncoder


def twyla_default(self, obj):
    # Builtin classes can not be monkey-patched
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    # NOTE: this could be monkey patched UUID.__json__ = UUID.__str__
    # actually.. a decision has to be made whether monkey-patching or adding
    # here is the way to go for 3rd-party classes/modules
    elif isinstance(obj, uuid.UUID):
        return obj.__str__()
    else:
        # __methods__ are reserved for builtin protocols.. this is a drop in
        # replacement of a future __json__ protocol as writing default
        # functions or JSONEncoders for all things is annoying.
        return getattr(obj.__class__, '__json__', twyla_default.default)(obj)


twyla_default.default = JSONEncoder().default
JSONEncoder.default = twyla_default


def dumps(obj):
    return json.dumps(obj)
