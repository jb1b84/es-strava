from crypt import methods
from distutils.log import debug
import logging
import os

from flask import Flask, request

app = Flask(__name__)


"""
Strava API: new user signup flow & event hook
"""


@app.route("/info")
def hello_world():
    # placeholder for app info & verification
    logging.debug("info route hit")
    name = os.environ.get("NAME", "World")
    return "Hello {}!".format(name)


@app.route('/', methods=['GET'])
def signup():
    # handle get for webhook callback / token handoff
    verify_token = 'notatoken'

    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if (mode and token):
        if (mode == 'subscribe' and token == verify_token):
            logging.info('webhook verified')
            return {"hub.challenge": challenge}
        else:
            return "unknown mode or token", 403
    else:
        return "unsupported method", 403


@app.route('/', methods=['POST'])
def new_event():
    logging.debug("POST request received")
    # handle post for event received
    logging.debug("Data: ", request.data)
    logging.debug("Form: ", request.form)
    logging.debug("JSON: ", request.json)

    return "message received"


"""
gcloud pub/sub placeholder
"""


def subscribe():
    return "Subscribe route"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
