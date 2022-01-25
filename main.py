from tokenize import Token
import google.cloud.logging
import json
import logging
import os
import requests

from dotenv import load_dotenv
from flask import Flask, request

app = Flask(__name__)

load_dotenv()

"""
Strava API: new user signup flow & event hook
"""


@app.route("/info")
def hello_world():
    setup_logging()
    # placeholder for app info & verification

    name = os.environ.get("NAME", "World")
    return "Hello {}!".format(name)


@app.route('/', methods=['GET'])
def signup():
    setup_logging()
    # handle get for webhook callback / token handoff
    verify_token = os.environ.get('VERIFY_TOKEN')

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
    logging.info("JSON: {}".format(request.json))
    event = request.json

    if event['aspect_type'] == 'create':
        # this is a new event creation so let's process it
        print("New {} event received for user {} with obj id {}".format(
              event['object_type'], event['owner_id'], event['object_id']))

        # retrieve the event from api
    else:
        # nothing to do here
        logging.info('received event with unknown aspect type {}'.format(
            event['aspect_type']))

    return 200


@app.route('/fetch/<int:object_id>')
def fetch_object(object_id):
    # connection data to populate from local storage & refresh later
    conn = {
        "token_type": "Bearer",
        "expires_at": 123,
        "expires_in": 123,
        "refresh_token": "re123",
        "access_token": "acc123",
        "athlete": {
            "id": 49404045
        }
    }

    # api details
    strava_api = 'https://www.strava.com/api/v3'
    bearer_token = os.environ.get('TOKEN')
    headers = {"Authorization": "Bearer {}".format(bearer_token)}

    url = '{}/activities/{}'.format(strava_api, object_id)
    print(url)

    r = requests.get(
        url,
        headers=headers
    ).json()

    if r.status_code == 200:
        # pass on to processing
        logging.info(r)
        return "activity fetched"
    else:
        # handle errors
        logging.error(r)

        # handle token refresh, need to distinguish these two errors somehow
        return "we encountered an error"


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
    env = os.environ.get('env')
    if (env != 'local'):
        # don't setup gcloud stuff in local dev
        client = google.cloud.logging.Client()
        client.setup_logging()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
