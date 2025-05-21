from selenium import webdriver
from time import sleep
from LinkedIn.services.scraping_utils import options, service, add_session_cookie
from LinkedIn.services.api import json_generator

def scroll_to_bottom(driver):
    """Helper function to scroll to the bottom of a page"""
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        print("Finished scrolling to bottom")
    except Exception as e:
        print(f"Error during scrolling: {e}")

def scrape_page(driver, url):
    """Helper function to scrape a single page"""
    try:
        driver.get(url)
        sleep(2)
        scroll_to_bottom(driver)
        return driver.find_element("xpath", "/html").get_attribute("outerHTML")
    except Exception as e:
        print(f"Error scraping page {url}: {e}")
        return None

def scrape_full_profile(linkedin_id):
    """Scraping full LinkedIn profile page with all detail pages"""
    driver = None
    try:
        # Setup Selenium WebDriver
        driver = webdriver.Chrome(service=service, options=options)    
        add_session_cookie(driver)
        print(f'Scraping data for id: {linkedin_id}')

        # Base profile URL and detail pages
        base_url = f"https://www.linkedin.com/in/{linkedin_id}/"
        detail_pages = [
            "details/experience/",
            "details/projects/",
            "details/volunteering-experiences/"
        ]

        # Dictionary to store all HTML content
        all_content = {}
        # for i in range(50):
            # sleep(1)  # Wait for the page to load
            # print(i, "sleeping")
        # First scrape main profile
        main_page_html = scrape_page(driver, base_url)
        if main_page_html is None:
            raise Exception("Failed to scrape main profile page")
        
        if "/404" in driver.current_url or "Page not found" in main_page_html:
            driver.quit()
            print(f"Profile for {linkedin_id} not found (404)")
            return {"error": f"Profile for {linkedin_id} not found."}

        all_content["main_profile"] = main_page_html

        # Scrape each detail page
        for detail_page in detail_pages:
            detail_url = base_url + detail_page
            detail_html = scrape_page(driver, detail_url)
            if detail_html:
                all_content[detail_page.rstrip('/')] = detail_html

        # Save combined content to file
        filename = fr"C:\prit\coding\projects\MiniProject\forgery_detection\LinkedIn\services\outputs\linkedin_profiles\{linkedin_id}_profile.html"
        try:
            # Ensure the directory exists
            import os
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            with open(filename, "w", encoding='utf-8') as file:
                print(f"Attempting to write to {filename}...")
                # Write main profile first
                file.write("<!-- MAIN PROFILE -->\n")
                file.write(all_content["main_profile"])
                file.write("\n")
                
                # Write detail pages
                for page_type, content in all_content.items():
                    if page_type != "main_profile":
                        file.write(f"\n<!-- {page_type.upper()} -->\n")
                        file.write(content)
                        file.write("\n")
            print(f"Successfully saved combined HTML to {filename}")
        except Exception as e:
            print(f"Error writing to file {filename}: {e}")
        print(f"correct till not checkpoint 1 {filename}")
        # Generate JSON from combined content
        json_generator(linkedin_id, all_content["main_profile"])  # You might want to modify this to handle all content

        if driver:
            driver.quit()

        return {
            "success": True,
            "file_saved": filename
        }
    
    except Exception as e:
        print(f"Error fetching profile for {linkedin_id}: {e}")
        if driver:
            driver.quit()
        return {"error": f"Error fetching profile for {linkedin_id}"}