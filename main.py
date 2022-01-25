from cmath import log
from crypt import methods
from distutils.log import debug
import google.cloud.logging
import logging
import os

from flask import Flask, request

app = Flask(__name__)


"""
Strava API: new user signup flow & event hook
"""


@app.route("/info")
def hello_world():
    setup_logging()
    # placeholder for app info & verification
    logging.warning("info route hit")
    name = os.environ.get("NAME", "World")
    return "Hello {}!".format(name)


@app.route('/', methods=['GET'])
def signup():
    setup_logging()
    # handle get for webhook callback / token handoff
    verify_token = 'JSON281'

    # check for access code
    code = request.args.get('code')
    if (code):
        # this is a new auth attempt
        scope = request.args.get('scope')
        logging.warning('code: {}, scope: {}'.format(code, scope))
        # need to exchange the auth code and scope for a refresh token
        # doing this manually in postman for now though so just bounce out
        return "thanks for the code"

    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    logging.warning('mode: {}, token: {}'.format(mode, token))

    if (mode and token):
        if (mode == 'subscribe' and token == verify_token):
            logging.info('webhook verified')
            return {"hub.challenge": challenge}
        else:
            logging.warning("unknown mode or token used")
            return "unknown mode or token", 403
    else:
        logging.warning("unsupported method passed to webhook")
        return "unsupported method", 403


@app.route('/', methods=['POST'])
def new_event():
    setup_logging()
    logging.warning("POST request received")
    # handle post for event received
    logging.warning("Data: ", request.data)
    logging.warning("Form: ", request.form)
    logging.warning("JSON: ", request.json)

    return "message received"


"""
gcloud pub/sub placeholder
"""


def subscribe():
    return "Subscribe route"


"""
Utils
"""


def setup_logging():
    # logging client setup
    # TODO: move to global hook
    client = google.cloud.logging.Client()
    client.setup_logging()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
