import urllib.parse
from typing import List, Dict
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from datetime import datetime
from base_scraper import JobScraper

class WttjScraper(JobScraper):
    def fetch_jobs(self, keyword: str, location: str) -> List[Dict]:
        print(f"Starting headless browser for Welcome to the Jungle: '{keyword}'...")
        
        # WttJ uses URL parameters for search
        safe_keyword = urllib.parse.quote(keyword)
        url = f"https://www.welcometothejungle.com/fr/jobs?query={safe_keyword}"
        
        parsed_jobs = []

        # Start the Playwright context manager
        with sync_playwright() as p:
            # 1. TURN OFF HEADLESS MODE and slow it down
            browser = p.chromium.launch(headless=False, slow_mo=500)
            page = browser.new_page()
            
            try:
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(3000) # Wait 3 seconds
                
                html_content = page.content()
                
                # 2. DUMP THE HTML TO A FILE FOR INSPECTION
                with open("wttj_debug.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print("Saved page source to wttj_debug.html")
                
            except Exception as e:
                print(f"Headless browser error: {e}")
                return []
            finally:
                browser.close()

        # Now we parse the rendered HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # WttJ changes their CSS classes frequently (they use styled-components).
        # To be robust, we look for 'a' tags that contain '/jobs/' in the href, 
        # as this URL structure rarely changes.
        job_links = soup.find_all('a', href=True)
        
        for link in job_links:
            href = link['href']
            
            # Identify job detail links
            if '/fr/companies/' in href and '/jobs/' in href:
                # Deduplicate and construct full URL
                full_url = f"https://www.welcometothejungle.com{href}"
                
                # We can usually extract the title from the text of the link itself
                # or from an 'h4' or 'span' inside it. We take the raw text.
                title_text = link.text.strip()
                
                # If the link has text, it's likely the primary title link
                if title_text and len(title_text) > 3:
                    # Extract company name from the URL path (fallback method)
                    # e.g., /fr/companies/acme-corp/jobs/...
                    company_slug = href.split('/companies/')[1].split('/')[0]
                    company_name = company_slug.replace('-', ' ').title()

                    job_data = {
                        "title": title_text,
                        "company": company_name,
                        "description": "Requires navigating to full page to extract.",
                        "url": full_url,
                        "date_posted": datetime.now().isoformat()[:10]
                    }
                    parsed_jobs.append(job_data)

        # Remove duplicate URLs (WttJ sometimes has multiple links to the same job card)
        unique_jobs = {job['url']: job for job in parsed_jobs}.values()
        final_jobs_list = list(unique_jobs)
        
        print(f"Found {len(final_jobs_list)} unique jobs.")
        return final_jobs_list