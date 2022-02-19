#!/usr/bin/python

import os

import google.auth
from google.auth import exceptions
from google.auth import transport
from google.oauth2 import id_token
import google_auth_httplib2

import google.auth.transport.requests
import requests

# For googleID token using gcloud:
# "aud": "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com",
# "iss": "accounts.google.com",
#credentials, project = google.auth.default()
#g_request = google.auth.transport.requests.Request()
#credentials.refresh(g_request)
#idt = credentials.id_token
#print 'id_token: ' + idt
#headers = {'Authorization': 'Bearer ' + idt }


idt = "YOUR_TEST_IAP_TOKEN_HERE"
headers = {'X-Goog-Iap-Jwt-Assertion': idt }

r = requests.get('http://localhost:10000/todos', headers=headers)
print(r.text)
