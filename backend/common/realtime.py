import json

from rest_framework.renderers import JSONRenderer


def json_safe(value):
    """Convert serializer data to plain JSON types before sending through Redis/msgpack."""
    return json.loads(JSONRenderer().render(value).decode("utf-8"))
