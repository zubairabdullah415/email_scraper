"""
Email Scraper for Restaurant Websites
Reads URLs from Google Sheet column G, scrapes emails, writes to column N
"""

import os
import re
import time
import logging
import asyncio
import aiohttp
from typing import List, Set, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailScraper:
    """Scrapes emails from restaurant websites"""
    
    def __init__(self, sheet_url: str, creds_path: str):
        self.sheet_url = sheet_url
        self.creds_path = creds_path
        self.sheet = None
        self.worksheet = None
        self._init_google_sheets()
        
        # Email regex pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Common pages to check for contact info
        self.contact_pages = [
            '', 'contact', 'contact-us', 'about', 'about-us', 
            'team', 'locations', 'reach-us', 'get-in-touch'
        ]
    
    def _init_google_sheets(self):
        """Initialize Google Sheets connection"""
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            creds = Credentials.from_service_account_file(
                self.creds_path,
                scopes=scope
            )
            
            client = gspread.authorize(creds)
            self.sheet = client.open_by_url(self.sheet_url)
            self.worksheet = self.sheet.get_worksheet(0)
            
            logger.info(f"✅ Connected to Google Sheet: {self.sheet.title}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Google Sheets: {e}")
            raise
    
    def extract_emails_from_text(self, text: str) -> Set[str]:
        """Extract email addresses from text"""
        if not text:
            return set()
        
        emails = set(self.email_pattern.findall(text))
        
        # Filter out common false positives
        filtered_emails = set()
        for email in emails:
            email_lower = email.lower()
            # Skip common image/asset file extensions
            if any(email_lower.endswith(ext) for ext in ['.png', '.jpg', '.gif', '.svg', '.css', '.js']):
                continue
            # Skip example/placeholder emails
            if any(word in email_lower for word in ['example.com', 'domain.com', 'test@', 'admin@localhost']):
                continue
            filtered_emails.add(email)
        
        return filtered_emails
    
    def extract_mailto_links(self, soup: BeautifulSoup) -> Set[str]:
        """Extract emails from mailto: links"""
        emails = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('mailto:'):
                # Extract email from mailto:email@domain.com
                email = href.replace('mailto:', '').split('?')[0].strip()
                if self.email_pattern.match(email):
                    emails.add(email)
        
        return emails
    
    async def scrape_url(self, session: aiohttp.ClientSession, url: str) -> Set[str]:
        """Scrape emails from a single URL"""
        
        if not url or not url.startswith('http'):
            return set()
        
        all_emails = set()
        
        try:
            # Try base URL and common contact pages
            urls_to_try = [url]
            
            # Add contact pages
            base_url = url.rstrip('/')
            for page in self.contact_pages[1:]:  # Skip empty string (already have base)
                urls_to_try.append(f"{base_url}/{page}")
            
            for try_url in urls_to_try[:3]:  # Limit to 3 pages to be polite
                try:
                    async with session.get(
                        try_url,
                        timeout=aiohttp.ClientTimeout(total=10),
                        allow_redirects=True
                    ) as response:
                        
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Extract from mailto links
                            mailto_emails = self.extract_mailto_links(soup)
                            all_emails.update(mailto_emails)
                            
                            # Extract from page text
                            text = soup.get_text()
                            text_emails = self.extract_emails_from_text(text)
                            all_emails.update(text_emails)
                            
                            # If we found emails, no need to check more pages
                            if all_emails:
                                break
                    
                    # Small delay between requests to be polite
                    await asyncio.sleep(0.5)
                    
                except asyncio.TimeoutError:
                    logger.debug(f"Timeout: {try_url}")
                    continue
                except Exception as e:
                    logger.debug(f"Error fetching {try_url}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
        
        return all_emails
    
    async def process_batch(self, start_row: int, end_row: int):
        """Process a batch of websites"""
        
        logger.info(f"Processing rows {start_row} to {end_row}")
        
        # Get data
        records = self.worksheet.get_all_records()
        
        # Create async session with headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            
            for idx in range(start_row - 2, min(end_row - 1, len(records))):
                row = records[idx]
                row_number = idx + 2  # +2 because of header and 0-indexing
                
                # Get website from column G
                website = row.get('Website', '').strip()
                
                # Check if email already exists in column N
                existing_email = row.get('Email', '').strip()
                if existing_email:
                    logger.info(f"Row {row_number}: Email already exists, skipping")
                    continue
                
                if not website:
                    logger.info(f"Row {row_number}: No website, skipping")
                    continue
                
                restaurant_name = row.get('Restaurant Name', 'Unknown')
                
                logger.info(f"Row {row_number}: Scraping {restaurant_name} - {website}")
                
                # Scrape emails
                emails = await self.scrape_url(session, website)
                
                if emails:
                    # Join multiple emails with semicolon
                    emails_str = '; '.join(sorted(emails))
                    
                    # Update column N (column 14)
                    self.worksheet.update_cell(row_number, 14, emails_str)
                    
                    logger.info(f"✅ Row {row_number}: Found {len(emails)} email(s): {emails_str}")
                    
                    # Update status in column O (column 15)
                    self.worksheet.update_cell(row_number, 15, "Email found")
                else:
                    logger.info(f"❌ Row {row_number}: No emails found")
                    self.worksheet.update_cell(row_number, 15, "No email found")
                
                # Rate limiting - be polite to Google Sheets API
                await asyncio.sleep(1)
    
    async def run(self, start_row: int = 2, end_row: Optional[int] = None, batch_size: int = 50):
        """Run the email scraper"""
        
        logger.info("=" * 70)
        logger.info("🔍 EMAIL SCRAPER STARTING")
        logger.info("=" * 70)
        
        # Get total rows
        records = self.worksheet.get_all_records()
        total_rows = len(records) + 1  # +1 for header
        
        if end_row is None or end_row > total_rows:
            end_row = total_rows
        
        logger.info(f"Total rows: {total_rows}")
        logger.info(f"Processing rows {start_row} to {end_row}")
        logger.info(f"Batch size: {batch_size}")
        logger.info("=" * 70)
        
        # Process in batches
        for batch_start in range(start_row, end_row + 1, batch_size):
            batch_end = min(batch_start + batch_size - 1, end_row)
            
            logger.info(f"\n📦 BATCH: Rows {batch_start} to {batch_end}")
            
            await self.process_batch(batch_start, batch_end)
            
            logger.info(f"✅ Batch complete")
            
            # Pause between batches
            if batch_end < end_row:
                logger.info("⏸️  Pausing 5 seconds before next batch...")
                await asyncio.sleep(5)
        
        logger.info("\n" + "=" * 70)
        logger.info("🎉 EMAIL SCRAPING COMPLETE!")
        logger.info("=" * 70)


async def main():
    """Main execution"""
    
    # Configuration
    SHEET_URL = os.getenv("GOOGLE_SHEET_URL", "https://docs.google.com/spreadsheets/d/15LzW3reW0CS9gtaFj9uO47mCl-9nd7THhEuray4H86c/edit")
    CREDS_PATH = os.getenv("GOOGLE_CREDS_PATH", "credentials.json")
    
    # Verify credentials file exists
    if not os.path.exists(CREDS_PATH):
        logger.error(f"❌ Credentials file not found: {CREDS_PATH}")
        logger.error("Please download credentials.json from Google Cloud Console")
        return
    
    # Create scraper
    scraper = EmailScraper(SHEET_URL, CREDS_PATH)
    
    # Run scraper
    # Start from row 2 (after header), process all rows, 50 at a time
    await scraper.run(
        start_row=2,      # Start after header
        end_row=11,     # None = process all rows
        batch_size=10     # Process 50 rows at a time
    )


if __name__ == "__main__":
    asyncio.run(main())
