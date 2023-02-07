import os
import jwt
import json
import datetime
import requests
from flask import Flask
from flask import request
from flask import jsonify
app = Flask(__name__)

# TESSERACT_JWT_SECRET from /etc/systemd/system/tesseract-olap.service
JWT_SECRET = 'FVheSkHMB7MqJCTdFmKJXnNlKw4qKC54'
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_MINUTES = 30

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def custom_endpoint(path):

    payload = {
    'auth_level': 1,
    'sub': '4849e49d-09d7-26ed-0787-4e9734deeabc', # "id" in mexico_cms.users postgres database
    'status': 'valid',
    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXP_DELTA_MINUTES)
    }

    jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)

    headers = {
    "x-tesseract-jwt-token": jwt_token.decode('utf-8')
    }

    try:
        BASE_URL = 'http://localhost:7777/'
        r = requests.get(BASE_URL + request.url.split('tesseract/custom/')[1], headers=headers)
        data = r.json()
        for ele in data['data']:
            del ele['Trade Value']

        return jsonify(data)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })
