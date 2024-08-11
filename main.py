from playwright.sync_api import sync_playwright
import pandas as pd
import argparse
import os
import sys
import re
from bs4 import BeautifulSoup


class Business:
    """Holds business data"""
    
    def __init__(self):
        self.name = None
        self.address = None
        self.website = None
        self.phone_number = None
        self.reviews_count = None
        self.reviews_average = None
        self.latitude = None
        self.longitude = None

    def to_dict(self):
        """Convert the Business instance to a dictionary"""
        return {
            'name': self.name,
            'address': self.address,
            'website': self.website,
            'phone_number': self.phone_number,
            'reviews_count': self.reviews_count,
            'reviews_average': self.reviews_average,
            'latitude': self.latitude,
            'longitude': self.longitude
        }

class BusinessList:
    """Holds a list of Business objects and saves to both Excel and CSV"""
    
    def __init__(self):
        self.business_list = []
        self.save_at = 'output'

    def dataframe(self):
        """Transform business_list to pandas dataframe"""
        return pd.DataFrame([business.to_dict() for business in self.business_list])

    def save_to_excel(self, filename):
        """Save pandas dataframe to Excel (xlsx) file"""
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_excel(f"{self.save_at}/{filename}.xlsx", index=False)

    def save_to_csv(self, filename):
        """Save pandas dataframe to CSV file"""
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_csv(f"{self.save_at}/{filename}.csv", index=False)

def extract_coordinates_from_url(url):
    """Helper function to extract coordinates from URL"""
    coordinates = url.split('/@')[-1].split('/')[0]
    return float(coordinates.split(',')[0]), float(coordinates.split(',')[1])

def parse_review_text(review_text):
    """Extract the number of 1-star reviews from review text"""
    match = re.search(r'(\d+)\s*1-star', review_text, re.IGNORECASE)
    return int(match.group(1)) if match else 0

def main():
    ########
    # Input 
    ########
    
    # Read search terms from arguments or file
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-t", "--total", type=int)
    parser.add_argument("-r", "--regions", type=str, nargs='+', help="List of regions to search in")
    args = parser.parse_args()

    if args.search:
        search_list = [args.search]
    else:
        search_list = []
        input_file_name = 'input.txt'
        input_file_path = os.path.join(os.getcwd(), input_file_name)
        if os.path.exists(input_file_path):
            with open(input_file_path, 'r') as file:
                search_list = file.read().splitlines()

    if not search_list:
        print('Error: You must either pass the -s search argument or add searches to input.txt')
        sys.exit()

    total = args.total if args.total else 1_000
    regions = args.regions if args.regions else ['USA', 'Australia', 'UK', 'New Zealand']

    ###########
    # Scraping
    ###########
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://www.google.com/maps", timeout=60000)
        page.wait_for_timeout(5000)

        for region in regions:
            for search_for_index, search_for in enumerate(search_list):
                search_for_index = search_for_index +1
                search_term = f"{search_for} {region}"
                print(f"-----\n{search_for_index} - {search_term}".strip())

                page.locator('//input[@id="searchboxinput"]').fill(search_term)
                page.wait_for_timeout(3000)
                page.keyboard.press("Enter")
                page.wait_for_timeout(5000)

                # Scrolling
                page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

                previously_counted = 0
                while True:
                    page.mouse.wheel(0, 10000)
                    page.wait_for_timeout(3000)

                    if page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count() >= total:
                        listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:total]
                        listings = [listing.locator("xpath=..") for listing in listings]
                        print(f"Total Scraped: {len(listings)}")
                        break
                    else:
                        if page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count() == previously_counted:
                            listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
                            print(f"Arrived at all available\nTotal Scraped: {len(listings)}")
                            break
                        else:
                            previously_counted = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
                            print(f"Currently Scraped: {previously_counted}")

                business_list = BusinessList()

                for listing in listings:
                    try:
                        
                        listing.click()
                        page.wait_for_timeout(5000)
                        
                        # Get HTML content after clicking
                        html_content = page.content()  # This retrieves the entire HTML of the current page
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        name = soup.select_one('.lfPIob')
                        address = soup.select_one('[data-item-id="address"] .fontBodyMedium')
                        website = soup.select_one('[data-item-id="authority"] .fontBodyMedium')
                        phone_number = soup.select_one('button[data-item-id*="phone:tel:"] div.fontBodyMedium')
                        review_count = soup.select_one('[jsaction="pane.reviewChart.moreReviews"] span')
                        reviews_average = soup.select_one('[jsaction="pane.reviewChart.moreReviews"] [role="img"]')
                        
                        business = Business()

                        business.name = name.get_text() if name else ""
                        business.address = address.get_text() if address else ""
                        business.website = website.get_text() if website else ""
                        business.phone_number = phone_number.get_text() if phone_number else ""
                        if review_count:
                            review_text = review_count.get_text()
                            business.reviews_count = int(review_text.split()[0].replace(',', '')) or 0
                        else:
                            business.reviews_count = 0
                            
                        if reviews_average:
                            business.reviews_average = float(reviews_average['aria-label'].split()[0].replace(',', '.')) or 0.0
                        else:
                            business.reviews_average = 0.0
                            
                        business.latitude, business.longitude = extract_coordinates_from_url(page.url)

                        business_list.business_list.append(business)
                    except Exception as e:
                        print(f'Error occurred: {e}')

                #########
                # Output
                #########
                business_list.save_to_excel(f"google_maps_data_{search_for.replace(' ', '_')}_{region}")
                business_list.save_to_csv(f"google_maps_data_{search_for.replace(' ', '_')}_{region}")

        browser.close()

if __name__ == "__main__":
    main()
