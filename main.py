from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import os
import sys
import re

@dataclass
class Business:
    """holds business data"""

    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    reviews_count: int = None
    reviews_average: float = None
    latitude: float = None
    longitude: float = None
    one_star_reviews: int = None

@dataclass
class BusinessList:
    """holds list of Business objects, and saves to both Excel and CSV"""

    business_list: list[Business] = field(default_factory=list)
    save_at = 'output'

    def dataframe(self):
        """Transform business_list to pandas dataframe"""
        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )

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

def extract_coordinates_from_url(url: str) -> tuple[float, float]:
    """Helper function to extract coordinates from URL"""
    coordinates = url.split('/@')[-1].split('/')[0]
    return float(coordinates.split(',')[0]), float(coordinates.split(',')[1])

def parse_review_text(review_text: str) -> int:
    """Extract the number of 1-star reviews from review text"""
    match = re.search(r'(\d+)\s*1-star', review_text, re.IGNORECASE)
    return int(match.group(1)) if match else 0

def main():
    ########
    # input 
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
                search_list = file.readlines()

    if not search_list:
        print('Error: You must either pass the -s search argument or add searches to input.txt')
        sys.exit()

    if args.total:
        total = args.total
    else:
        total = 1_000

    if args.regions:
        regions = args.regions
    else:
        regions = ['USA', 'Australia', 'UK', 'New Zealand']

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

                        name_attibute = 'aria-label'
                        address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
                        website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
                        phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
                        review_count_xpath = '//button[@jsaction="pane.reviewChart.moreReviews"]//span'
                        reviews_average_xpath = '//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]'

                        business = Business()

                        if len(listing.get_attribute(name_attibute)) >= 1:
                            business.name = listing.get_attribute(name_attibute)
                        else:
                            business.name = ""
                        if page.locator(address_xpath).count() > 0:
                            business.address = page.locator(address_xpath).all()[0].inner_text()
                        else:
                            business.address = ""
                        if page.locator(website_xpath).count() > 0:
                            business.website = page.locator(website_xpath).all()[0].inner_text()
                        else:
                            business.website = ""
                        if page.locator(phone_number_xpath).count() > 0:
                            business.phone_number = page.locator(phone_number_xpath).all()[0].inner_text()
                        else:
                            business.phone_number = ""
                        if page.locator(review_count_xpath).count() > 0:
                            review_text = page.locator(review_count_xpath).inner_text()
                            business.reviews_count = int(review_text.split()[0].replace(',', '')) or 0
                            business.one_star_reviews = parse_review_text(review_text)
                        else:
                            business.reviews_count = 0
                            business.one_star_reviews = 0
                            
                        if page.locator(reviews_average_xpath).count() > 0:
                            business.reviews_average = float(page.locator(reviews_average_xpath).get_attribute(name_attibute).split()[0].replace(',', '.')) or 0.0
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
