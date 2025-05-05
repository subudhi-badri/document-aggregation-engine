from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

from LinkedIn.commander import LINKEDIN_ACCEESS_TOKEN, LINKEDIN_ACCEESS_TOKEN_EXP, HEADLESS

# Setting up the options
options = Options()
if not HEADLESS=="False":
    options.add_argument("--headless=new")
options.add_argument('--ignore-ssl-errors=yes')
options.add_argument("--log-level=3")
options.add_argument('--ignore-certificate-errors=yes')

# Setting up service
service = Service(ChromeDriverManager().install(), log_output='nul')


def add_session_cookie(driver):
    """Load cookies from variables and add them to the driver."""
    cookie = {
        "domain": ".www.linkedin.com",
        "name": "li_at",
        "value": LINKEDIN_ACCEESS_TOKEN,  
        "path": "/",
        "secure": True,
        "httpOnly": True,
        "expirationDate": LINKEDIN_ACCEESS_TOKEN_EXP,
    }
    # Add cookies to the driver
    try:
        driver.get("https://www.linkedin.com")
        driver.add_cookie(cookie)
    except Exception as e:
        print(f"Error adding cookies to driver: {e}")