import json
import os

from eve.auth import BasicAuth
from rauth import OAuth2Service
from flask import url_for, request, redirect, Response, abort

from redis import StrictRedis

from functools import wraps

class DataportenAdminSignIn(BasicAuth):
    tokenPrefix = 'ADMIN-{}'
    def __init__(self):
        super(DataportenAdminSignIn, self).__init__()

        self.provider_name = 'dataporten_admin'
        self.consumer_id =  os.environ['DATAPORTEN_ADMIN_CLIENT_ID']
        self.consumer_secret = os.environ['DATAPORTEN_ADMIN_CLIENT_SECRET']

        self.service = OAuth2Service(
            name=self.provider_name,
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://auth.dataporten.no/oauth/authorization',
            access_token_url='https://auth.dataporten.no/oauth/token',
            base_url='https://auth.dataporten.no/'
        )

        self.redis = StrictRedis()

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            client_id=self.consumer_id,
            response_type='code',
            redirect_uri=self.get_callback_url())
        )

    def callback(self):
        def decode_json(payload):
            return json.loads(payload.decode('utf-8'))

        if 'code' not in request.args:
            return None, None, None
        raw_access_token = self.service.get_raw_access_token(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()}
        )
        response = decode_json(raw_access_token.content)
        oauth_session = self.service.get_session(token=response['access_token'])

        userinfo = oauth_session.get('userinfo').json()
        # {'user': {'userid_sec': ['feide:ran033@uit.no'], 'userid': '9618b141-55f7-442b-b89a-7cdf2d3e716a', 'name': 'Ruben Andreassen',
        # 'email': 'ruben.andreassen@uit.no', 'profilephoto': 'p:6712c0ae-6779-4f25-8c95-696498a5c0ca'},
        # 'audience': 'b00d74c3-1afe-49a8-9a9d-bd25903db400'}
        # print(userinfo['audience'])
        # print(os.environ['DATAPORTEN_CLIENT_ID'])
        # Validate that the audience is the same as the client_id
        if (userinfo['audience'] != os.environ['DATAPORTEN_ADMIN_CLIENT_ID']):
            return None, None

        # Store the access_token as key with the user_id as value with an expiration time
        self.redis.set(self.tokenPrefix.format(response['access_token']), userinfo['user']['userid'], response['expires_in'])

        return userinfo['user']['userid'], response['access_token']

    def get_callback_url(self):
        #TODO: This may not be the best check for Azure environment
        try:
            os.environ["MONGO_PASSWORD"]
            return url_for('oauth_callback', provider=self.provider_name, _external=True, _scheme="https")
        except KeyError:
            return url_for('oauth_callback', provider=self.provider_name, _external=True)


    def logout(self):
        """ Delete the stored token
        """
        try:
            token = request.headers.get('Authorization').split(' ')[1]
            self.redis.delete(self.tokenPrefix.format(token))
            return True
        except:
            return False

    # def check_auth(self, token, allowed_roles, resource, method):
    def check_auth(self, token):
        """ Check if API request is authorized.
        Examines token in header and checks Redis cache to see if token is
        valid. If so, request is allowed.
        :param token: OAuth 2.0 access token submitted.
        :param allowed_roles: Allowed user roles.
        :param resource: Resource being requested.
        :param method: HTTP method being executed (POST, GET, etc.)
        """
        dataporten_userid = self.redis.get(self.tokenPrefix.format(token))
        self.set_request_auth_value(dataporten_userid)

        return token and dataporten_userid

    def authorized(self, allowed_roles, resource, method):
        """ Validates the the current request is allowed to pass through.
        :param allowed_roles: allowed roles for the current request, can be a
                              string or a list of roles.
        :param resource: resource being requested.
        """
        try:
            token = request.headers.get('Authorization').split(' ')[1]
        except:
            token = None
        return self.check_auth(token, allowed_roles, resource, method)

    def authenticate(self):
        """ Returns a standard a 401 response that enables basic auth.
        Override if you want to change the response and/or the realm.
        """
        resp = Response(
            None, 401
        )
        abort(401, description="Please log in by accessing the /authorize endpoint", response=resp)

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('authorization').split(' ')[1]
        if not token or not DataportenAdminSignIn().check_auth(token):
            return DataportenAdminSignIn().authenticate()
        return f(*args, **kwargs)
    return decorated