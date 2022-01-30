import csv
import os
import requests

from queue import Queue

"""
1) Build queue
2) Open CSV
3) Add activity_id for each row to queue
4) Check if activity already exists in ES
5) If not, fetch details from Strava and sync in ES
"""

q = Queue()

# Open CSV
with open('./csv/activities.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count != 0:
            q.put(row[0])
        line_count += 1


print('Processed {} rows'.format(line_count))

athlete_id = 49404045
base_url = 'http://127.0.0.1:5000'
i = 0

while not q.empty():
    activity_id = q.get()

    # to prevent rate limiting, check if doc exists in ES first
    check_url = '{}/{}/{}'.format(base_url, 'activity', activity_id)
    doc = requests.get(check_url)
    if doc:
        pass
    else:
        # need to sync
        sync_url = '{}/{}/{}/{}'.format(base_url,
                                        'sync', activity_id, athlete_id)
        requests.get(sync_url)
        i += 1


print('Total not found: {}'.format(i))
