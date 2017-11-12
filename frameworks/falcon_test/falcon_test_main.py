# things.py

# Let's get this party started!
import json

import falcon

# setup connection to mongo
from pymongo import MongoClient

client = MongoClient()
db = client.test_database
foos = db.foos  # collection of foo objects
if not foos.count():
    foos.insert_one({'foo': 'bar', 'bar': 'foo'})


# Falcon follows the REST architectural style, meaning (among
# other things) that you think in terms of resources and state
# transitions, which map to HTTP verbs.
class TestResource(object):
    def on_get(self, req, resp):
        """Handles GET requests"""
        resp.body = json.dumps({'foo': 'bar'})


class ModelTestResource(object):
    def on_get(self, req, resp):
        """Handles GET requests"""
        foo = foos.find_one({'foo': 'bar'})
        resp.body = json.dumps({'foo': foo['foo'], 'bar': foo['bar']})


# falcon.API instances are callable WSGI apps
app = falcon.API()

# Resources are represented by long-lived class instances
json_test = TestResource()
model_test = ModelTestResource()

# things will handle all requests to the '/things' URL path
app.add_route('/', json_test)
app.add_route('/model', model_test)
