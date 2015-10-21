import server
import unittest
import json
from pymongo import MongoClient
from base64 import b64encode


# unit test for server.py classes
class FlaskTestCase(unittest.TestCase):
    # set up before each test case
    def setUp(self):
        self.app = server.app.test_client()         # ref server's Flask app
        server.app.config['TESTING'] = True         # run in testing mode
        mongo = MongoClient('localhost', 27017)     # establish conn to MDB
        db = mongo.test_database                    # inject test DB into app
        server.app.db = db                          # specify DB to store data
        db.drop_collection('trips')                 # drop trips collection
        db.drop_collection('users')                 # drop users collection

    # test Trip and User POST method - includes authentication
    def test_post(self):
        # create User object
        user_response = self.app.post('/users/', data=json.dumps(dict(
            username='lesliekimm', password='password123')),
            content_type='application/json')
        user_id = json.loads(user_response.data.decode())       # get user_id

        self.assertEqual(user_response.status_code, 200)
        assert 'application/json' in user_response.content_type

        # create headers by encoding un:pw and encoding using b64
        creds_string = "{0}:{1}".format('lesliekimm', 'password123')
        cred_encoded = creds_string.encode('utf-8')
        cred_b64encoded = b64encode(cred_encoded).decode()
        # create headers with properly encoded us:pw
        headers = {'Authorization': 'Basic ' + cred_b64encoded}

        # create Trip object w/ name, waypoints and user_id
        response = self.app.post('/trips/', headers=headers, data=json.dumps(
            dict(name='San Francisco', waypoints=[], uID=user_id)),
            content_type='application/json')
        responseJSON = json.loads(response.data.decode())       # decode doc

        # perform assertion tests
        self.assertEqual(response.status_code, 200)
        assert 'application/json' in response.content_type
        assert 'San Francisco' in responseJSON['name']
        self.assertEqual(0, len(responseJSON['waypoints']))

    # test Trip GET method for an existing trip_id and GET for User (auth)
    def test_get(self):
        # create User object
        user_response = self.app.post('/users/', data=json.dumps(dict(
            username='lkim', password='password000')),
            content_type='application/json')
        user_id = json.loads(user_response.data.decode())       # get user_id

        # create headers by encoding un:pw and encoding using b64
        creds_string = "{0}:{1}".format('lkim', 'password000')
        cred_encoded = creds_string.encode('utf-8')
        cred_b64encoded = b64encode(cred_encoded).decode()
        # create headers with properly encoded us:pw
        headers = {'Authorization': 'Basic ' + cred_b64encoded}

        # GET User which tests authentication
        get_response = self.app.get('/users/', headers=headers)

        # perform assertion tests
        self.assertEqual(get_response.status_code, 200)

        # create Trip object w/ name, waypoints and user_id
        response = self.app.post('/trips/', headers=headers, data=json.dumps(
            dict(name='Cross Country', waypoints=[], uID=user_id)),
            content_type='application/json')
        responseJSON = json.loads(response.data.decode())       # decode doc
        trip_id = responseJSON['_id']                           # get trip id

        # GET the specific trip associated with retrieved id and decode
        get_response = self.app.get('/trips/'+trip_id)
        get_responseJSON = json.loads(get_response.data.decode())

        # perform assertion tests
        self.assertEqual(get_response.status_code, 200)
        assert 'Cross Country' in responseJSON['name']
        assert trip_id in responseJSON['_id']
        self.assertEqual(0, len(get_responseJSON['waypoints']))

    # test Trip GET for collection
    def test_get_collection(self):
        # create User object
        user_response = self.app.post('/users/', data=json.dumps(dict(
            username='leslie', password='password111')),
            content_type='application/json')
        user_id = json.loads(user_response.data.decode())       # get user_id

        # create headers by encoding un:pw and encoding using b64
        creds_string = "{0}:{1}".format('leslie', 'password111')
        cred_encoded = creds_string.encode('utf-8')
        cred_b64encoded = b64encode(cred_encoded).decode()
        # create headers with properly encoded us:pw
        headers = {'Authorization': 'Basic ' + cred_b64encoded}

        # create 3 Trip objects w/ name, waypoints and user_id
        dc_response = self.app.post('/trips/', headers=headers, data=json.dumps(
            dict(name='Washington DC', waypoints=['DC', 'Virginia',
                                                  'Maryland'], uID=user_id)),
            content_type='application/json')
        east_coast_response = self.app.post('/trips/', headers=headers, data=json.dumps(
            dict(name='East Coast', waypoints=['New York', 'New Jersey',
                                               'Vermont', 'Rhode Island'],
                 uID=user_id)), content_type='application/json')
        north_america_response = self.app.post('/trips/', headers=headers, data=json.dumps(
            dict(name='North America', waypoints=['United States', 'Canada',
                                                  'Mexico'], uID=user_id)),
            content_type='application/json')

        # TODO: update this to return collection
        response = self.app.get('/trips/')

    # test Trip GET method for a non existing trip_id
    def test_get_nonexistent_trip(self):
        # GET a Trip that doesn't exist
        response = self.app.get('/trips/55f0cbb4236f44b7f0e3cb23')

        # perform assertion tests
        self.assertEqual(response.status_code, 404)

    # test Trip PUT method
    def test_put(self):
        # create User object
        user_response = self.app.post('/users/', data=json.dumps(dict(
            username='kimleslie', password='password12345')),
            content_type='application/json')
        user_id = json.loads(user_response.data.decode())       # get user_id

        self.assertEqual(user_response.status_code, 200)
        assert 'application/json' in user_response.content_type

        # create headers by encoding un:pw and encoding using b64
        creds_string = "{0}:{1}".format('kimleslie', 'password12345')
        cred_encoded = creds_string.encode('utf-8')
        cred_b64encoded = b64encode(cred_encoded).decode()
        # create headers with properly encoded us:pw
        headers = {'Authorization': 'Basic ' + cred_b64encoded}

        # create Trip object w/ name, waypoints and user_id
        response = self.app.post('/trips/', headers=headers, data=json.dumps(
            dict(name='West Coast', waypoints=[], uID=user_id)),
            content_type='application/json')

        # decode JSON doc returned and get _id
        postResponseJSON = json.loads(response.data.decode())
        postedObjectID = postResponseJSON['_id']

        # PUT changes for specified Trip
        response = self.app.put('/trips/'+postedObjectID, data=json.dumps(
            dict(name='West Coast', waypoints=['Los Angeles', 'Seattle',
                                               'Portland'])),
            content_type='application/json')
        responseJSON = json.loads(response.data.decode())

        # perform assertion tests
        self.assertEqual(response.status_code, 200)
        assert 'West Coast' in responseJSON['name']
        self.assertEqual(3, len(responseJSON['waypoints']))

    # test Trip DELETE method
    def test_delete(self):
        # create User object
        user_response = self.app.post('/users/', data=json.dumps(dict(
            username='kiml', password='password321')),
            content_type='application/json')
        user_id = json.loads(user_response.data.decode())       # get user_id

        self.assertEqual(user_response.status_code, 200)
        assert 'application/json' in user_response.content_type

        # create headers by encoding un:pw and encoding using b64
        creds_string = "{0}:{1}".format('kiml', 'password321')
        cred_encoded = creds_string.encode('utf-8')
        cred_b64encoded = b64encode(cred_encoded).decode()
        # create headers with properly encoded us:pw
        headers = {'Authorization': 'Basic ' + cred_b64encoded}

        # create Trip object w/ name, waypoints and user_id
        response = self.app.post('/trips/', headers=headers, data=json.dumps(
            dict(name='West Coast', waypoints=[], uID=user_id)),
            content_type='application/json')

        # decode JSON doc returned and get _id
        postResponseJSON = json.loads(response.data.decode())
        postedObjectID = postResponseJSON['_id']

        del_response = self.app.delete('/trips/'+postedObjectID)
        self.assertEqual(del_response.status_code, 200)

        get_response = self.app.get('/trips/'+postedObjectID)
        self.assertEqual(get_response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
