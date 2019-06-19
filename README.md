# app-ads-crawler
Given a list of bundle ids and the os, find the app-ads.txt file online and scan for a particular listing.

## Steps
- Parse bundle id's and info from CSV
- Attempt to get developer url from Store
- Given developer url, attempt to get app-ads-txt from developer site
- Check app-ads.txt for company info
- Produce csv results
