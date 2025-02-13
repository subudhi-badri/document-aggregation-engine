from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random  # Import random for adding delays


def search_with_name(name, school_or_company):
    print(f"Executing search with name: {name} and school/company: {school_or_company}")

    """Search for a LinkedIn profile by name and school/company."""
    # Construct the search query
    query = f"{name} {school_or_company} linkedin"
    
    # Setup Selenium WebDriver
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Run in headless mode
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Perform Google search
        print(f"Performing Google search with query: {query}")
        driver.get(f"https://www.google.com/search?q={query}")
        
        # Check for CAPTCHA by looking for specific elements
        time.sleep(2)  # Wait for the page to load
        if "captcha" in driver.page_source.lower():
            print("CAPTCHA detected. Please solve it manually.")
            input("Press Enter after solving the CAPTCHA...")


        time.sleep(random.uniform(2, 5))  # Wait for the page to load with a random delay


        # Find the first LinkedIn link
        linkedin_link = driver.find_element(By.XPATH, "//a[contains(@href, 'linkedin.com')]").get_attribute("href")
        print(linkedin_link)
        # Extract the LinkedIn ID from the URL
        linkedin_id = linkedin_link.split('/')[4]  # Assuming the URL is in the format: https://www.linkedin.com/in/linkedin_id/
        
        if linkedin_id:
            print(f"LinkedIn ID extracted: {linkedin_id}")
        else:
            print("No LinkedIn ID found in the search results.")
        return linkedin_id  # Return the extracted LinkedIn ID

    except Exception as e:
        print(f"Error during search: {e}")
        return None
    finally:
        driver.quit()
