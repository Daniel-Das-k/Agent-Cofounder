#!/usr/bin/env python3
"""
Simple Web Interface for Gemini Pitch Deck Generator
Uses built-in Python HTTP server - no external dependencies needed
"""

import os
import json
import requests
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import tempfile
import pathlib
import sys
import re
import subprocess
import base64

# Add helpers to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'helpers'))

try:
    from helpers import pptx_helper
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False
    print("⚠️ PPTX generation not available - missing dependencies")

load_dotenv()

def parse_multipart_form_data(data, boundary):
    """Parse multipart/form-data"""
    form_data = {}
    
    # Split by boundary
    parts = data.split(boundary.encode())
    
    for part in parts:
        if b'Content-Disposition: form-data' in part:
            # Extract field name
            name_match = re.search(rb'name="([^"]+)"', part)
            if name_match:
                field_name = name_match.group(1).decode('utf-8')
                
                # Extract value (everything after the headers)
                content_start = part.find(b'\r\n\r\n')
                if content_start != -1:
                    value_start = content_start + 4
                    value_end = part.rfind(b'\r\n')
                    if value_end > value_start:
                        field_value = part[value_start:value_end].decode('utf-8')
                        form_data[field_name] = field_value
    
    return form_data

class PitchDeckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.serve_html()
        elif self.path == '/generate':
            self.generate_pitch_deck()
        elif (self.path.endswith('.html') or self.path.endswith('.pdf') or self.path.endswith('.pptx')) and 'pitch_deck_' in self.path:
            self.serve_file()
        else:
            self.send_error(404)
    
    def serve_file(self):
        """Serve generated HTML files"""
        filename = self.path[1:]  # Remove leading slash
        try:
            with open(filename, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            if filename.endswith('.html'):
                self.send_header('Content-type', 'text/html')
            elif filename.endswith('.pdf'):
                self.send_header('Content-type', 'application/pdf')
                self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(filename)}"')
            elif filename.endswith('.pptx'):
                self.send_header('Content-type', 'application/vnd.openxmlformats-officedocument.presentationml.presentation')
                self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(filename)}"')
            else:
                self.send_header('Content-type', 'application/octet-stream')
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, "File not found")
    
    def do_POST(self):
        if self.path == '/generate':
            self.generate_pitch_deck()
        else:
            self.send_error(404)
    
    def serve_html(self):
        """Serve the main HTML interface"""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Gemini Pitch Deck Generator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
        }
        
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #34495e;
        }
        
        input, textarea, select {
            width: 100%;
            padding: 15px;
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #3498db;
        }
        
        textarea {
            resize: vertical;
            min-height: 120px;
        }
        
        .btn {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            background: #95a5a6;
            cursor: not-allowed;
            transform: none;
        }
        
        .result {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 5px solid #3498db;
        }
        
        .loading {
            text-align: center;
            margin: 20px 0;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .examples {
            background: #e8f5e8;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
        }
        
        .examples h3 {
            color: #27ae60;
            margin-bottom: 10px;
        }
        
        .examples ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .examples li {
            margin: 8px 0;
            padding: 5px 0;
            cursor: pointer;
            color: #2c3e50;
        }
        
        .examples li:hover {
            color: #3498db;
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Gemini Pitch Deck Generator</h1>
        
        <div class="examples">
            <h3>💡 Example Ideas (click to use):</h3>
            <ul>
                <li onclick="fillExample('AI-powered personal finance app for millennials')">📱 AI-powered personal finance app for millennials</li>
                <li onclick="fillExample('Sustainable food delivery platform using electric vehicles')">🌱 Sustainable food delivery platform using electric vehicles</li>
                <li onclick="fillExample('Remote work productivity tool with AI-powered scheduling')">💼 Remote work productivity tool with AI-powered scheduling</li>
                <li onclick="fillExample('Virtual reality fitness platform for home workouts')">🥽 Virtual reality fitness platform for home workouts</li>
                <li onclick="fillExample('Blockchain-based supply chain transparency solution')">⛓️ Blockchain-based supply chain transparency solution</li>
            </ul>
        </div>
        
        <form id="pitchForm" onsubmit="generatePitchDeck(event)">
            <div class="form-group">
                <label for="topic">Startup Idea/Topic:</label>
                <textarea id="topic" name="topic" 
                         placeholder="Describe your startup idea in detail. Include the problem you're solving, your target market, and your unique solution..." 
                         required></textarea>
            </div>
            
            <div class="form-group">
                <label for="audience">Target Audience:</label>
                <select id="audience" name="audience">
                    <option value="investors">Investors</option>
                    <option value="customers">Potential Customers</option>
                    <option value="partners">Business Partners</option>
                    <option value="employees">Potential Employees</option>
                </select>
            </div>
            
            <button type="submit" class="btn" id="generateBtn">
                🚀 Generate Pitch Deck with AI
            </button>
        </form>
        
        <div id="result" class="result" style="display: none;"></div>
    </div>

    <script>
        function fillExample(text) {
            document.getElementById('topic').value = text;
        }
        
        async function generatePitchDeck(event) {
            event.preventDefault();
            
            const btn = document.getElementById('generateBtn');
            const result = document.getElementById('result');
            const form = document.getElementById('pitchForm');
            
            btn.disabled = true;
            btn.innerHTML = '⏳ Generating with AI...';
            result.style.display = 'block';
            result.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>🤖 AI is creating your pitch deck...</p>
                    <p><small>This may take 30-60 seconds</small></p>
                </div>
            `;
            
            const formData = new FormData(form);
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.text();
                result.innerHTML = data;
                
            } catch (error) {
                result.innerHTML = `
                    <h3>❌ Error</h3>
                    <p>Failed to generate pitch deck: ${error.message}</p>
                `;
            } finally {
                btn.disabled = false;
                btn.innerHTML = '🚀 Generate Pitch Deck with AI';
            }
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def generate_pitch_deck(self):
        """Generate pitch deck using Gemini API"""
        try:
            topic = ""
            audience = "investors"
            
            if self.command == 'POST':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Debug: print the raw post data
                print(f"Debug - Raw POST data: {post_data[:200]}...")
                
                # Check Content-Type to determine parsing method
                content_type = self.headers.get('Content-Type', '')
                print(f"Debug - Content-Type: {content_type}")
                
                if 'multipart/form-data' in content_type:
                    # Extract boundary
                    boundary_match = re.search(r'boundary=([^;]+)', content_type)
                    if boundary_match:
                        boundary = '--' + boundary_match.group(1)
                        print(f"Debug - Boundary: {boundary}")
                        
                        parsed_data = parse_multipart_form_data(post_data, boundary)
                        print(f"Debug - Parsed multipart data: {parsed_data}")
                        
                        topic = parsed_data.get('topic', '')
                        audience = parsed_data.get('audience', 'investors')
                    else:
                        raise ValueError("Could not find boundary in multipart data")
                else:
                    # URL-encoded form data
                    try:
                        parsed_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
                        print(f"Debug - Parsed URL-encoded data: {parsed_data}")
                        
                        topic = parsed_data.get('topic', [''])[0]
                        audience = parsed_data.get('audience', ['investors'])[0]
                    except Exception as parse_error:
                        print(f"Debug - Parse error: {parse_error}")
                        raise ValueError(f"Could not parse form data: {parse_error}")
            else:
                # GET request - extract from query params
                query = urllib.parse.urlparse(self.path).query
                parsed_data = urllib.parse.parse_qs(query)
                topic = parsed_data.get('topic', ['AI-powered personal finance app'])[0]
                audience = parsed_data.get('audience', ['investors'])[0]
            
            print(f"Debug - Final topic: '{topic}'")
            print(f"Debug - Final audience: '{audience}'")
            
            if not topic or topic.strip() == "":
                raise ValueError("Topic is required - please enter your startup idea")
            
            # Generate content using Gemini
            pitch_data = self.call_gemini_api(topic, audience)
            
            # Create HTML presentation
            html_file = self.create_html_presentation(pitch_data)
            
            # Create PDF from HTML - try multiple methods
            pdf_file = self.create_pdf_from_html(html_file)
            if not pdf_file:
                pdf_file = self.create_browser_based_pdf(html_file)
            
            # Try to create PPTX if available
            pptx_file = None
            if PPTX_AVAILABLE:
                try:
                    pptx_file = self.create_pptx_presentation(pitch_data)
                except Exception as e:
                    print(f"PPTX generation failed: {e}")
            
            # Generate success response
            response_html = f"""
                <h3>🎉 Pitch Deck Generated Successfully!</h3>
                <p><strong>Title:</strong> {pitch_data.get('title', 'Startup Pitch Deck')}</p>
                <p><strong>Slides:</strong> {len(pitch_data.get('slides', []))} slides</p>
                
                <h4>📄 Download Options:</h4>
                <ul>
                    <li><a href="/{html_file}" target="_blank">🌐 View HTML Presentation</a></li>
                    {f'<li><a href="/{pdf_file}" target="_blank">📄 Download PDF (.pdf)</a></li>' if pdf_file else ''}
                    {f'<li><a href="/{pptx_file}" target="_blank">📊 Download PowerPoint (.pptx)</a></li>' if pptx_file else ''}
                </ul>
                
                <h4>📋 Slide Overview:</h4>
                <ol>
                    <li><strong>Title:</strong> {pitch_data.get('company_name', 'Your Company')}</li>
            """
            
            for slide in pitch_data.get('slides', []):
                response_html += f"<li><strong>{slide.get('heading', 'Slide')}</strong></li>"
            
            response_html += """
                </ol>
                
                <div style="margin-top: 20px; padding: 15px; background: #e8f5e8; border-radius: 5px;">
                    <h4>💡 Next Steps:</h4>
                    <ul>
                        <li>📖 Review the generated content</li>
                        <li>✏️ Customize with your specific data</li>
                        <li>🎨 Add your branding and images</li>
                        <li>🎤 Practice your presentation</li>
                    </ul>
                </div>
            """
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(response_html.encode())
            
        except Exception as e:
            error_response = f"""
                <h3>❌ Generation Failed</h3>
                <p><strong>Error:</strong> {str(e)}</p>
                <p>Please check your API key and try again.</p>
                
                <h4>🔧 Troubleshooting:</h4>
                <ul>
                    <li>Ensure your Google API key is valid</li>
                    <li>Check your internet connection</li>
                    <li>Try a simpler topic description</li>
                    <li>Make sure the Gemini API is accessible</li>
                </ul>
            """
            
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(error_response.encode())
    
    def call_gemini_api(self, topic, audience):
        """Call Gemini API to generate pitch deck content"""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        prompt = f"""
        Create a comprehensive startup pitch deck for: {topic}
        Target audience: {audience}
        
        Generate a JSON response with this exact structure:
        {{
            "title": "Company Name - Pitch Deck",
            "company_name": "Company Name", 
            "tagline": "One-line description of what the company does",
            "slides": [
                {{
                    "slide_number": 1,
                    "heading": "Problem Statement",
                    "content": ["Clear bullet point 1", "Clear bullet point 2", "Clear bullet point 3"],
                    "notes": "Speaker notes for this slide explaining key points"
                }}
            ]
        }}
        
        Create exactly these 11 slides:
        1. Problem Statement - What problem are you solving? Include market pain points and user frustrations
        2. Solution Overview - How do you solve it? Your core value proposition
        3. Market Opportunity - Market size (TAM, SAM, SOM), growth trends, target segments
        4. Product/Service - Core features, benefits, unique selling points
        5. Business Model - How you make money, pricing strategy, revenue streams
        6. Traction & Metrics - Current progress, user growth, revenue, key milestones
        7. Competition Analysis - Competitive landscape, your advantages
        8. Team - Key team members, expertise, advisory board
        9. Financial Projections - 3-5 year revenue forecast, unit economics
        10. Funding Ask - How much you're raising, use of funds, timeline
        11. Thank You & Contact - Next steps, contact information
        
        Make content specific, data-driven, and compelling for {audience}.
        Use realistic numbers and industry data where possible.
        Each slide should have 3-5 clear, actionable bullet points.
        """
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
        
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "candidateCount": 1,
                "maxOutputTokens": 8192
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        content = result['candidates'][0]['content']['parts'][0]['text']
        
        # Clean up the response
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        
        return json.loads(content)
    
    def search_pexels_images(self, query, per_page=3):
        """Search for relevant images using Pexels API"""
        pexels_api_key = os.getenv('PEXEL_API_KEY')
        if not pexels_api_key:
            return []
        
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": pexels_api_key}
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": "landscape",
            "size": "medium"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            images = []
            for photo in data.get('photos', []):
                images.append({
                    'url': photo['src']['medium'],
                    'photographer': photo['photographer'],
                    'alt': photo['alt'] or query
                })
            return images
        except Exception as e:
            print(f"Image search failed for '{query}': {e}")
            return []

    def create_html_presentation(self, pitch_data):
        """Create HTML presentation file with images"""
        filename = f"pitch_deck_{hash(str(pitch_data)) % 10000}.html"
        
        # Search for relevant images
        print("🖼️ Searching for relevant images...")
        topic_keywords = pitch_data.get('company_name', '').split() + pitch_data.get('tagline', '').split()
        main_keyword = ' '.join(topic_keywords[:3]) if topic_keywords else 'business startup'
        print(f"   Main keyword: {main_keyword}")
        
        # Get images for different slide types - more comprehensive search
        hero_images = self.search_pexels_images(f"{main_keyword} technology startup", 2)
        business_images = self.search_pexels_images("business meeting team collaboration", 2)
        growth_images = self.search_pexels_images("growth chart success analytics", 2)
        finance_images = self.search_pexels_images("finance money investment banking", 2)
        problem_images = self.search_pexels_images("problem solving challenge difficulty", 2)
        solution_images = self.search_pexels_images("solution innovation technology breakthrough", 2)
        market_images = self.search_pexels_images("market opportunity global business", 2)
        product_images = self.search_pexels_images("product development technology innovation", 2)
        team_images = self.search_pexels_images("team collaboration professionals workplace", 2)
        funding_images = self.search_pexels_images("funding investment capital handshake", 2)
        contact_images = self.search_pexels_images("contact communication thank you", 2)
        
        # Debug: Print image counts
        total_images = len(hero_images + business_images + growth_images + finance_images + problem_images + solution_images + market_images + product_images + team_images + funding_images + contact_images)
        print(f"   Found {total_images} total images across all categories")
        
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0f0f23;
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .slide {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 30px 60px rgba(0,0,0,0.3);
            margin: 40px 0;
            min-height: 700px;
            position: relative;
            page-break-after: always;
            overflow: hidden;
        }}
        
        .slide-number {{
            position: absolute;
            top: 30px;
            right: 40px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 12px 20px;
            border-radius: 30px;
            font-weight: 600;
            font-size: 16px;
            z-index: 10;
        }}
        
        /* Title Slide Styles */
        .title-slide {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
        }}
        
        .title-slide::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('{hero_image}') center/cover;
            opacity: 0.2;
            z-index: 1;
        }}
        
        .title-slide .content {{
            position: relative;
            z-index: 2;
            padding: 60px;
        }}
        
        .title-slide h1 {{
            font-size: 4.5em;
            margin-bottom: 30px;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .title-slide .tagline {{
            font-size: 2.2em;
            opacity: 0.95;
            margin-bottom: 50px;
            font-weight: 300;
        }}
        
        .title-slide .subtitle {{
            font-size: 1.4em;
            opacity: 0.8;
            font-weight: 400;
        }}
        
        /* Regular Slide Styles */
        .regular-slide {{
            padding: 60px;
            display: grid;
            grid-template-columns: 1fr 0.4fr;
            gap: 40px;
            align-items: start;
        }}
        
        .slide-with-image {{
            background: linear-gradient(45deg, #f8f9fa 0%, #ffffff 100%);
        }}
        
        .slide-content {{
            z-index: 2;
        }}
        
        .slide-image {{
            position: relative;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }}
        
        .slide-image img {{
            width: 100%;
            height: 300px;
            object-fit: cover;
        }}
        
        .slide-image .photo-credit {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.7));
            color: white;
            padding: 15px;
            font-size: 0.8em;
            text-align: right;
        }}
        
        h2 {{
            color: #2c3e50;
            font-size: 3em;
            margin-bottom: 40px;
            font-weight: 700;
            position: relative;
        }}
        
        h2::after {{
            content: '';
            position: absolute;
            bottom: -10px;
            left: 0;
            width: 80px;
            height: 4px;
            background: linear-gradient(90deg, #3498db, #2980b9);
            border-radius: 2px;
        }}
        
        .content {{
            font-size: 1.4em;
            line-height: 1.7;
            color: #34495e;
        }}
        
        .content ul {{
            list-style: none;
            padding: 0;
        }}
        
        .content li {{
            margin: 20px 0;
            padding: 15px 0 15px 40px;
            position: relative;
            background: linear-gradient(90deg, transparent, rgba(52,152,219,0.05), transparent);
            border-radius: 8px;
            transition: all 0.3s ease;
        }}
        
        .content li::before {{
            content: "●";
            color: #3498db;
            font-weight: bold;
            font-size: 1.5em;
            position: absolute;
            left: 15px;
            top: 15px;
        }}
        
        .content li:hover {{
            background: linear-gradient(90deg, rgba(52,152,219,0.1), rgba(52,152,219,0.15), rgba(52,152,219,0.1));
            transform: translateX(5px);
        }}
        
        .notes {{
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-left: 6px solid #3498db;
            padding: 25px;
            margin-top: 40px;
            border-radius: 0 15px 15px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .notes::before {{
            content: "💡 Speaker Notes: ";
            font-weight: 700;
            color: #2c3e50;
            font-size: 1.1em;
        }}
        
        .notes-content {{
            margin-top: 10px;
            font-style: italic;
            color: #555;
        }}
        
        /* Special slide themes */
        .problem-slide {{ background: linear-gradient(135deg, #ff7675, #fd79a8); color: white; }}
        .solution-slide {{ background: linear-gradient(135deg, #00b894, #00cec9); color: white; }}
        .market-slide {{ background: linear-gradient(135deg, #fdcb6e, #e17055); color: white; }}
        .product-slide {{ background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: white; }}
        .business-slide {{ background: linear-gradient(135deg, #fd79a8, #fdcb6e); color: white; }}
        .team-slide {{ background: linear-gradient(135deg, #00cec9, #55a3ff); color: white; }}
        .finance-slide {{ background: linear-gradient(135deg, #00b894, #00a085); color: white; }}
        .funding-slide {{ background: linear-gradient(135deg, #e17055, #d63031); color: white; }}
        
        .special-slide h2 {{ color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
        .special-slide .content {{ color: rgba(255,255,255,0.95); }}
        .special-slide .content li::before {{ color: rgba(255,255,255,0.8); }}
        
        /* Special image styling for themed slides */
        .special-image {{
            border: 2px solid rgba(255,255,255,0.3);
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        }}
        
        .special-image img {{
            opacity: 0.9;
        }}
        
        .special-image .photo-credit {{
            background: linear-gradient(transparent, rgba(0,0,0,0.8));
        }}
        
        @media print {{
            body {{ 
                background: white; 
                padding: 0;
                margin: 0;
            }}
            
            .container {{
                max-width: none;
                margin: 0;
            }}
            
            .slide {{ 
                box-shadow: none; 
                margin: 0; 
                page-break-after: always;
                min-height: 100vh;
                max-width: none;
                border-radius: 0;
                background: white !important;
            }}
            
            .slide-number {{
                background: #333 !important;
            }}
            
            /* Ensure images print properly */
            .slide-image img {{
                max-width: 100%;
                height: auto;
            }}
            
            /* Hide photo credits in print */
            .photo-credit {{
                display: none;
            }}
            
            /* Better text contrast for print */
            .special-slide {{
                color: white !important;
            }}
            
            .special-slide h2,
            .special-slide .content {{
                color: white !important;
            }}
        }}
        
        @media (max-width: 1024px) {{
            .regular-slide {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}
            
            .slide-image {{
                order: -1;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {slides_html}
    </div>
</body>
</html>'''
        
        slides_html = ""
        hero_image_url = hero_images[0]['url'] if hero_images else ''
        
        # Title slide with hero image - matching PDF design
        title_slide = f'''
            <div class="slide title-slide">
                <div class="slide-number">1</div>
                <div class="content">
                    <h1>{pitch_data.get("company_name", "Startup Name")}</h1>
                    <div class="tagline">{pitch_data.get("tagline", "Your tagline here")}</div>
                    <div class="subtitle">Investor Pitch Deck</div>
                </div>
            </div>
        '''
        slides_html += title_slide
        
        # Define slide themes based on content
        slide_themes = {
            "problem": "problem-slide special-slide",
            "solution": "solution-slide special-slide", 
            "market": "market-slide special-slide",
            "product": "product-slide special-slide",
            "business": "business-slide special-slide",
            "team": "team-slide special-slide",
            "financial": "finance-slide special-slide",
            "funding": "funding-slide special-slide"
        }
        
        # Image pools for different slide types
        image_pools = {
            "problem": problem_images,
            "solution": solution_images,
            "market": market_images,
            "product": product_images,
            "business": business_images,
            "team": team_images,
            "growth": growth_images,
            "traction": growth_images,
            "competition": business_images,
            "finance": finance_images,
            "financial": finance_images,
            "funding": funding_images,
            "thank": contact_images,
            "contact": contact_images,
            "default": hero_images
        }
        
        # Content slides with smart theming and images
        for i, slide in enumerate(pitch_data.get("slides", [])):
            content_items = ""
            for item in slide.get("content", []):
                content_items += f"<li>{item}</li>"
            
            # Determine slide theme based on heading
            heading_lower = slide.get("heading", "").lower()
            slide_theme = "regular-slide"
            slide_image = None
            
            # Apply theme based on content
            for theme_key, theme_class in slide_themes.items():
                if theme_key in heading_lower:
                    slide_theme = theme_class
                    break
            
            # Select appropriate image - EVERY slide gets an image
            # First try to match specific keywords
            matched_image = None
            for keyword, images in image_pools.items():
                if keyword in heading_lower and images:
                    matched_image = images[i % len(images)]  # Rotate through available images
                    break
            
            # If no specific match, use contextual fallbacks
            if not matched_image:
                if "problem" in heading_lower or "challenge" in heading_lower:
                    matched_image = problem_images[0] if problem_images else None
                elif "solution" in heading_lower or "overview" in heading_lower:
                    matched_image = solution_images[0] if solution_images else None
                elif "market" in heading_lower or "opportunity" in heading_lower:
                    matched_image = market_images[0] if market_images else None
                elif "product" in heading_lower or "service" in heading_lower:
                    matched_image = product_images[0] if product_images else None
                elif "business" in heading_lower or "model" in heading_lower:
                    matched_image = business_images[0] if business_images else None
                elif "team" in heading_lower:
                    matched_image = team_images[0] if team_images else None
                elif "traction" in heading_lower or "metrics" in heading_lower or "growth" in heading_lower:
                    matched_image = growth_images[0] if growth_images else None
                elif "competition" in heading_lower or "analysis" in heading_lower:
                    matched_image = business_images[0] if business_images else None
                elif "financial" in heading_lower or "projections" in heading_lower:
                    matched_image = finance_images[0] if finance_images else None
                elif "funding" in heading_lower or "ask" in heading_lower:
                    matched_image = funding_images[0] if funding_images else None
                elif "thank" in heading_lower or "contact" in heading_lower:
                    matched_image = contact_images[0] if contact_images else None
            
            # Final fallback - ensure EVERY slide has an image
            if not matched_image:
                # Cycle through all available images
                all_images = hero_images + business_images + growth_images + finance_images
                if all_images:
                    matched_image = all_images[i % len(all_images)]
            
            slide_image = matched_image
            
            # Build slide HTML - ALL slides get images now
            if "special-slide" in slide_theme and slide_image:
                # Special themed slide WITH image
                slide_html = f'''
                    <div class="slide {slide_theme}">
                        <div class="slide-number">{slide.get("slide_number", 1) + 1}</div>
                        <div class="regular-slide">
                            <div class="slide-content">
                                <h2>{slide.get("heading", "Slide Title")}</h2>
                                <div class="content">
                                    <ul>{content_items}</ul>
                                </div>
                            </div>
                            <div class="slide-image special-image">
                                <img src="{slide_image['url']}" alt="{slide_image['alt']}" loading="lazy">
                                <div class="photo-credit">Photo by {slide_image['photographer']} on Pexels</div>
                            </div>
                        </div>
                    </div>
                '''
            elif slide_image:
                # Regular slide with image
                slide_html = f'''
                    <div class="slide slide-with-image">
                        <div class="slide-number">{slide.get("slide_number", 1) + 1}</div>
                        <div class="regular-slide">
                            <div class="slide-content">
                                <h2>{slide.get("heading", "Slide Title")}</h2>
                                <div class="content">
                                    <ul>{content_items}</ul>
                                </div>
                            </div>
                            <div class="slide-image">
                                <img src="{slide_image['url']}" alt="{slide_image['alt']}" loading="lazy">
                                <div class="photo-credit">Photo by {slide_image['photographer']} on Pexels</div>
                            </div>
                        </div>
                    </div>
                '''
            else:
                # Fallback slide without image (should rarely happen now)
                slide_html = f'''
                    <div class="slide {slide_theme}">
                        <div class="slide-number">{slide.get("slide_number", 1) + 1}</div>
                        <div class="regular-slide">
                            <div class="slide-content">
                                <h2>{slide.get("heading", "Slide Title")}</h2>
                                <div class="content">
                                    <ul>{content_items}</ul>
                                </div>
                            </div>
                        </div>
                    </div>
                '''
            
            # Add speaker notes if available
            if slide.get("notes"):
                notes_section = f'''
                    <div class="notes">
                        <div class="notes-content">{slide["notes"]}</div>
                    </div>
                '''
                slide_html = slide_html.replace('</div>\n                    </div>', f'{notes_section}</div>\n                    </div>')
            
            slides_html += slide_html
        
        # Add client-side PDF generation script
        pdf_script = '''
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <script>
            function downloadPDF() {
                const { jsPDF } = window.jspdf;
                const pdf = new jsPDF('l', 'mm', 'a4'); // landscape A4
                const slides = document.querySelectorAll('.slide');
                let promises = [];
                
                slides.forEach((slide, index) => {
                    promises.push(
                        html2canvas(slide, {
                            scale: 2,
                            useCORS: true,
                            allowTaint: true,
                            backgroundColor: null
                        }).then(canvas => {
                            const imgData = canvas.toDataURL('image/jpeg', 0.9);
                            if (index > 0) pdf.addPage();
                            
                            // A4 landscape: 297mm x 210mm
                            const imgWidth = 297;
                            const imgHeight = (canvas.height * imgWidth) / canvas.width;
                            
                            pdf.addImage(imgData, 'JPEG', 0, 0, imgWidth, Math.min(imgHeight, 210));
                        })
                    );
                });
                
                Promise.all(promises).then(() => {
                    pdf.save('pitch_deck.pdf');
                });
            }
        </script>
        '''
        
        # Add download button after the container
        download_button = '''
        <div style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
            <button onclick="downloadPDF()" style="
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                border: none;
                padding: 15px 25px;
                border-radius: 50px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                box-shadow: 0 10px 25px rgba(102,126,234,0.3);
                transition: all 0.3s ease;
            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                📄 Download PDF
            </button>
        </div>
        '''
        
        final_html = html_template.format(
            title=pitch_data.get("title", "Startup Pitch Deck"),
            hero_image=hero_image_url,
            slides_html=slides_html
        )
        
        # Insert the PDF script and button before closing body tag
        final_html = final_html.replace('</body>', f'{pdf_script}{download_button}</body>')
        
        # Write to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        return filename
    
    def create_pdf_from_html(self, html_file):
        """Convert HTML presentation to PDF using available methods"""
        pdf_filename = html_file.replace('.html', '.pdf')
        
        # Try Playwright first (most reliable for complex CSS)
        try:
            print("📄 Converting to PDF using Playwright...")
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(f'file://{os.path.abspath(html_file)}')
                page.pdf(
                    path=pdf_filename,
                    format='A4',
                    landscape=True,
                    margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'},
                    print_background=True
                )
                browser.close()
                print(f"✅ PDF created with Playwright: {pdf_filename}")
                return pdf_filename
                
        except ImportError:
            print("⚠️ Playwright not available")
        except Exception as e:
            print(f"❌ Playwright PDF generation failed: {e}")
        
        # Try wkhtmltopdf
        try:
            print("📄 Converting to PDF using wkhtmltopdf...")
            result = subprocess.run([
                'wkhtmltopdf',
                '--page-size', 'A4',
                '--orientation', 'Landscape',
                '--margin-top', '0',
                '--margin-bottom', '0',
                '--margin-left', '0',
                '--margin-right', '0',
                '--disable-smart-shrinking',
                '--print-media-type',
                '--enable-local-file-access',
                html_file,
                pdf_filename
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"✅ PDF created with wkhtmltopdf: {pdf_filename}")
                return pdf_filename
            else:
                print(f"❌ wkhtmltopdf error: {result.stderr}")
                
        except FileNotFoundError:
            print("⚠️ wkhtmltopdf not found")
        except subprocess.TimeoutExpired:
            print("❌ wkhtmltopdf timed out")
        except Exception as e:
            print(f"❌ wkhtmltopdf failed: {e}")
        
        return None
    
    def create_browser_based_pdf(self, html_file):
        """Create PDF using browser-based rendering (Chrome/Puppeteer)"""
        pdf_filename = html_file.replace('.html', '.pdf')
        
        try:
            # Try Chrome headless first
            print("📄 Converting to PDF using Chrome headless...")
            
            result = subprocess.run([
                'google-chrome',
                '--headless',
                '--disable-gpu',
                '--print-to-pdf=' + pdf_filename,
                '--print-to-pdf-no-header',
                '--virtual-time-budget=5000',
                f'file://{os.path.abspath(html_file)}'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(pdf_filename):
                print(f"✅ PDF created with Chrome: {pdf_filename}")
                return pdf_filename
            
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        try:
            # Try Chromium as fallback
            print("📄 Trying Chromium...")
            
            result = subprocess.run([
                'chromium-browser',
                '--headless',
                '--disable-gpu',
                '--print-to-pdf=' + pdf_filename,
                '--print-to-pdf-no-header',
                '--virtual-time-budget=5000',
                f'file://{os.path.abspath(html_file)}'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(pdf_filename):
                print(f"✅ PDF created with Chromium: {pdf_filename}")
                return pdf_filename
                
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
            
        print("❌ Browser-based PDF generation failed")
        return None
    
    def create_pptx_presentation(self, pitch_data):
        """Create PowerPoint presentation if pptx is available"""
        if not PPTX_AVAILABLE:
            return None
        
        # Use the existing pptx_helper if available
        # This would integrate with the existing PowerPoint generation
        
        return None

def main():
    print("🚀 Starting Gemini Pitch Deck Generator Web Server")
    print("=" * 50)
    
    # Check for PDF generation capabilities
    pdf_methods = []
    
    try:
        from playwright.sync_api import sync_playwright
        pdf_methods.append("Playwright")
    except ImportError:
        pass
    
    try:
        result = subprocess.run(['wkhtmltopdf', '--version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            pdf_methods.append("wkhtmltopdf")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    if pdf_methods:
        print(f"✅ PDF generation available via: {', '.join(pdf_methods)}")
    else:
        print("⚠️ Server-side PDF generation not available")
        print("   Client-side PDF generation will be available in the browser")
        print("\n💡 To enable server-side PDF generation, install:")
        print("   Option 1: pip install playwright && playwright install chromium")
        print("   Option 2: brew install wkhtmltopdf (macOS)")
        print("   Option 3: sudo apt-get install wkhtmltopdf (Ubuntu/Debian)")
        print()
    
    # Check API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in .env file")
        print("Please add your Google API key to the .env file")
        return
    
    print(f"✅ Google API key found: {api_key[:20]}...")
    
    if PPTX_AVAILABLE:
        print("✅ PowerPoint generation available")
    else:
        print("⚠️ PowerPoint generation not available (missing dependencies)")
    
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, PitchDeckHandler)
    
    print(f"\\n🌐 Server running at: http://localhost:8080")
    print("💡 Open this URL in your browser to use the pitch deck generator")
    print("🛑 Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n\\n👋 Server stopped. Thanks for using Gemini Pitch Deck Generator!")

if __name__ == "__main__":
    main()