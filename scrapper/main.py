from wttj_scraper import WttjScraper
from db_manager import DatabaseManager

def run_pipeline():
    print("Starting HunterHub Scraper Pipeline...")

    # 1. Initialize and run the scraper
    scraper = WttjScraper()
    scraped_jobs = scraper.fetch_jobs(keyword="Data Engineer", location="Remote")
    
    # 2. Check if we actually got data
    if not scraped_jobs:
        print("No jobs found. Exiting.")
        return

    # 3. Connect to Database and save
    db = DatabaseManager()
    try:
        db.save_jobs(scraped_jobs)
    except Exception as e:
        print(f"Error saving to database: {e}")
    finally:
        # Always make sure we close the connection!
        db.close()

if __name__ == "__main__":
    run_pipeline()