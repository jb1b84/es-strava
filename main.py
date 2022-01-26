from asyncore import write
import google.cloud.logging
import json
import logging
import os
import requests
import time

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
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
        code_exchange(code)
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
        fetch_object(event['object_id'], event['owner_id'])
    else:
        # nothing to do here
        logging.info('received event with unknown aspect type {}'.format(
            event['aspect_type']))

    return "event received"


@app.route('/athlete-profile/<int:athlete_id>')
def get_athlete_profile(athlete_id):
    athlete = get_athlete(athlete_id)

    # api details
    strava_api = 'https://www.strava.com/api/v3'
    bearer_token = athlete['details']['access_token']
    headers = {"Authorization": "Bearer {}".format(bearer_token)}

    url = '{}/athlete'.format(strava_api)
    r = requests.get(url, headers=headers)
    print(r.json())

    return "test"


@app.route('/code-exchange/<code>')
def code_exchange(code):
    # api details
    strava_api = 'https://www.strava.com/api/v3'

    url = '{}/oauth/token'.format(strava_api)
    r = requests.post(url, data={
        "client_id": os.environ.get('STRAVA_CLIENT_ID'),
        "client_secret": os.environ.get('STRAVA_CLIENT_SECRET'),
        "grant_type": "authorization_code",
        "code": code
    })

    res = r.json()
    print(res)

    if r.status_code == 200:
        athlete_id = res['athlete']['id']
        athlete_doc = {
            "athlete_id": athlete_id,
            "details": res
        }

        write_doc('strava-athletes', athlete_id, athlete_doc)

    return "hello"


@app.route('/refresh-token/<int:athlete_id>')
def refresh_athlete_token(athlete_id):
    athlete = get_athlete(athlete_id)

    # api details
    strava_api = 'https://www.strava.com/api/v3'

    url = '{}/oauth/token'.format(strava_api)
    r = requests.post(url, data={
        "client_id": os.environ.get('STRAVA_CLIENT_ID'),
        "client_secret": os.environ.get('STRAVA_CLIENT_SECRET'),
        "grant_type": "refresh_token",
        "refresh_token": athlete['details']['refresh_token']
    })

    res = r.json()

    athlete_doc = {
        "athlete_id": athlete_id,
        "details": res
    }

    write_doc('strava-athletes', athlete_id, athlete_doc)

    return "token updated"


@app.route('/fetch/<int:object_id>/<int:athlete_id>')
def fetch_object(object_id, athlete_id):
    athlete = get_athlete(athlete_id)

    # api details
    strava_api = 'https://www.strava.com/api/v3'
    bearer_token = athlete['details']['access_token']
    headers = {"Authorization": "Bearer {}".format(bearer_token)}

    url = '{}/activities/{}/'.format(strava_api, object_id)

    r = requests.get(
        url,
        headers=headers
    )
    res = r.json()

    if r.status_code == 200:
        # pass on to processing
        print(res)
        activity_id = res['id']
        write_doc('strava-activity', activity_id, res)
        return "activity fetched"
    elif r.status_code == 401:
        # token has probably expired
        print('Status code {} {}'.format(r.status_code, res['message']))
        print(res)

        # let's get a new one
        refresh_athlete_token(athlete_id)

        # TODO: retry once
        return "Authorization error, fetching new token"
    else:
        # handle errors
        logging.error(r)

        # don't retry since we're unsure what went wrong
        return "we encountered an error {}: {}".format(r.status_code, res['message'])


"""
Elasticsearch api
"""


def connect_elasticsearch():
    es = Elasticsearch(
        cloud_id=os.environ.get('ES_CLOUD_ID'),
        api_key=os.environ.get('ES_STRAVA_KEY'),
        use_ssl=True,
        verify_certs=True
    )

    # get cluster info
    resp = es.info()
    print(resp)

    return es


@app.route('/athlete/<int:athlete_id>', methods=['GET'])
def get_athlete(athlete_id):
    res = es.get(index="strava-athletes", id=athlete_id)

    # check on the access token while we're here
    expiry = res['_source']['details']['expires_at']
    minutes_left = (expiry - time.time()) / 60
    print('Token expires in {} minutes'.format(
        minutes_left))

    return res['_source']


@app.route('/athlete/<int:athlete_id>', methods=['POST'])
def set_athlete(athlete_id):
    athlete_data = request.json

    athlete_doc = {
        "athlete_id": athlete_id,
        "details": athlete_data
    }

    res = write_doc('strava-athletes', athlete_id, athlete_doc)

    return res


def write_doc(index, id, doc, refresh=True):
    res = es.index(index=index,
                   id=id, document=doc)
    print(res['result'])

    if refresh:
        es.indices.refresh(index=index)

    return


# sloppy global but works for now
es = connect_elasticsearch()

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
