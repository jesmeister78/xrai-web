#!/bin/sh
export FLASK_APP=./www/index.py
pipenv run flask --debug run -h 0.0.0.0 -p 5001 
# pipenv run flask --debug run -h 0.0.0.0 -p 5001 --cert=cert.pem --key=key.pem