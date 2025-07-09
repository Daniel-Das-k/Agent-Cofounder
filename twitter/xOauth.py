
import os
import json
import base64
import hashlib
import re
from flask import Flask, render_template, request, session, redirect
from requests_oauthlib import OAuth2Session
from flask_cors import CORS
from dotenv import load_dotenv
import requests

load_dotenv()

class TwitterOauth:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = os.urandom(24)
        CORS(self.app)
        self.client_id = os.getenv("TWITTER_OAUTH_CLIENT_ID")
        self.client_secret = os.getenv("TWITTER_OAUTH_CLIENT_SECRET")
        self.redirect_uri = os.getenv("TWITTER_REDIRECT_URI")
        self.auth_url = "https://twitter.com/i/oauth2/authorize"
        self.token_url = "https://api.twitter.com/2/oauth2/token"
        self.scopes = ["tweet.read", "users.read", "tweet.write", "offline.access"]
        self.code_verifier = self.create_code_verifier()
        self.code_challenge = self.create_code_challenge()
        self.json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'twitter_access.json'))
        self.setup_routes()

    def create_code_verifier(self):
        code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
        return re.sub("[^a-zA-Z0-9]+", "", code_verifier)

    def create_code_challenge(self):
        code_challenge = hashlib.sha256(self.code_verifier.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(code_challenge).decode("utf-8").replace("=", "")

    def setup_routes(self):
        self.app.add_url_rule('/', 'home', self.home)
        self.app.add_url_rule('/oauth/callback', 'callback', self.callback)
        self.app.add_url_rule('/logout', 'logout', self.logout)

    def home(self):
        stored_data = self.get_stored_data()
        if stored_data:
            session['token'] = stored_data['access_token']
            self.current_user_id = stored_data['current_user']['id']
            self.current_user_username= stored_data['current_user']['username']
            print(self.current_user_id, "Id loaded from storage")
            print(self.current_user_username,"User Name")
            return render_template("index.html", user_info=self.current_user_id,username = self.current_user_username)
            
        else:
            twitter = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri, scope=self.scopes)
            authorization_url, state = twitter.authorization_url(
                self.auth_url, code_challenge=self.code_challenge, code_challenge_method="S256"
            )
            session["oauth_state"] = state
            print(f"Authorization URL: {authorization_url}")
            return render_template("index.html", oauth_uri=authorization_url)

    def callback(self):
        try:
            code = request.args.get("code")
            if not code:
                return "No authorization code found in the request."

            print("Authorization code received:", code)

            twitter = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri, scope=self.scopes)
            token = twitter.fetch_token(
                token_url=self.token_url,
                client_secret=self.client_secret,
                code_verifier=self.code_verifier,
                code=code,
            )
            print("Token fetched:", token)

            bearer_client = OAuth2Session(self.client_id, token=token)
            user_info_response = bearer_client.get('https://api.twitter.com/2/users/me')
            if user_info_response.status_code != 200:
                print(f"Failed to fetch user info: {user_info_response.text}")
                return "Failed to fetch user info."

            user_info = user_info_response.json()
            print("User info response:", user_info)

            # Check if 'data' exists in the response
            if 'data' not in user_info:
                return "User info does not contain 'data'."

            user_data = user_info['data']
            print("THIS IS USER DATA", user_data)
            print("USER DATA ID", user_data['id'])
            self.current_user = {
                'id': user_data['id'],
                'username': user_data['username'],
                'name': user_data['name'],
            }
            print(self.current_user["id"],"this is current user id")

            session['token'] = token
            self.store_data({
                'access_token': token['access_token'],
                'current_user': self.current_user
            })
            return redirect("/")
        except Exception as e:
            print(f"Error during callback: {str(e)}")
            return f"An error occurred during callback: {str(e)}"

    def logout(self):
        session.clear()
        if os.path.exists(self.json_path):
            os.remove(self.json_path)
        return redirect("/")

    def get_stored_data(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r') as f:
                return json.load(f)
        return None

    def store_data(self, data):
        with open(self.json_path, 'w') as f:
            json.dump(data, f)

    def run(self, debug=True):
        self.app.run(debug=debug)

if __name__ == "__main__":
    app = TwitterOauth()
    app.run()