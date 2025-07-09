#!/usr/bin/env python3
"""
Standalone Reddit Posting Tool
Separate from the AI Cofounder system
"""

import sys
from reddit_client import RedditClient

class RedditPoster:
    """Standalone Reddit posting application"""
    
    def __init__(self):
        self.client = RedditClient()
        self.authenticated = False
    
    def authenticate_user(self):
        """Authenticate with Reddit"""
        print("🔐 Reddit Authentication Required")
        print("=" * 40)
        
        if self.client.authenticate():
            self.authenticated = True
            return True
        else:
            print("❌ Authentication failed. Please check your credentials.")
            return False
    
    def search_subreddits_interactive(self):
        """Interactive subreddit search"""
        print("\n🔍 SUBREDDIT SEARCH")
        print("-" * 20)
        
        query = input("Enter search topic (e.g., 'startups', 'technology'): ").strip()
        
        if not query:
            print("❌ Please enter a search term")
            return []
        
        print(f"🔍 Searching for subreddits related to '{query}'...")
        subreddits = self.client.search_subreddits(query, limit=10)
        
        if subreddits:
            print(f"\n📊 Found {len(subreddits)} relevant subreddits:")
            print("-" * 50)
            for i, sub in enumerate(subreddits, 1):
                print(f"{i}. r/{sub['name']}")
                print(f"   👥 {sub['subscribers']:,} subscribers")
                print(f"   📝 {sub['description']}")
                print()
        else:
            print("❌ No subreddits found for that topic")
        
        return subreddits
    
    def create_post_interactive(self):
        """Interactive post creation"""
        print("\n✍️ CREATE REDDIT POST")
        print("-" * 25)
        
        print("💡 Suggested subreddits for testing:")
        print("   • test - for general testing")
        print("   • SandBoxTest - for testing posts")
        print("   • u_YourUsername - your own profile")
        print("   • CasualConversation - for casual posts")
        print()
        
        # Get subreddit
        subreddit = input("Enter subreddit name (without r/): ").strip()
        if not subreddit:
            print("❌ Subreddit name is required")
            return False
        
        # Get title
        title = input("Enter post title: ").strip()
        if not title:
            print("❌ Post title is required")
            return False
        
        # Get content type
        print("\nPost type:")
        print("1. Text post")
        print("2. Link post")
        post_type = input("Choose (1 or 2): ").strip()
        
        if post_type == "1":
            content = input("Enter post content/text: ").strip()
            is_text_post = True
        elif post_type == "2":
            content = input("Enter URL: ").strip()
            is_text_post = False
        else:
            print("❌ Invalid choice")
            return False
        
        if not content:
            print("❌ Post content is required")
            return False
        
        # Confirm post
        print("\n📋 POST PREVIEW")
        print("-" * 15)
        print(f"Subreddit: r/{subreddit}")
        print(f"Title: {title}")
        print(f"Type: {'Text' if is_text_post else 'Link'}")
        print(f"Content: {content[:100]}{'...' if len(content) > 100 else ''}")
        
        confirm = input("\nPost this? (y/n): ").strip().lower()
        
        if confirm in ['y', 'yes']:
            print("\n🚀 Posting to Reddit...")
            result = self.client.post_to_subreddit(subreddit, title, content, is_text_post)
            
            if result['success']:
                print("🎉 Post successful!")
                print(f"🔗 View at: {result['url']}")
                return True
            else:
                print(f"❌ Post failed: {result['error']}")
                return False
        else:
            print("❌ Post cancelled")
            return False
    
    def show_user_subreddits(self):
        """Show user's subscribed subreddits"""
        if not self.authenticated:
            print("❌ Please authenticate first")
            return
        
        print("\n📊 YOUR SUBSCRIBED SUBREDDITS")
        print("-" * 30)
        
        subreddits = self.client.get_user_subreddits(limit=15)
        
        if subreddits:
            for i, sub in enumerate(subreddits, 1):
                print(f"{i:2d}. r/{sub['name']}")
                print(f"    👥 {sub['subscribers']:,} subscribers")
                print(f"    📝 {sub['title']}")
                print()
        else:
            print("❌ No subreddits found or error occurred")
    
    def run(self):
        """Main application loop"""
        print("🚀 Reddit Poster - Standalone Tool")
        print("=" * 40)
        
        # Check credentials
        if not self.client.client_id or not self.client.client_secret:
            print("⚠️ Setup Required:")
            print("1. Go to https://www.reddit.com/prefs/apps")
            print("2. Create a new app (choose 'script' type)")
            print("3. Add your credentials to .env file:")
            print("   REDDIT_CLIENT_ID='your_client_id'")
            print("   REDDIT_CLIENT_SECRET='your_client_secret'")
            return
        
        # Authenticate
        if not self.authenticate_user():
            return
        
        while True:
            print("\n🎯 REDDIT POSTER MENU")
            print("-" * 20)
            print("1. Create new post")
            print("2. Search subreddits")
            print("3. View my subreddits")
            print("4. Exit")
            
            choice = input("\nChoose an option (1-4): ").strip()
            
            if choice == "1":
                self.create_post_interactive()
            elif choice == "2":
                self.search_subreddits_interactive()
            elif choice == "3":
                self.show_user_subreddits()
            elif choice == "4":
                print("\n👋 Thanks for using Reddit Poster!")
                break
            else:
                print("❌ Invalid choice. Please try again.")

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
Reddit Poster - Standalone Tool

Usage:
    python reddit_poster.py                 # Interactive mode
    python reddit_poster.py --help          # Show this help

Features:
- OAuth 2.0 authentication with Reddit
- Search for relevant subreddits
- Create text and link posts
- View your subscribed subreddits
- Interactive user interface

Setup:
1. Create Reddit app at https://www.reddit.com/prefs/apps
2. Add credentials to .env file
3. Run the tool
        """)
        return
    
    poster = RedditPoster()
    try:
        poster.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()