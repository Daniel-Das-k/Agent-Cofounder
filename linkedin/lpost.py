import os
import json
import requests
from dotenv import load_dotenv
from .crew import CrewLinkedIn

load_dotenv()
linkedin = CrewLinkedIn()

class LinkedinManager:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.load_tokens()

    def load_tokens(self):
        with open("linkedin_token.json", 'r') as f:
            token = json.load(f)
            self.access_token = token["access_token"]
            self.user_id = token["id"]

    def upload_image_to_linkedin(self, image_path):
        """Upload an image to LinkedIn and return the upload reference."""
        init_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        upload_request_body = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": f"urn:li:person:{self.user_id}",
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }

        response = requests.post(init_url, headers=headers, json=upload_request_body)
        response.raise_for_status()

        upload_info = response.json()
        upload_url = upload_info['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset = upload_info['value']['asset']

        with open(image_path, 'rb') as image_file:
            image_headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/octet-stream"
            }
            image_response = requests.put(upload_url, headers=image_headers, data=image_file)
            image_response.raise_for_status()

        return asset

    def create_linkedin_post_with_image(self, text, asset):
        """Create a LinkedIn post with text and an image."""
        post_url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        post_data = {
            "author": f"urn:li:person:{self.user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {
                                "text": "Example Image Description"
                            },
                            "media": asset,
                            "title": {
                                "text": "Example Image Title"
                            }
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        response = requests.post(post_url, headers=headers, json=post_data)
        response.raise_for_status()
        return response.json()

    def run(self, image_path, content):
        try:
            text = linkedin.run(content)
            asset = self.upload_image_to_linkedin(image_path)
            print(f"Image uploaded successfully with asset: {asset}")

            post_response = self.create_linkedin_post_with_image(str(text), asset)
            print("Post created successfully:", json.dumps(post_response, indent=4))
            
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            if 'response' in locals() and response.content:
                print("Response content:", response.content)

        except Exception as err:
            print(f"Other error occurred: {err}")

# Usage
if __name__ == "__main__":
    image_path = input('Enter the path to your image: ')
    content = input('Enter the text for your LinkedIn post: ')
    linkedin_manager = LinkedinManager()
    linkedin_manager.run(image_path, content)