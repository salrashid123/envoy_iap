from flask import Flask, request, abort
from flask_restplus import Api, Resource, fields
from functools import wraps

import logging
import pprint
import base64

from google.oauth2 import id_token
from google.auth import transport
import google.auth.transport.requests

app = Flask(__name__)
app.config['DEBUG'] = True

#AUTHORIZATION_HEADER = 'X-Goog-Iap-Jwt-Assertion'
AUTHORIZATION_HEADER = 'Authorization'

authorizations = {}

api = Api(app, version='1.0', title='TodoMVC API',
    description='A simple TodoMVC API'
)

def auth_required(f):
    @wraps(f)
    def check_authorization(*args, **kwargs):
        if request.headers.get(AUTHORIZATION_HEADER):
            token = request.headers.get(AUTHORIZATION_HEADER)            
            # Do JWT validation for IAP here in a similar way to the check below for google_id_token
            # note, IAP uses EC so you need to validate the JWTs for that scheme
            # you may need to use a library which does ES256 validation using
            # JWK like https://github.com/mpdavis/python-jose 
            # ...the following is for GoogleIDToken and uses RS256...i added this in just as a
            # middleware example
            token = token.split(' ')[1]
            r = google.auth.transport.requests.Request()
            id_token.verify_token(token,r)            
        else:
            api.abort(401, AUTHORIZATION_HEADER + ' header required')
        return f(*args, **kwargs)
    return check_authorization

ns = api.namespace('todos', description='TODO operations')

todo = api.model('Todo', {
    'id': fields.Integer(readOnly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details')
})

class TodoDAO(object):
    def __init__(self):
        self.todos = {}

    def get(self, id):
        if (id in self.todos):        
           return self.todos[id]
        api.abort(404, "Todo {} doesn't exist".format(id))

    def create(self,data):
        id = data['id']
        if (id in self.todos):
            api.abort(409, "Todo {} already exists".format(str(id)))
        self.todos[id] = data
        return data

    def update(self, id, data):
        if (id in self.todos):
          self.todo[id] = data
          return data
        api.abort(404, "Todo {} doesn't exist".format(id))

    def delete(self, id):
        if (id in self.todos):
          del self.todos[id]
          return
        api.abort(404, "Todo {} doesn't exist".format(id))


DAO = TodoDAO()

@ns.route('')
class TodoList(Resource):
    @ns.doc('list_todos')
    @ns.marshal_with(todo, envelope='items')
    #@auth_required
    def get(self):
        '''List all resources'''        
        return list(DAO.todos.values())

    @ns.doc('create_todo')
    @ns.marshal_with(todo, code=201)
    #@auth_required
    def post(self):
        '''Create a given resource'''        
        return DAO.create(api.payload), 201

@ns.route('/<int:id>')
class Todo(Resource):
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    @ns.response(404, 'Todo not found')
    #@auth_required
    def get(self, id):
        '''Fetch a given resource'''
        return DAO.get(id)

    @ns.doc('delete_todo')
    @ns.response(204, 'Todo deleted')
    #@auth_required
    def delete(self, id):
        '''Delete a given resource'''
        DAO.delete(id)
        return '', 204

    @ns.expect(todo)
    @ns.response(404, 'Todo not found')
    @ns.marshal_with(todo)
    #@auth_required
    def put(self, id):
        '''Update a given resource'''        
        return DAO.update(id, api.payload)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50051, debug=True,  threaded=True)
