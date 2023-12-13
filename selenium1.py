from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By


# Setting up ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Navigate to the page
url = "https://careers.varonis.com/careers?p=job%2FoBSujfw0%2Fapply%3Fnl%3D1&jvk=Job&jvi=oBSujfw0,Job&j=oBSujfw0&__jvst=Career%20Site&nl=1"  # Replace with your target URL
driver.get(url)

# Wait for the dynamic content to load
time.sleep(5)  # Adjust the sleep time as necessary

# Find all input, textarea, and select elements
input_elements = driver.find_elements(By.TAG_NAME, 'input')
textarea_elements = driver.find_elements(By.TAG_NAME, 'textarea')
select_elements = driver.find_elements(By.TAG_NAME, 'select')



# Extracting information from the elements
for element in input_elements + textarea_elements + select_elements:
    element_type = element.get_attribute('type')
    element_name = element.get_attribute('name')
    element_id = element.get_attribute('id')
    element_placeholder = element.get_attribute('placeholder')

    print(f"Type: {element_type}, Name: {element_name}, ID: {element_id}, Placeholder: {element_placeholder}")

    print(f"Number of input elements found: {len(input_elements)}")
    print(f"Number of textarea elements found: {len(textarea_elements)}")
    print(f"Number of select elements found: {len(select_elements)}")


# Close the driver
driver.quit()
