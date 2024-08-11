# Scrape-businesses-in-a-region-on-google-maps-with-python


![](data_scraped_csv.png)
![](data_scraped.png)



Scrape businesses in a region on google maps with python

To run the provided script, follow these steps:

1. Set Up Your Environment
Ensure you have Python and the required libraries installed. You can use a virtual environment to manage dependencies.

Install Dependencies
Create and activate a virtual environment (optional but recommended):


python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install the necessary packages:


pip install playwright pandas
playwright install
This will install Playwright and its required browser binaries. If you encounter issues, you may need to follow Playwright's installation instructions for your specific environment.

2. Prepare Your Script
Save the Script:
Copy the provided script into a file, e.g., scrape_google_maps.py.

Ensure Input File (if needed):
If you are not using the -s argument to pass search terms directly, create an input.txt file in the same directory as your script with each search term on a new line.

3. Run the Script
Open a terminal or command prompt and navigate to the directory where your script is saved. Run the script with the desired arguments.

Basic Usage
For searching a term in default regions:


python scrape_google_maps.py -s "restaurant" -t 100
Specify Regions
To search in specific regions:


python scrape_google_maps.py -s "restaurant" -t 100 -r USA Australia UK New Zealand
Run with Input File
If you have multiple search terms in input.txt, simply run:


python scrape_google_maps.py -t 100
4. Review Output
The script will generate Excel and CSV files in the output directory with the data scraped. The filenames will be formatted as google_maps_data_<search_term>_<region>.xlsx and google_maps_data_<search_term>_<region>.csv.

Troubleshooting
Error Handling: Ensure that Playwright is correctly installed and the browser binaries are available. If you encounter issues, refer to Playwright's documentation for troubleshooting.
Network Issues: Check for network issues if the script is unable to access Google Maps or if there are issues with loading the page.
Adjust Timeouts: If the page takes longer to load, you might need to adjust page.wait_for_timeout() values.