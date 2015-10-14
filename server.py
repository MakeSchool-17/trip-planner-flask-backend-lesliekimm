from flask import Flask, request, make_response, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient
from bson.objectid import ObjectId
from utils.mongo_json_encoder import JSONEncoder
from functools import wraps
from bcyrpt import hashpw, gensalt

# basic setup
app = Flask(__name__)                       # create flask instance
mongo = MongoClient('localhost', 27017)     # establish connection to local MDB
app.db = mongo.develop_database             # specify DB to store data
# create instance of flask_restful API to add diff endpts to this API
# provides specific format for defining endpts fro diff resources in our app
api = Api(app)


# check_auth method decides whether user provided valid credentials
def check_auth(username, password):
    # THIS IS DUMMY IMPLEMENTATION - REPLACE
    hashed_pw = hashpw(password, gensalt(log_rounds=12))
    # if hashed_pw == stored hashed pw
    return username == 'admin' and password == 'secret'


# defines a wrapper that will check authentication header of an incoming request
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # first reads auth header by accessing request.authorization
        auth = request.authorization
        # checks if header was provided
        # if header provided, passes deatils to check_auth method
        # check_auth method decides whether user provided valid credentials
        # if auth not successful, return 401 response
        if not auth or not check_auth(auth.username, auth.password):
            message = {'error': 'Basic Auth Required.'}
            resp = jsonify(message)
            resp.status_code = 401
            return resp

        # if auth successful, wrapped function will be called as usual
        return f(*args, **kwargs)
    return decorated


# implement REST Resource
# most apps will defined one resource for each entity that can be stored in app
# resource implements one method for each HTTP verb that is supported
class Trip(Resource):
    # invoked to create a new instance of MyObject on the server
    # client that calls this endpt provides a JSON body as part of HTTP request
    def post(self):
        # access JSON that client provides
        trip = request.json
        # access collection where we will store new object
        # typically, one collection per entity
        trip_collection = app.db.trips
        # insert JSON document into collection
        result = trip_collection.insert_one(trip)   # inserting doc
        # retrieve the result of inserting doc & use to fetch inserted doc
        # from the collection using find_one - takes a dictionary that
        # describes filter criteria for our dogs (i.e. _id) the _id field is
        # auto maintained by MongoDB & stores unique ID for each doc stored
        # we wrap result.inserted_id into TripId type - not a string!
        my_trip = trip_collection.find_one(
            {'_id': ObjectId(result.inserted_id)})
        # return selected doc to client
        return my_trip

    # retrieve a Trip instance
    def get(self, trip_id=None):
        # reference my_collection to select the doc that client is trying to
        # access
        trip_collection = app.db.trips
        # build a query based on my_objet_id that we recieved as poart of
        # client's request
        trip = trip_collection.find_one({'_id': ObjectId(trip_id)})

        # if doc w/ provided id isn't found, return a 404 statement, else
        # return doc to client
        if trip is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            return trip

    # update a Trip
    def put(self, trip_id):
        trip_update = request.json
        trip_collection = app.db.trips

        result = trip_collection.update_one({'_id': ObjectId(trip_id)},
                                            {'$set': trip_update})
        updated = trip_collection.find_one({'_id': ObjectId(trip_id)})

        return updated

    # delete a Trip
    def delete(self, trip_id):
        trip_collection = app.db.trips

        result = trip_collection.delete_one({'_id': ObjectId(trip_id)})
        deleted_trip = trip_collection.find_one({'_id': ObjectId(trip_id)})

        if deleted_trip is not None:
            response = jsonify(data=deleted_trip)
            response.status_code = 404
            return response
        else:
            return deleted_trip


class User(Resource):
    def post(self):
        user = request.json
        user_collection = app.db.users
        result = user_collection.insert_one(user)   # inserting doc
        my_user = user_collection.find_one(
            {'_id': ObjectId(result.inserted_id)})

        return my_user

    @requires_auth
    def get(self):
        pass

# add REST resource to API by mapping btw routes and resources
# a route defines a URL that can be called by a client app
# first param is resource we want to map to a specific URL
# next are collection of endpts
api.add_resource(Trip, '/trip/', '/trip/<string:trip_id>')
api.add_resource(User, '/user/', '/user/<string:user_id>')

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
