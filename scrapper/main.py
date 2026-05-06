import asyncio
from wttj_scraper import WttjScraper
from db_manager import DatabaseManager 

async def run_pipeline():
    print("Starting HunterHub Scraper Pipeline...")
    db = DatabaseManager()
    
    total_scraped = 0
    new_inserted = 0

    try:
        scraper = WttjScraper(headless=False)
        print("Initiating search stream...")
        
        async for job in scraper.fetch_jobs(keyword="Data Engineer", location="Remote"):
            total_scraped += 1
            
            try:
                is_new = db.save_job(job)
                if is_new:
                    new_inserted += 1
                    print(f"  [+] NEW JOB SAVED: {job['title']} @ {job['company']}")
                else:
                    print(f"  [-] Skipped Duplicate: {job['title']} @ {job['company']}")
                    
            except Exception as db_err:
                print(f"  [!] Database Error: {db_err}")

        print("\n=== Pipeline Finished Successfully ===")
        print(f"Total jobs scraped: {total_scraped}")
        print(f"New jobs added to DB: {new_inserted}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_pipeline())