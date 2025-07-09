#!/usr/bin/env python3
"""
Startup Reddit Poster - Only allows posting to approved startup subreddits
Based on your startup launch checklist
"""

import sys
from reddit_client import RedditClient

class StartupRedditPoster:
    """Reddit poster specifically for startup-related subreddits"""
    
    def __init__(self):
        self.client = RedditClient()
        self.authenticated = False
        
        # Approved subreddits from your launch checklist with posting requirements
        self.approved_subreddits = {
            'Startups': {
                'description': 'General startup community',
                'title_requirement': 'i will not promote',
                'requires_flair': True,
                'difficulty': 'Hard'
            },
            'advancedentrepreneur': {
                'description': 'Advanced entrepreneurship discussions',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Medium'
            },
            'AlphaandBetausers': {
                'description': 'Alpha and beta testing community',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'Coupons': {
                'description': 'Coupon and deal sharing',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'Design_Critiques': {
                'description': 'Design feedback and critiques',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'Entrepreneur': {
                'description': 'Main entrepreneurship community',
                'title_requirement': None,
                'requires_flair': True,
                'difficulty': 'Medium'
            },
            'indiebiz': {
                'description': 'Independent business discussions',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'LadyBusiness': {
                'description': 'Women in business',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'MadeThis': {
                'description': 'Show off your creations',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'Plugyourproduct': {
                'description': 'Product promotion community',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'ProductMgmt': {
                'description': 'Product management discussions',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Medium'
            },
            'RoastMyStartup': {
                'description': 'Get feedback on your startup',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'SideProject': {
                'description': 'Side project showcase',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'smallbusiness': {
                'description': 'Small business community',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Medium'
            },
            'startup': {
                'description': 'Startup discussions',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'startups_promotion': {
                'description': 'Startup promotion',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'sweatystartup': {
                'description': 'Service-based business startups',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'thesidehustle': {
                'description': 'Side hustle discussions',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'Webdesign': {
                'description': 'Web design community',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'AskReddit': {
                'description': 'Ask Reddit community',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Medium'
            },
            'EntrepreneurRideAlong': {
                'description': 'Entrepreneur journey sharing',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'InternetIsBeautiful': {
                'description': 'Cool internet discoveries',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Medium'
            },
            'Productivity': {
                'description': 'Productivity tips and tools',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'Programming': {
                'description': 'Programming discussions',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Medium'
            },
            'TodayILearned': {
                'description': 'Today I learned facts',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Medium'
            },
            'WantToLearn': {
                'description': 'Learning new skills',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            },
            'Webdev': {
                'description': 'Web development',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Medium'
            },
            'growmybusiness': {
                'description': 'Business growth strategies',
                'title_requirement': None,
                'requires_flair': False,
                'difficulty': 'Easy'
            }
        }
    
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
    
    def show_approved_subreddits(self):
        """Display approved subreddits with posting requirements"""
        print("\n📋 APPROVED STARTUP SUBREDDITS")
        print("=" * 50)
        print("These subreddits are pre-approved for startup content:\n")
        
        # Group by difficulty
        easy_subs = []
        medium_subs = []
        hard_subs = []
        
        for subreddit, info in self.approved_subreddits.items():
            if info['difficulty'] == 'Easy':
                easy_subs.append((subreddit, info))
            elif info['difficulty'] == 'Medium':
                medium_subs.append((subreddit, info))
            else:
                hard_subs.append((subreddit, info))
        
        # Display easy subreddits first (recommended for beginners)
        print("🟢 EASY (No special requirements):")
        for i, (subreddit, info) in enumerate(easy_subs, 1):
            print(f"{i:2d}. r/{subreddit}")
            print(f"    📝 {info['description']}")
            print()
        
        print("🟡 MEDIUM (May require flair or have stricter rules):")
        start_num = len(easy_subs) + 1
        for i, (subreddit, info) in enumerate(medium_subs, start_num):
            print(f"{i:2d}. r/{subreddit}")
            print(f"    📝 {info['description']}")
            if info['requires_flair']:
                print(f"    ⚠️ Requires post flair")
            print()
        
        print("🔴 HARD (Special title requirements + flair):")
        start_num = len(easy_subs) + len(medium_subs) + 1
        for i, (subreddit, info) in enumerate(hard_subs, start_num):
            print(f"{i:2d}. r/{subreddit}")
            print(f"    📝 {info['description']}")
            if info['title_requirement']:
                print(f"    ⚠️ Must include '{info['title_requirement']}' in title")
            if info['requires_flair']:
                print(f"    ⚠️ Requires post flair")
            print()
    
    def show_easy_subreddits(self):
        """Show only easy subreddits for quick posting"""
        print("\n🟢 EASY SUBREDDITS (Recommended for beginners)")
        print("=" * 50)
        print("These subreddits have no special requirements:\n")
        
        easy_subs = [(sub, info) for sub, info in self.approved_subreddits.items() if info['difficulty'] == 'Easy']
        
        for i, (subreddit, info) in enumerate(easy_subs, 1):
            print(f"{i:2d}. r/{subreddit}")
            print(f"    📝 {info['description']}")
            print(f"    ✅ No title requirements, no flair needed")
            print()
        
        print("💡 These are perfect for your first posts!")
        print("💡 Try r/startup, r/SideProject, or r/RoastMyStartup first")
    
    def select_subreddit_interactive(self):
        """Interactive subreddit selection from approved list"""
        self.show_approved_subreddits()
        
        print("🎯 SELECT SUBREDDIT")
        print("-" * 20)
        
        # Show numbered options
        subreddit_list = list(self.approved_subreddits.keys())
        
        while True:
            try:
                choice = input(f"Enter subreddit number (1-{len(subreddit_list)}) or name: ").strip()
                
                # Check if it's a number
                if choice.isdigit():
                    index = int(choice) - 1
                    if 0 <= index < len(subreddit_list):
                        return subreddit_list[index]
                    else:
                        print(f"❌ Please enter a number between 1 and {len(subreddit_list)}")
                        continue
                
                # Check if it's a subreddit name
                if choice in self.approved_subreddits:
                    return choice
                
                # Check if it's a subreddit name without case sensitivity
                for subreddit in self.approved_subreddits:
                    if choice.lower() == subreddit.lower():
                        return subreddit
                
                print(f"❌ '{choice}' is not in the approved list. Please choose from the list above.")
                
            except KeyboardInterrupt:
                print("\n❌ Cancelled by user")
                return None
    
    def create_startup_post(self):
        """Create a post to an approved startup subreddit"""
        print("\n✍️ CREATE STARTUP POST")
        print("-" * 25)
        
        # Select subreddit
        subreddit = self.select_subreddit_interactive()
        if not subreddit:
            return False
        
        print(f"\n✅ Selected: r/{subreddit}")
        sub_info = self.approved_subreddits[subreddit]
        print(f"📝 {sub_info['description']}")
        print(f"🏷️ Difficulty: {sub_info['difficulty']}")
        
        # Show requirements if any
        if sub_info['title_requirement'] or sub_info['requires_flair']:
            print("\n⚠️ POSTING REQUIREMENTS:")
            if sub_info['title_requirement']:
                print(f"   • Title must include: '{sub_info['title_requirement']}'")
            if sub_info['requires_flair']:
                print(f"   • Post flair is required (you'll need to add it manually after posting)")
        
        # Get title with automatic requirement insertion
        if sub_info['title_requirement']:
            print(f"\n✏️ Title will automatically include '{sub_info['title_requirement']}'")
            base_title = input("Enter your post title: ").strip()
            if not base_title:
                print("❌ Post title is required")
                return False
            title = f"{base_title} - {sub_info['title_requirement']}"
            print(f"📝 Final title: {title}")
        else:
            title = input("\nEnter post title: ").strip()
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
        
        # Show preview
        print("\n📋 POST PREVIEW")
        print("-" * 25)
        print(f"Subreddit: r/{subreddit}")
        print(f"Description: {sub_info['description']}")
        print(f"Difficulty: {sub_info['difficulty']}")
        print(f"Title: {title}")
        print(f"Type: {'Text' if is_text_post else 'Link'}")
        print(f"Content: {content[:100]}{'...' if len(content) > 100 else ''}")
        
        # Show warnings for requirements
        if sub_info['requires_flair']:
            print("\n⚠️ IMPORTANT: This subreddit requires post flair!")
            print("   After posting, immediately go to your post and add appropriate flair.")
        
        # Confirm
        confirm = input("\nPost this to the startup community? (y/n): ").strip().lower()
        
        if confirm in ['y', 'yes']:
            print("\n🚀 Posting to Reddit...")
            result = self.client.post_to_subreddit(subreddit, title, content, is_text_post)
            
            if result['success']:
                print("🎉 Startup post successful!")
                print(f"🔗 View at: {result['url']}")
                print(f"📊 Posted to r/{subreddit} - {sub_info['description']}")
                
                # Remind about flair if needed
                if sub_info['requires_flair']:
                    print("\n🚨 REMINDER: Don't forget to add post flair!")
                    print("   1. Click on your post")
                    print("   2. Click 'Add Flair' or the flair button")
                    print("   3. Select appropriate flair and save")
                
                return True
            else:
                error_msg = result['error']
                print(f"❌ Post failed: {error_msg}")
                
                # Provide specific help for common errors
                if "SUBMIT_VALIDATION_FLAIR_REQUIRED" in str(error_msg):
                    print("\n💡 This subreddit requires flair to be set BEFORE posting.")
                    print("   Unfortunately, this can't be automated. Try a different subreddit.")
                    print("   Recommended alternatives:")
                    print("   • r/startup (no flair required)")
                    print("   • r/SideProject (no flair required)")
                    print("   • r/RoastMyStartup (no flair required)")
                elif "SUBMIT_VALIDATION_TITLE_REQUIREMENT" in str(error_msg):
                    print(f"\n💡 Title requirement issue. Make sure title includes: '{sub_info['title_requirement']}'")
                
                return False
        else:
            print("❌ Post cancelled")
            return False
    
    def quick_post_to_approved(self, subreddit_name, title, content, is_text_post=True):
        """Quick post to approved subreddit"""
        # Validate subreddit
        if subreddit_name not in self.approved_subreddits:
            print(f"❌ '{subreddit_name}' is not in the approved startup subreddits list")
            print("✅ Try these easy options:", [sub for sub, info in self.approved_subreddits.items() if info['difficulty'] == 'Easy'][:5])
            return False
        
        if not self.authenticated:
            print("❌ Please authenticate first")
            return False
        
        print(f"🚀 Posting to r/{subreddit_name}...")
        result = self.client.post_to_subreddit(subreddit_name, title, content, is_text_post)
        
        if result['success']:
            print("🎉 Startup post successful!")
            print(f"🔗 View at: {result['url']}")
            return True
        else:
            return False
    
    def run(self):
        """Main application"""
        print("🚀 Startup Reddit Poster")
        print("=" * 30)
        print("📋 Only posts to approved startup-related subreddits")
        print()
        
        # Check credentials
        if not self.client.client_id or not self.client.client_secret:
            print("⚠️ Setup Required:")
            print("Reddit credentials not found in .env file")
            return
        
        # Authenticate
        if not self.authenticate_user():
            return
        
        while True:
            print("\n🎯 STARTUP REDDIT POSTER MENU")
            print("-" * 30)
            print("1. Create startup post")
            print("2. View approved subreddits")
            print("3. Show easy subreddits (recommended)")
            print("4. Exit")
            
            choice = input("\nChoose an option (1-4): ").strip()
            
            if choice == "1":
                self.create_startup_post()
            elif choice == "2":
                self.show_approved_subreddits()
            elif choice == "3":
                self.show_easy_subreddits()
            elif choice == "4":
                print("\n👋 Thanks for using Startup Reddit Poster!")
                break
            else:
                print("❌ Invalid choice. Please try again.")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("""
Startup Reddit Poster - Approved Subreddits Only

Usage:
    python startup_reddit_poster.py              # Interactive mode
    python startup_reddit_poster.py --help       # Show this help
    python startup_reddit_poster.py --list       # Show approved subreddits

Features:
- Only allows posting to pre-approved startup subreddits
- Interactive subreddit selection
- Post preview before publishing
- OAuth 2.0 authentication with Reddit

Approved subreddits include:
- r/Startups, r/Entrepreneur, r/startup
- r/RoastMyStartup, r/SideProject
- And 25+ other startup-focused communities
            """)
            return
        elif sys.argv[1] == "--list":
            poster = StartupRedditPoster()
            poster.show_approved_subreddits()
            return
    
    poster = StartupRedditPoster()
    try:
        poster.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()