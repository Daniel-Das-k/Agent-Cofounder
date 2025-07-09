import webbrowser
from flask import Flask, request, redirect, session
import requests
from dotenv import load_dotenv
import os
import threading
import json
load_dotenv()

class LinkedInAuthApp:
    def __init__(self):
        self.CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
        self.REDIRECT_URI = os.getenv('LINKEDIN_REDIRECT_URI')
        self.CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
        self.app1 = Flask(__name__)
        self.app1.secret_key = os.urandom(24)  # Generate a more secure secret key

        # Define routes
        self.app1.add_url_rule('/', 'home', self.home)
        self.app1.add_url_rule('/linkedin/login', 'linkedin_login', self.linkedin_login)
        self.app1.add_url_rule('/linkedin/callback', 'linkedin_callback', self.linkedin_callback)

    def home(self):
        session.clear()  # Clear the session when home route is accessed
        return 'Welcome to the LinkedIn OAuth demo! <a href="/linkedin/login">Login with LinkedIn</a>'

    def linkedin_login(self):
        session.clear()
        authorization_url = 'https://www.linkedin.com/oauth/v2/authorization'
        params = {
            'response_type': 'code',
            'client_id': self.CLIENT_ID,
            'redirect_uri': self.REDIRECT_URI,
            'scope': 'openid+profile+email+w_member_social'
        }
        url = f"{authorization_url}?response_type={params['response_type']}&client_id={params['client_id']}&redirect_uri={params['redirect_uri']}&scope={params['scope']}"
        
        return redirect(url)

    def linkedin_callback(self):
        code = request.args.get('code')
        
        if code:
            # user = str(input('Enter the name: '))  # This should be dynamic or based on the logged-in user's session
            access_token = self.get_access_token(code)
            if access_token:
                session['access_token'] = access_token
                uid = self.get_id(access_token)
                name= uid.json().get('given_name', 'Unknown User')
                family_name= uid.json().get('family_name', 'Unknown User')
                user= f"{name} {family_name}"
                uid=uid.json().get('sub')
                # with open("details.txt", "a") as f:
                #     f.write(f"access_token({user})={access_token}\n")
                #     f.write(f"id({user})={uid}\n")
                
                json_file = "details.json"

                # Load existing data (if any)
                if os.path.exists(json_file):
                    with open(json_file, "r") as f:
                        all_details = json.load(f)
                else:
                    all_details = {}

                # Update this user's record
                all_details[user] = {
                    "access_token": access_token,
                    "id": uid
                }

                # Write back to JSON (with indentation for readability)
                with open(json_file, "w") as f:
                    json.dump(all_details, f, indent=4)

                return 'LinkedIn OAuth successful!'
            else:
                return 'Failed to get access token!'
        else:
            return 'LinkedIn OAuth failed!'

    def get_id(self, access_token):
        url = 'https://api.linkedin.com/v2/userinfo'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(url, headers=headers)
        print(f"Response from LinkedIn userinfo request: {response.json()}")
        return response

    def get_access_token(self, code):
        access_token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.REDIRECT_URI,
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET
        }
        response = requests.post(access_token_url, data=data)
        print(f"Response from LinkedIn access token request: {response.json()}")
        return response.json().get('access_token')

    # def open_browser(self):
    #     webbrowser.open_new('http://localhost:5000/')  # Open the home route instead of the login route

    def run(self):
        # threading.Timer(1, self.open_browser).start()  # Use threading to open the browser after a slight delay
        self.app1.run(debug=True)

if __name__ == '__main__':
    app1 = LinkedInAuthApp()
    app1.run()