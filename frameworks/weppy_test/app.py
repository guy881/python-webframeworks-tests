import json

from weppy import App
from weppy.orm import Database, Model, Field
from weppy.tools import service
from pymongo import MongoClient


class ExampleModel(Model):
    foo = Field.string()
    bar = Field.string()


app = App(__name__)
db = Database(app, auto_migrate=True)
db.define_models(ExampleModel)
app.pipeline = [db.pipe]

client = MongoClient()
db = client.test_database
foos = db.foos  # collection of foo objects


@app.route("/")
@service.json
def simple_json():
    return {'foo': 'bar'}


@app.route("/model")
@service.json
def model():
    example = ExampleModel.get(foo='bar')
    return {'foo': example.foo, 'bar': example.bar}


@app.route("/model-mongo")
@service.json
def model_mongo():
    foo = foos.find_one({'foo': 'bar'})
    return json.dumps({'foo': foo['foo'], 'bar': foo['bar']})


@app.command('setup')
def setup():
    # create the ExampleModel object
    example = ExampleModel.create(
        foo="bar",
        bar="foo",
    )
    db.commit()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=False)
