import json
import requests

class TwitterPoster:
    def __init__(self, token_file='twitter_access.json'):
        self.token_file = token_file

    def get_access_token(self):
        with open(self.token_file, 'r') as f:
            token_data = json.load(f)
            return token_data['access_token']

    def post_tweet(self):
        access_token = self.get_access_token()

        content  = "hi"
        payload = {
            "text": str(content)
        }
        response = self.post_tweet_api(payload, access_token)
        return response

    def post_tweet_api(self, payload, token):
        print("Tweeting!")
        response = requests.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        print("Posted:", payload["text"])
        return response

if __name__ == "__main__":
    xpost = TwitterPoster()
    # xcrew = Twitter()
    # xtweet = xcrew.run()
    
    xpost.post_tweet()