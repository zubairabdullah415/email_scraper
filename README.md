# 📧 Email Scraper for Restaurant Websites

Extract emails from 2,000+ restaurant websites and populate your Google Sheet automatically.

---

## 🎯 What This Does

1. **Reads** websites from Column G in your Google Sheet
2. **Scrapes** each website for email addresses by:
   - Finding `mailto:` links
   - Searching page text for `@` patterns
   - Checking contact/about pages
3. **Writes** found emails to Column N
4. **Updates** status in Column O

---

## 🚀 Quick Setup

### Step 1: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 2: Update Your .env File

Add this line to your `.env`:

```bash
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/15LzW3reW0CS9gtaFj9uO47mCl-9nd7THhEuray4H86c/edit
```

(You already have `GOOGLE_CREDS_PATH` and `credentials.json` from the calling agent)

### Step 3: Run the Scraper

```powershell
python email_scraper.py
```

---

## 📊 Your Google Sheet Structure

The scraper expects:

| Column | Header | Purpose |
|--------|--------|---------|
| A | Restaurant Name | For logging |
| G | Website | **Source URLs** |
| N | Email | **Scraped emails** (output) |
| O | Notes | Status updates (output) |

---

## ⚙️ Configuration Options

### Process Specific Rows

Edit `email_scraper.py`, line at bottom:

```python
await scraper.run(
    start_row=2,      # Start from row 2 (after header)
    end_row=100,      # End at row 100 (change or use None for all)
    batch_size=50     # Process 50 rows at a time
)
```

### Examples:

**Test with first 10 restaurants:**
```python
await scraper.run(start_row=2, end_row=11, batch_size=10)
```

**Process all 2,000:**
```python
await scraper.run(start_row=2, end_row=None, batch_size=50)
```

**Resume from row 500:**
```python
await scraper.run(start_row=500, end_row=None, batch_size=50)
```

---

## 🎯 Features

### Smart Email Detection
- ✅ Finds `mailto:` links
- ✅ Extracts emails from page text
- ✅ Checks contact/about pages automatically
- ✅ Filters out fake emails (example.com, test@)
- ✅ Removes image file extensions (.png@...)

### Polite Scraping
- ⏱️ 0.5s delay between pages
- ⏱️ 1s delay between websites
- ⏱️ 5s delay between batches
- 🚫 Only checks 3 pages per site max
- 🚫 10s timeout per page

### Robust Error Handling
- ✅ Skips websites that are down
- ✅ Handles timeouts gracefully
- ✅ Continues on errors
- ✅ Updates Google Sheets in real-time

---

## 📈 Expected Performance

| Metric | Value |
|--------|-------|
| Speed | ~100-150 websites/hour |
| Success Rate | ~60-70% (many sites don't list emails) |
| Time for 2,000 | ~13-20 hours |

**Recommendation:** Run overnight or in batches

---

## 🎮 Usage Examples

### Test Run (First 10)

```powershell
# Edit email_scraper.py, change the last lines to:
# await scraper.run(start_row=2, end_row=11, batch_size=10)

python email_scraper.py
```

### Full Run (All 2,000)

```powershell
# Keep defaults or set:
# await scraper.run(start_row=2, end_row=None, batch_size=50)

python email_scraper.py
```

### Resume After Interruption

```powershell
# Check your sheet, see which row you stopped at
# Edit email_scraper.py:
# await scraper.run(start_row=523, end_row=None, batch_size=50)

python email_scraper.py
```

---

## 📊 Output Format

### Column N (Email):
```
contact@restaurant.com
info@restaurant.com; bookings@restaurant.com
manager@restaurant.com
[empty if none found]
```

### Column O (Status):
```
Email found
No email found
```

---

## 🛠️ Advanced Customization

### Add More Contact Page Variations

In `email_scraper.py`, line 33:

```python
self.contact_pages = [
    '', 'contact', 'contact-us', 'about', 'about-us', 
    'team', 'locations', 'reach-us', 'get-in-touch',
    'info', 'kontakt', 'contacto'  # Add your own!
]
```

### Change Timeout

Line 94:

```python
timeout=aiohttp.ClientTimeout(total=10),  # Change to 15, 20, etc.
```

### Process Faster (Less Polite)

Line 123:

```python
await asyncio.sleep(0.5)  # Change to 0.2 (faster but riskier)
```

---

## 🔍 Monitoring Progress

The scraper logs everything:

```
✅ Row 5: Found 2 email(s): info@pizza.com; orders@pizza.com
❌ Row 8: No emails found
✅ Row 12: Found 1 email(s): contact@thai.com
```

Watch the console for real-time updates!

---

## ⚠️ Important Notes

### 1. Rate Limiting
- Google Sheets API: 100 requests/100 seconds
- The scraper handles this with built-in delays
- If you hit limits, increase `batch_size` delays

### 2. Website Blocking
- Some sites may block scrapers
- The script uses a real browser User-Agent
- If blocked, those sites will just show "No email found"

### 3. Privacy & Ethics
- ✅ Only scrapes public contact information
- ✅ Respects robots.txt (implicitly via politeness)
- ✅ Doesn't overwhelm servers with requests
- ⚠️ Use responsibly and follow local laws

### 4. False Positives
- Some emails might be support@platform.com (hosting)
- Some might be info@emailservice.com (mailing)
- Manually verify important contacts

---

## 🐛 Troubleshooting

### "Credentials file not found"
```powershell
# Make sure credentials.json is in the project folder
ls credentials.json
```

### "Permission denied" on Google Sheets
```powershell
# Make sure the service account email has Editor access to the sheet
# Check credentials.json for the email address
# Share the Google Sheet with that email
```

### "No emails found" for all sites
```powershell
# Test with a known site:
# Add a row with Website: https://www.example-restaurant.com
# Many restaurants don't list emails publicly!
```

### Script runs but sheet doesn't update
```powershell
# Check if you're looking at the right sheet/tab
# Make sure column headers match exactly
# "Website" in column G, "Email" in column N
```

---

## 📈 Optimization Tips

### For Faster Processing

1. **Increase batch size:**
   ```python
   batch_size=100  # Process more at once
   ```

2. **Reduce delays:**
   ```python
   await asyncio.sleep(0.3)  # Faster between sites
   ```

3. **Limit pages checked:**
   ```python
   urls_to_try[:2]  # Only check 2 pages instead of 3
   ```

### For Better Results

1. **Check more pages:**
   ```python
   urls_to_try[:5]  # Check 5 pages per site
   ```

2. **Increase timeout:**
   ```python
   timeout=aiohttp.ClientTimeout(total=20),
   ```

3. **Add custom contact pages for your region:**
   ```python
   self.contact_pages = ['', 'contact', 'kontakt', 'contacto']
   ```

---

## 🎯 Next Steps After Scraping

Once you have emails:

1. **Clean the data:**
   - Remove obvious spam emails
   - Verify important contacts manually

2. **Use for cold calling:**
   - Import into your CRM
   - Send introduction emails
   - Follow up with calls

3. **Segment by response:**
   - Mark which emails bounced
   - Track opens/clicks
   - Focus on engaged prospects

---

## 💡 Pro Tips

1. **Run in batches:**
   - Day 1: Rows 2-500
   - Day 2: Rows 501-1000
   - etc.

2. **Test first:**
   - Always test with 10-20 rows first
   - Verify output format looks good

3. **Monitor for blocks:**
   - If many sites show "No email", you might be blocked
   - Increase delays or pause scraping

4. **Backup your sheet:**
   - Make a copy before running
   - File → Make a copy

---

## 🤝 Integration with Cold Calling Agent

Once emails are scraped:

1. Use `email_scraper.py` to get emails (Column N)
2. Use `dialer.py` to make calls (Column K - Phone)
3. Have both email and phone for each restaurant!

Perfect for multi-channel outreach! 📧📞

---

**Ready to scrape 2,000 emails? Run `python email_scraper.py` now!** 🚀
