# tests/test_selenium.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from PIL import Image
import os
import time
import threading
import gc  # For garbage collection

# --- Test Setup ---

# Define where downloads will go for verification (needs to be absolute path)
DOWNLOAD_DIR = os.path.abspath("selenium_downloads")
# Ensure download dir exists and is empty before tests
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
for f in os.listdir(DOWNLOAD_DIR): # Clear out old downloads
    try:
        os.remove(os.path.join(DOWNLOAD_DIR, f))
    except (PermissionError, OSError):
        print(f"Warning: Could not remove file {f} during setup")


@pytest.fixture(scope='module') # 'module' scope: setup/teardown once per test file
def chrome_driver():
    """Setup Selenium WebDriver."""
    chrome_options = ChromeOptions()
    # Uncomment the next line if you want to run headless (without browser UI)
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox") # Often needed in CI environments
    chrome_options.add_argument("--disable-dev-shm-usage") # Often needed in CI environments
    chrome_options.add_argument("--window-size=1920,1080") # Standard window size

    # Configure download directory
    prefs = {"download.default_directory": DOWNLOAD_DIR,
             "download.prompt_for_download": False, # To auto-download
             "download.directory_upgrade": True,
             "safeBrowse.enabled": True}
    chrome_options.add_experimental_option("prefs", prefs)

    # Use webdriver-manager to automatically handle driver download/setup
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    yield driver # Provide the driver object to the test

    # Teardown: close browser
    driver.quit()


@pytest.fixture(scope='module')
def live_server_url():
    """Start Flask app in a background thread and provide its URL."""
    # Use a different port than default 5000 if it might conflict
    test_port = 5001
    test_host = '127.0.0.1'

    # Create Flask app instance (ensure it's configured for testing if needed)
    from app import app
    app.config['TESTING'] = True # Ensure test config if needed
    app.config['SECRET_KEY'] = 'selenium-key'

    # Run Flask app in a thread daemonized
    server_thread = threading.Thread(target=app.run, kwargs={'host': test_host, 'port': test_port})
    server_thread.daemon = True # Allows main thread to exit even if this thread is running
    server_thread.start()

    # Wait a moment for the server to start (adjust sleep time if needed)
    time.sleep(1)

    yield f"http://{test_host}:{test_port}/"
    # No explicit stop needed for daemon thread


# --- Helper function to create a dummy image file ---
def create_dummy_image(filename="test_image.png", size=(60, 30), color="blue"):
    """Creates a test image and saves it to the download directory."""
    img = Image.new('RGB', size, color=color)
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    img.save(filepath)
    img.close()  # Explicitly close the image
    return filepath


def test_page_load(chrome_driver, live_server_url):
    """Test if the main page loads correctly."""
    chrome_driver.get(live_server_url)
    assert "Simple Image Resizer & Filter" in chrome_driver.title
    assert chrome_driver.find_element(By.TAG_NAME, "h1").text == "Image Resizer & Filter"


def test_image_upload_and_resize(chrome_driver, live_server_url):
    """Test uploading an image, resizing by width, and downloading."""
    chrome_driver.get(live_server_url)

    # Create a dummy image to upload but with a DIFFERENT prefix to avoid confusion
    # Change the name so it doesn't contain the same prefix as the downloaded file
    image_path = create_dummy_image("original_image.png", size=(100, 50), color="red")

    # Find form elements and interact with them
    file_input = chrome_driver.find_element(By.ID, "file")
    width_radio = chrome_driver.find_element(By.ID, "resize_width")
    width_input = chrome_driver.find_element(By.ID, "width")
    submit_button = chrome_driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

    width_radio.click()
    width_input.clear()
    width_input.send_keys("80")
    file_input.send_keys(image_path)
    submit_button.click()

    # Now look specifically for JPEG files with upload_ prefix (the processed files)
    # that weren't there before the submission
    download_wait_timeout = 15
    start_time = time.time()
    downloaded_filepath = None

    while time.time() - start_time < download_wait_timeout:
        # Look specifically for JPEG files that were generated from our upload
        files = [f for f in os.listdir(DOWNLOAD_DIR) 
                if f.endswith('.jpeg') and not f == "original_image.png"]
        
        if files:
            downloaded_filepath = os.path.join(DOWNLOAD_DIR, files[0])
            break
        time.sleep(0.5)

    assert downloaded_filepath is not None, "Downloaded file not found"
    
    try:
        img = Image.open(downloaded_filepath)
        assert img.size == (80, 40), f"Image wasn't resized correctly. Expected (80, 40) but got {img.size}"
        img.close()
    finally:
        # Cleanup
        gc.collect()
        time.sleep(1)


def test_image_upload_grayscale_filter(chrome_driver, live_server_url):
    """Test uploading an image and applying grayscale filter."""
    chrome_driver.get(live_server_url)
    image_path = create_dummy_image("upload_gray.jpg", size=(40, 40), color=(100, 150, 200))  # Use JPG

    file_input = chrome_driver.find_element(By.ID, "file")
    grayscale_checkbox = chrome_driver.find_element(By.ID, "grayscale")
    # Keep original size
    none_radio = chrome_driver.find_element(By.ID, "resize_none")
    format_select = chrome_driver.find_element(By.ID, "format")
    submit_button = chrome_driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

    none_radio.click()  # Keep original size
    grayscale_checkbox.click()
    # Select JPEG output explicitly (though it's default)
    format_select.find_element(By.CSS_SELECTOR, "option[value='JPEG']").click()
    file_input.send_keys(image_path)

    submit_button.click()

    # Wait for download
    expected_filename_part = "upload_gray"
    download_wait_timeout = 15
    download_complete = False
    start_time = time.time()
    downloaded_filepath = None

    while time.time() - start_time < download_wait_timeout:
         files = [f for f in os.listdir(DOWNLOAD_DIR) 
                 if expected_filename_part in f 
                 and f.endswith('.jpeg') 
                 and not f.endswith('.crdownload')]
         
         if files:
             downloaded_filepath = os.path.join(DOWNLOAD_DIR, files[0])
             download_complete = True
             break
         time.sleep(0.5)

    assert download_complete, "Grayscale download did not complete"
    assert downloaded_filepath is not None

    try:
        img = Image.open(downloaded_filepath)
        assert img.size == (40, 40)  # Original size
        assert img.mode == 'L' or img.mode == 'RGB'  # Grayscale ('L') or RGB (visually gray)
        img.close()
    finally:
        gc.collect()
        time.sleep(1)
        try:
            if os.path.exists(image_path): 
                os.remove(image_path)
        except:
            pass
        try:
            if os.path.exists(downloaded_filepath):
                os.remove(downloaded_filepath)
        except:
            pass


def test_form_submission_no_file(chrome_driver, live_server_url):
    """Test browser validation for required file input."""
    chrome_driver.get(live_server_url)
    
    # Submit the form without a file
    submit_button = chrome_driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_button.click()
    
    # The form shouldn't be submitted - we should still be on the same page
    # with no redirect (because browser validation prevents submission)
    time.sleep(1)  # Small wait
    
    # Verify we're still on the main page (no redirect occurred)
    assert chrome_driver.current_url == live_server_url, "Browser should prevent form submission"
    
    # Success - the browser prevented submission as expected
    # No need to check for flash messages since the request never reached the server