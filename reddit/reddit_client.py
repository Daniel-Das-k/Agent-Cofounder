#!/usr/bin/env python3
"""
Reddit OAuth 2.0 Client for Posting Content
Integrates with the AI Cofounder system
"""

import praw
import webbrowser
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

load_dotenv()

class RedditOAuthHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback"""
    
    def do_GET(self):
        # Parse the authorization code from callback
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        if 'code' in query_params:
            self.server.auth_code = query_params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_response = """
            <html>
            <body>
                <h2>✅ Reddit Authorization Successful!</h2>
                <p>You can now close this window and return to your AI Cofounder app.</p>
                <script>window.close();</script>
            </body>
            </html>
            """
            self.wfile.write(html_response.encode('utf-8'))
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error_response = """
            <html>
            <body>
                <h2>❌ Authorization Failed</h2>
                <p>Please try again.</p>
            </body>
            </html>
            """
            self.wfile.write(error_response.encode('utf-8'))
    
    def log_message(self, format, *args):
        # Suppress server logs
        pass

class RedditClient:
    """Reddit API client with OAuth 2.0 authentication"""
    
    def __init__(self):
        self.reddit = None
        self.authenticated = False
        
        # Reddit app credentials (you need to create these)
        self.client_id = os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.redirect_uri = 'http://localhost:8080/callback'
        self.user_agent = 'AICofounder/1.0 by Odd_Ambition_4294'
        
        if not self.client_id or not self.client_secret:
            print("⚠️ Reddit credentials not found in .env file")
            print("Please add REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to your .env file")
    
    def authenticate(self):
        """Authenticate with Reddit using OAuth 2.0"""
        if not self.client_id or not self.client_secret:
            return False
        
        try:
            # Create Reddit instance for OAuth
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                user_agent=self.user_agent
            )
            
            # Get authorization URL
            auth_url = self.reddit.auth.url(
                scopes=['submit', 'read'],
                state='AICofounderAuth',
                duration='temporary'
            )
            
            print("🔐 Starting Reddit OAuth authentication...")
            print("📝 Opening browser for Reddit authorization...")
            
            # Start local server for callback
            server = HTTPServer(('localhost', 8080), RedditOAuthHandler)
            server.auth_code = None
            
            # Open browser for authorization
            webbrowser.open(auth_url)
            
            print("✋ Please authorize the app in your browser...")
            print("🔄 Waiting for authorization...")
            
            # Handle one request (the callback)
            server.handle_request()
            
            if hasattr(server, 'auth_code') and server.auth_code:
                # Exchange code for access token
                print(f"🔑 Exchanging authorization code for access token...")
                self.reddit.auth.authorize(server.auth_code)
                self.authenticated = True
                print("✅ Reddit authentication successful!")
                
                try:
                    user = self.reddit.user.me()
                    print(f"👋 Authenticated as: {user}")
                    return True
                except Exception as user_error:
                    print(f"⚠️ Authentication successful but couldn't get user info: {user_error}")
                    return True  # Still consider it successful
            else:
                print("❌ Authentication failed - no authorization code received")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def post_to_subreddit(self, subreddit_name: str, title: str, content: str, is_text_post: bool = True):
        """Post content to a specific subreddit"""
        if not self.authenticated:
            print("❌ Not authenticated. Please run authenticate() first.")
            return False
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            if is_text_post:
                # Text post
                submission = subreddit.submit(title=title, selftext=content)
            else:
                # Link post (content should be URL)
                submission = subreddit.submit(title=title, url=content)
            
            print(f"✅ Successfully posted to r/{subreddit_name}")
            print(f"📝 Title: {title}")
            print(f"🔗 URL: https://reddit.com{submission.permalink}")
            
            return {
                'success': True,
                'url': f"https://reddit.com{submission.permalink}",
                'submission_id': submission.id
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Failed to post: {error_msg}")
            
            # Provide helpful error messages
            if "SUBREDDIT_NOTALLOWED" in error_msg:
                print("💡 This subreddit has posting restrictions. Try these instead:")
                print("   • r/test - Open for testing")
                print("   • r/SandBoxTest - For test posts")
                print("   • r/CasualConversation - For casual posts")
                print("   • Your own profile: u/your_username")
            elif "RATELIMIT" in error_msg:
                print("💡 You're posting too frequently. Wait a few minutes and try again.")
            elif "NO_TEXT" in error_msg:
                print("💡 This subreddit requires text content.")
            elif "DOMAIN_BANNED" in error_msg:
                print("💡 The link domain is not allowed in this subreddit.")
            
            return {'success': False, 'error': error_msg}
    
    def get_user_subreddits(self, limit=10):
        """Get user's subscribed subreddits"""
        if not self.authenticated:
            return []
        
        try:
            subreddits = []
            for subreddit in self.reddit.user.subreddits(limit=limit):
                subreddits.append({
                    'name': subreddit.display_name,
                    'title': subreddit.title,
                    'subscribers': subreddit.subscribers
                })
            return subreddits
        except Exception as e:
            print(f"❌ Error getting subreddits: {e}")
            return []
    
    def search_subreddits(self, query: str, limit=5):
        """Search for subreddits related to a topic"""
        try:
            if not self.reddit:
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
            
            subreddits = []
            for subreddit in self.reddit.subreddits.search(query, limit=limit):
                subreddits.append({
                    'name': subreddit.display_name,
                    'title': subreddit.title,
                    'subscribers': subreddit.subscribers,
                    'description': subreddit.public_description[:100] + '...' if len(subreddit.public_description) > 100 else subreddit.public_description
                })
            return subreddits
        except Exception as e:
            print(f"❌ Error searching subreddits: {e}")
            return []

# Example usage and testing
if __name__ == "__main__":
    client = RedditClient()
    
    print("🚀 Reddit Client Test")
    print("=" * 40)
    
    # Test authentication
    if client.authenticate():
        print("\n📊 Testing subreddit search...")
        subreddits = client.search_subreddits("startups")
        for sub in subreddits[:3]:
            print(f"• r/{sub['name']} - {sub['subscribers']:,} subscribers")
        
        # Example post (commented out for safety)
        # result = client.post_to_subreddit(
        #     "test", 
        #     "AI Cofounder Test Post", 
        #     "This is a test post from the AI Cofounder system!"
        # )
        # print(f"Post result: {result}")
    else:
        print("❌ Authentication failed")