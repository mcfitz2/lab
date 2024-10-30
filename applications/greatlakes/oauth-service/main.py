import pprint
import requests
from oauthlib.oauth2 import WebApplicationClient
from prefect.blocks.system import Secret
from flask import Flask, request, redirect, jsonify
import os
import time


class OauthHandler:
    def __init__(self,
                 slug,
                 client_id_var,
                 client_secret_var,
                 access_token_var,
                 refresh_token_var,
                 auth_url,
                 token_url,
                 scope,
                 refresh_url=None,
                 use_auth_header=True):
        self.use_auth_header = use_auth_header
        if scope is None:
            scope = []
        self.refresh_url = refresh_url or token_url
        self.scope = scope
        self.slug = slug
        self.token_url = token_url
        self.access_token_var = access_token_var
        self.refresh_token_var = refresh_token_var
        self.auth_url = auth_url
        self.client_id = self.get_secret_by_name(client_id_var)
        self.client_secret = self.get_secret_by_name(client_secret_var)
        self.client = WebApplicationClient(self.get_secret_by_name(client_id_var))
        self.cached_access_token = None
        self.cached_refresh_token = None
        self.cache_age = 0
        print(f"Instantiated handler [{self.slug}] with CLIENT_ID={self.client_id} CLIENT_SECRET={self.client_secret}")

    def auth_route(self):
        redirect_uri = self.client.prepare_request_uri(
            self.auth_url,
            redirect_uri=f"{os.environ['BASE_URL']}/auth/{self.slug}/callback",
            access_type='offline',
            scope=self.scope,
        )
        return redirect(redirect_uri)

    def callback_route(self):
        code = request.args.get("code")
        if self.use_auth_header:
            token_url, headers, body = self.client.prepare_token_request(
                self.token_url,
                authorization_response=request.url,
                redirect_url=f"{os.environ['BASE_URL']}/auth/{self.slug}/callback",
                code=code,
            )
            token_response = requests.post(
                token_url,
                headers=headers,
                data=body,
                auth=(self.client_id, self.client_secret),
            )
        else:
            token_url, headers, body = self.client.prepare_token_request(
                self.token_url,
                authorization_response=request.url,
                redirect_url=f"{os.environ['BASE_URL']}/auth/{self.slug}/callback",
                code=code,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            token_response = requests.post(
                token_url,
                headers=headers,
                data=body,
            )
        tokens = token_response.json()
        try:
            self.set_secret(self.access_token_var, tokens['access_token'])
            self.set_secret(self.refresh_token_var, tokens['refresh_token'])
            self.cached_refresh_token = tokens['refresh_token']
            self.cached_access_token = tokens['access_token']
            self.cache_age = time.time()
        except KeyError:
            print("failed to save tokens")
            pprint.pprint(tokens)
        return redirect('/home')

    def refresh_route(self):
        if self.use_auth_header:
            response = requests.post(self.refresh_url, data={
                'grant_type': 'refresh_token',
                'refresh_token': self.get_refresh_token()
            }, auth=(self.client_id, self.client_secret))
        else:
            response = requests.post(self.refresh_url, data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': self.get_refresh_token()
            })

        try:
            tokens = response.json()
            pprint.pprint(tokens)

            self.set_secret(self.access_token_var, tokens['access_token'])
            if tokens.get('refresh_token'):
                self.set_secret(self.refresh_token_var, tokens.get('refresh_token'))
                self.cached_refresh_token = tokens.get('refresh_token')
            self.cached_access_token = tokens['access_token']
            self.cache_age = time.time()
        except KeyError:
            pprint.pprint(tokens)
        except Exception as e:
            print(e)
            print(response.status_code)
            pprint.pprint(response.content)
        return jsonify({
            'accessToken': self.cached_access_token,
            'refreshToken': self.cached_refresh_token
        })

    def token_route(self):
        return jsonify({
            'accessToken': self.get_access_token(),
            'refreshToken': self.get_refresh_token()
        })

    @staticmethod
    def get_secret_by_name(name):
        secret_block = Secret.load(name)
        return secret_block.get()

    @staticmethod
    def set_secret(name, value):
        return Secret(value=value).save(name, overwrite=True)

    def reload_cache(self):
        #if (time.time() - self.cache_age) > 300 or not self.cached_access_token or not self.cached_refresh_token:
        self.cached_access_token = self.get_secret_by_name(self.access_token_var)
        self.cached_refresh_token = self.get_secret_by_name(self.refresh_token_var)
        self.cache_age = time.time()

    def get_access_token(self):
        self.reload_cache()
        return self.cached_access_token

    def get_refresh_token(self):
        self.reload_cache()
        return self.cached_refresh_token


class GoogleHandler(OauthHandler):
    def __init__(self):
        super().__init__('google',
                         'google-client-id',
                         'google-client-secret',
                         'google-access-token',
                         'google-refresh-token',
                         'https://accounts.google.com/o/oauth2/v2/auth',
                         'https://oauth2.googleapis.com/token',
                         [
                             'email',
                             'profile',
                             'openid',
                             'https://mail.google.com/',
                             'https://www.googleapis.com/auth/fitness.activity.read',
                             'https://www.googleapis.com/auth/calendar',
                             'https://www.googleapis.com/auth/drive',
                             'https://www.googleapis.com/auth/documents'
                         ])


class FitBitHandler(OauthHandler):
    def __init__(self):
        super().__init__('fitbit',
                         'fitbit-client-id',
                         'fitbit-client-secret',
                         'fitbit-access-token',
                         'fitbit-refresh-token',
                         'https://www.fitbit.com/oauth2/authorize',
                         'https://api.fitbit.com/oauth2/token',
                         [
                             'activity',
                             'cardio_fitness',
                             'electrocardiogram',
                             'heartrate',
                             'location',
                             'nutrition',
                             'oxygen_saturation',
                             'profile',
                             'respiratory_rate',
                             'settings',
                             'sleep',
                             'social',
                             'temperature',
                             'weight'
                         ])


class StravaHandler(OauthHandler):
    def __init__(self):
        super().__init__('strava',
                         'strava-client-id',
                         'strava-client-secret',
                         'strava-access-token',
                         'strava-refresh-token',
                         'https://www.strava.com/oauth/authorize',
                         'https://www.strava.com/oauth/token',
                         ['read_all,activity:read_all,profile:read_all']
                         )


class DropboxHandler(OauthHandler):
    def __init__(self):
        super().__init__('dropbox',
                         'dropbox-client-id',
                         'dropbox-client-secret',
                         'dropbox-access-token',
                         'dropbox-refresh-token',
                         'https://www.dropbox.com/1/oauth2/authorize',
                         'https://api.dropbox.com/1/oauth2/token',
                         []
                         )


app = Flask(__name__)
handlers = {
    'google': GoogleHandler(),
    'fitbit': FitBitHandler(),
    'strava': StravaHandler(),
    'dropbox': DropboxHandler()
}


@app.route('/home')
def home():
    html = '<table style="border: 1px solid black;">\n' + '\n'.join([
        f'<tr style = "border: 1px solid black;">\n\t<td>{slug}</td>\n\t<td><a href = "/auth/{slug}">{slug}</a></td>\n\t<td><a href="/auth/{slug}/refresh">refresh</a></td>\n\t<td>{handlers[slug].get_access_token()[:20]}</td>\n\t<td>{handlers[slug].get_refresh_token()[:20]}</td>\n</tr>\n'
        for slug in handlers.keys()]) + '</table>'

    return html


@app.route('/auth/<slug>')
def auth_route(slug):
    print(slug)
    return handlers[slug].auth_route()


@app.route('/auth/<slug>/callback')
def callback_route(slug):
    return handlers[slug].callback_route()


@app.route('/auth/<slug>/refresh', methods=['POST', 'GET'])
def refresh_token(slug):
    return handlers[slug].refresh_route()


@app.route('/auth/<slug>/token', methods=['GET'])
def get_token(slug):
    return handlers[slug].token_route()


if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(host="0.0.0.0", port=4002, debug=True)
