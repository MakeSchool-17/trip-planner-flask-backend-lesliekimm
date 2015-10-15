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
trip_collection = app.db.trips              # collection to store obj
user_collection = app.db.users              # collection to store users


# check_auth method decides whether user provided valid credentials
def check_auth(username, password):
    user_collection = app.db.users          # access collection of Users
    # retrieve User with username provided
    user = user_collection.find_one({'username': username})

    # if there is no User, return False, otherwise check credentials
    if user is None:
        return False
    else:
        encoded_pw = password.encode('utf-8')   # encode password provided

        # compare encoded password with hashed password
        if bcrypt.hashpw(encoded_pw, user['password']) == user['password']:
            return True                     # return True if they match
        else:
            return False                    # otherwise return False


# define wrapper that checks authentication header of an incoming request
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization        # read auth header
        # check_auth with username and password provided and if False
        # returned or no header provided, return 401
        if not auth or not check_auth(auth.username, auth.password):
            message = {'error': 'Basic Auth Required.'}
            resp = jsonify(message)         # insert error msg to return
            resp.status_code = 401          # set status to 401
            return resp                     # return resp
        return f(*args, **kwargs)   # if auth success, wrapped func called
    return decorated


# implement REST resources
# Trip class can POST (create a new Trip with waypoints), GET (return a
# collection of Trips or one Trip), PUT (update a collection of Trips or one
# Trip) and DELETE (delete a Trip with waypoints)
class Trip(Resource):
    # POST creates a new Trip instance with waypoints - must sent JSON doc
    def post(self):
        trip = request.json                 # access JSON passed in
        result = trip_collection.insert_one(trip)   # insert JSON doc in coll
        my_trip = trip_collection.find_one(         # retrieve result &
            {'_id': ObjectId(result.inserted_id)})  # fetch inserted doc
        return my_trip                      # return selected doc to client

    # GET retrieves a collection of Trips or specific Trip if trip_id specified
    def get(self, trip_id=None):
        # access coll if no trip_id specificed, or specific Trip if provided
        trip = trip_collection.find_one({'_id': ObjectId(trip_id)})

        # return 404 if trip_id Trip isn't found, or Trip if found
        if trip is None:
            response = jsonify(data=[])     # set data to return to empty array
            response.status_code = 404      # set status_code to 404
            return response                 # return response
        else:
            return trip                     # return trip if found

    # PUT updates a collection of Trips or specific Trip if trip_id specified
    def put(self, trip_id=None):
        trip_update = request.json          # access JSON passed in
        # find the trip_id passed in and update using $set
        trip_collection.update_one({'_id': ObjectId(trip_id)},
                                   {'$set': trip_update})
        # retrieve the updated Trip
        updated = trip_collection.find_one({'_id': ObjectId(trip_id)})
        return updated                      # return updated Trip doc

    # delete a Trip
    def delete(self, trip_id):
        # delete Trip of specified trip_id
        trip_collection.delete_one({'_id': ObjectId(trip_id)})
        # retrieve delted Trip doc
        deleted_trip = trip_collection.find_one({'_id': ObjectId(trip_id)})

        # return 404 if deleted_trip is not None, else return deleted_trip
        if deleted_trip is not None:
            response = jsonify(data=deleted_trip)   # set data to deleted_trip
            response.status_code = 404              # set response to 404
            return response                         # return response
        else:
            return deleted_trip                     # return deleted_trip


# User class can POST (create a new user which will store username and hashed
# password) and GET (which requires authentication to retrieve all Trips for
# a specific User)
class User(Resource):
    # POST creates a new User instance & returns ID - must sent JSON doc
    def post(self):
        user = request.json                     # request json doc
        encoded_pw = user['password'].encode('utf-8')   # encode password
        hashed_pw = bcrypt.hashpw(encoded_pw,           # hash password
                                  bcrypt.gensalt(app.bcrypt_rounds))
        user['password'] = hashed_pw                    # update pasword
        result = user_collection.insert_one(user)       # inserting doc
        my_user = user_collection.find_one(             # retrieve result &
            {'_id': ObjectId(result.inserted_id)})      # fetch inserted doc
        return my_user['_id']                           # return user's id

    # GET retrieves all Trips for a user and requires authentication
    @requires_auth
    def get(self):
        resp = jsonify(message=[])          # msg indicates auth went through
        resp.status_code = 200              # set status to 200
        return resp                         # return resp


# add REST resources to API by mapping between routes and resources
api.add_resource(Trip, '/trips/', '/trips/<string:trip_id>')
api.add_resource(User, '/users/', '/users/<string:user_id>')


# provide a custom JSON serializer for flaks_restful
@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(JSONEncoder().encode(data), code)
    resp.headers.extend(headers or {})
    return resp

if __name__ == '__main__':
    # Turn this on in debug mode to get detailled information about request
    # related exceptions: http://flask.pocoo.org/docs/0.10/config/
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(debug=True)
