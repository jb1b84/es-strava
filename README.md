# Strava <> Elasticsearch
A simple integration that implements:
* OAuth handshake with Strava
* Webhook that receives new user activity from Strava
* Syncs athletes and their activity in Elasticsearch
* Backfill script to add historical data from a CSV
* Flask API acts as intermediary
* Intended for Google Cloud Run usage


TODO:
- [ ] Abstract out ES & Strava bits into separate libs
- [ ] Flask routing refactor
- [ ] Add logging to Flask hook for all routes
- [ ] Implement delete activity and aspect type
- [ ] cleanup
  