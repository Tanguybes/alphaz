from flask import request
from typing import *

def get_token_from_request():
    token = None
    # Get token from authorization bearer
    auth = request.headers.get("Authorization", None)
    if auth is not None:
        if "bearer" in auth.lower():
            parts = auth.split()
            if len(parts) > 1:
                token = parts[1]

    # Token from get have priority if present
    token_from_get = request.args.get("token", None)
    if token_from_get is not None:
        token = token_from_get

    # Token from post
    dataPost = request.get_json()
    if dataPost is not None and "token" in dataPost:
        token = dataPost["token"]
    return token

class Requests:
    def get_token(self):
        return get_token_from_request()

    def get_gets(self) -> Dict[str, object]:
        """returns GET value as a dict.

        Returns:
            Dict[str, object]: [description]
        """
        return {x: y for x, y in request.args.items()}

    def get_uuid(self):
        posts = request.get_json()
        if posts is None:
            posts = {}
        request_uuid = request.full_path + "&" + "&".join("%s=%s" % (x, y) for x, y in posts.items())
        return request_uuid