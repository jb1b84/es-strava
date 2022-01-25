from crypt import methods
from distutils.log import debug
import os

from flask import Flask, request

app = Flask(__name__)


@app.route("/")
def hello_world():
    print('test flow')
    name = os.environ.get("NAME", "World")
    return "Hello {}!".format(name)


"""
Strava API: new user signup flow & event hook
"""


@app.route('/webhook', methods=['GET'])
def signup():
    # handle get for webhook callback / token handoff

    return "thanks for signing up"


@app.route('/webhook', methods=['POST'])
def new_event():
    # handle post for event received
    print("Data: ", request.data)
    print("Form: ", request.form)
    print("JSON: ", request.json)

    return "message received"


"""
gcloud pub/sub placeholder
"""


def subscribe():
    return "Subscribe route"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
