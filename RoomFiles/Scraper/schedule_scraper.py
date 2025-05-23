"""
Description:
- This script scrapes class schedule data from the Sacramento State University class schedule website.
- The script uses Selenium to automate the browser and scrape data.
- It collects information about classes, including building, room, days, start time, and end time.
- The data is saved in a JSON file for further processing or analysis.

How to Run:
- Make sure you have Python and Firefox installed on your system.
- Install the required dependencies, including Selenium:
   pip install selenium
- Update the `gecko_path` variable to point to your `geckodriver` executable.
    - You can download `geckodriver` from: https://github.com/mozilla/geckodriver/releases.
- Run the script:
   python schedule_scraper.py
- The scraped data will be saved in the `ScrapedSchedules` folder as a JSON file.
"""
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from collections import defaultdict
import json
import time
import os

# Path to geckodriver
gecko_path = r"C:\Users\nmira\Documents\College\drivers\geckodriver.exe"

# Define the semester and year as a single variable
semester_year = "summer-2025"  # Change this value for each new semester

# Construct the directory URL dynamically using the semester and year
directory_url = f"https://www.csus.edu/class-schedule/{semester_year}/"

# Ensure the output folder exists
output_folder = 'ScrapedSchedules'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)  # Create the folder if it doesn't exist

# Set the output file name dynamically based on the semester and year
output_file_name = f"{semester_year}_schedule.json"
output_path = os.path.join(output_folder, output_file_name)

print(f"📂 Output file will be saved as: {output_path}")

# Set up Firefox driver
service = Service(executable_path=gecko_path)
driver = webdriver.Firefox(service=service)

# Step 1: Get all major links
# Navigate to the directory URL containing links to all majors
driver.get(directory_url)

# Wait until at least one link to a major page is present on the page
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.XPATH, f'//a[contains(@href, "/class-schedule/{semester_year}/")]'))
)

# Extract all links to major pages
link_elements = driver.find_elements(By.XPATH, f'//a[contains(@href, "/class-schedule/{semester_year}/")]')
major_links = []
for elem in link_elements:
    href = elem.get_attribute("href")
    if href and href not in major_links:
        major_links.append(href)

# Print the list of major links found
print("✅ Found major links:")
for link in major_links:
    print(link)

# Step 2: Visit each major page and scrape class data
# Initialize an empty list to store class information
class_list = []
class_id = 1  # Unique ID for each class

# Loop through each major page URL
for url in major_links:
    print(f"\n🔍 Scraping: {url}")
    driver.get(url)

    try:
        # Wait for expandable rows (class rows) to load on the page
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, '//button[@aria-label="Expand Row"]'))
        )
        time.sleep(1)

        # Find all "Expand Row" buttons and click them to reveal class details
        expand_buttons = driver.find_elements(By.XPATH, '//button[@aria-label="Expand Row"]')
        print(f"🟢 Found {len(expand_buttons)} rows to expand")

        for btn in expand_buttons:
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.3)  # Small delay to ensure the row expands
            except Exception as e:
                print(f"⚠️ Couldn't click expand row: {e}")
                continue

        # Wait for class information blocks to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'class-info-main'))
        )
        time.sleep(1)
    except Exception as e:
        print(f"⚠️ No class-info-main blocks found or expandable rows failed: {e}")
        continue

    # Extract all class information blocks
    class_blocks = driver.find_elements(By.CLASS_NAME, 'class-info-main')
    print(f"  → Found {len(class_blocks)} class blocks")

    # Process each class block to extract relevant details
    for block in class_blocks:
        try:
            # Helper function to safely extract text from elements
            def safe_get(classname):
                elems = block.find_elements(By.CLASS_NAME, classname)
                return elems[0].text.split(':')[-1].strip() if elems else "N/A"

            # Extract class details
            building = safe_get('class_building')
            room = safe_get('class_room')
            days = safe_get('class_days')
            start = safe_get('class_start_time')
            end = safe_get('class_end_time')

            # Skip incomplete class information
            if "N/A" in (building, room, days, start, end):
                print("⚠️ Incomplete class info, skipping.")
                continue

            # Create a dictionary for the class and add it to the list
            class_obj = {
                "id": class_id,
                "building": building,
                "room": room,
                "days": days,
                "start_time": start,
                "end_time": end,
                "time_range": f"{start} - {end}"
            }

            class_list.append(class_obj)
            class_id += 1

        except Exception as e:
            print(f"⚠️ Unexpected error on one block: {e}")
            continue

    # Save the updated list to JSON file after each major page
    with open(output_path, 'w') as f:
        json.dump(class_list, f, indent=2)
    print(f"💾 Partial save complete to {output_path}.")

# Done
# Close the browser and print a success message
driver.quit()
print(f"\n✅ Room schedule saved to {output_path}")