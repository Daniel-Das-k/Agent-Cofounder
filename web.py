import asyncio
import os
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler

async def main():
    # Create an instance of AsyncWebCrawler
    async with AsyncWebCrawler() as crawler:
        # URL to crawl
        url = "https://www.vcsheet.com/fund/500-global"
        
        # Extract subdirectory name from URL
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        subdir_name = path_parts[-1] if path_parts[-1] else 'home'
        
        # Create vcdata directory if it doesn't exist
        os.makedirs("vcdata", exist_ok=True)
        
        # Run the crawler on a URL
        result = await crawler.arun(url=url)

        # Save the extracted content to a text file with subdirectory name
        filename = f"vcdata/browse_funds/{subdir_name}.txt"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(result.markdown)
        
        print(f"Data has been saved to {filename}")

# Run the async main function
asyncio.run(main())
