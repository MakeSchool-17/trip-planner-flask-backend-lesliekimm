from flask import Flask, request, make_response, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient
from bson.objectid import ObjectId
from utils.mongo_json_encoder import JSONEncoder
from functools import wraps
import bcrypt

# basic setup
app = Flask(__name__)                       # create flask instance
mongo = MongoClient('localhost', 27017)     # establish connection to local MDB
app.db = mongo.develop_database             # specify DB to store data
api = Api(app)                              # create flask_RESTful API instance
app.bcrypt_rounds = 12                      # config work factor for fast tests
trips = app.db.trips                        # collection to store trip objects
users = app.db.users                        # collection to store users objects


# check_auth method decides whether user provided valid credentials
def check_auth(username, password):
    user = users.find_one({'username': username})   # retrieve correct User
    encoded_pw = password.encode('utf-8')           # encode password

    if user is None:
        return False                        # if no User, return False
    else:                                   # otherwise, authenticate
        if bcrypt.hashpw(encoded_pw, user['password']) == user['password']:
            return True                     # return True if passwords match
        else:
            return False                    # otherwise return False


# decorator function that checks authenticaiton header of an incoming request
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # returns Authorization object (username and password)
        auth = request.authorization        # read auth header
        # check_auth w/ UN and PW provided and if False returned or no header
        # provided, return 401
        if not auth or not check_auth(auth.username, auth.password):
            message = {'error': 'Basic Auth Required.'}
            resp = jsonify(message)         # insert error msg to return
            resp.status_code = 401          # set status to 401
            return resp
        return f(*args, **kwargs)           # if auth success, call wrap func
    return decorated


# implement REST resources
# Trip class can POST (create new Trip w/ waypoints), GET (return coll of Trips
# or one Trip), PUT (update a coll of Trips or one Trip) and DELETE (delete a
# Trip w/ waypoints)
class Trip(Resource):
    # POSt creates a new Trip instance w/ waypoints - requires authentication
    # and must send in header and JSON doc
    @requires_auth
    def post(self):
        trip = request.json                         # access JSON passed in
        result = trips.insert_one(trip)             # insert JSON doc in coll
        # retrieve result & fetch inserted doc
        my_trip = trips.find_one({'_id': ObjectId(result.inserted_id)})
        return my_trip                              # return doc to client

    # GET retrieves a coll of Trips of specific Trip if trip_id specified
    @requires_auth
    def get(self, trip_id=None):
        auth = request.authorization
        # if no trip_id specified, return trips collection
        if trip_id is None:
            found_trips = trips.find({'username': auth.username})
            trips_to_return = list(found_trips)
            return trips_to_return
        # otherwise, return specified trip
        else:
            # access specified trip_id passed in
            trip = trips.find_one({'_id': ObjectId(trip_id)})

            # if trip isn't found, return 404 error code
            if trip is None:
                response = jsonify(data=[])         # set data to empty array
                response.status_code = 404          # set status_code to 404
                return response
            # otherwise, return trip
            else:
                return trip

    # PUT updates a collection of Trips or specific Trip if trip_id specified
    @requires_auth
    def put(self, trip_id=None):
        trip_update = request.json                  # access JSON passed in
        # find the trip_id passed in and update using $set
        trips.update_one({'_id': ObjectId(trip_id)},
                                   {'$set': trip_update})
        # retrieve the updated Trip
        updated = trips.find_one({'_id': ObjectId(trip_id)})
        return updated                              # return updated Trip doc

    # delete a Trip
    @requires_auth
    def delete(self, trip_id):
        # delete Trip of specified trip_id
        trips.delete_one({'_id': ObjectId(trip_id)})
        # retrieve delted Trip doc
        deleted_trip = trips.find_one({'_id': ObjectId(trip_id)})

        # return 404 if deleted_trip is not None, else return deleted_trip
        if deleted_trip is not None:
            response = jsonify(data=deleted_trip)   # set data to deleted_trip
            response.status_code = 404              # set response to 404
            return response                         # return response
        else:
            return deleted_trip                     # return deleted_trip


class User(Resource):
    def post(self):
        user = request.json                             # access JSON passed in

        if (user['username'] is None or user['password'] is None):
            message = {'error': 'Request requires username and password.'}
            resp = jsonify(message)                 # insert error msg
            resp.status_code = 400                  # set status to 401
            return resp

        my_user = users.find_one({'username': user['username']})

        if my_user is not None:
            message = {'error': 'Username already in use'}
            resp = jsonify(message)
            resp.satus_code = 400
            return resp
        else:
            encoded_pw = user['password'].encode('utf-8')   # encode password
            hashed_pw = bcrypt.hashpw(encoded_pw,           # hash password
                                      bcrypt.gensalt(app.bcrypt_rounds))
            user['password'] = hashed_pw                    # update password
            users.insert_one(user)                          # insert doc

    # GET retrieves all Trips for a user and requires authentication
    @requires_auth
    def get(self):
        resp = jsonify(message=[])          # msg indicates auth went through
        resp.status_code = 200              # set status to 200
        return resp                         # return resp

# add REST resources to API by mapping routes and resources
api.add_resource(Trip, '/trips/', '/trips/<string:trip_id>')
api.add_resource(User, '/users/', '/users/<string:user_id>')


# provide a custom JSON serializer for flask_restful
@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(JSONEncoder().encode(data), code)
    resp.headers.extend(headers or {})
    return resp

if __name__ == '__main__':
    # turn this on in debug mode to get detailed information about request
    # related exceptions: http://flask.pocoo.org/docs/0.10/config/
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(debug=True)
