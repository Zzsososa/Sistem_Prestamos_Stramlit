import os
import time
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import yaml

class BasePage:
    """Base class for all page objects"""
    
    def __init__(self, driver):
        self.driver = driver
        self._load_config()
        
    def _load_config(self):
        """Load configuration from YAML file"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'config.yaml')
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
    def open_url(self, url):
        """Open a specific URL"""
        self.driver.get(url)
        
    def get_base_url(self):
        """Get the base URL from config"""
        return self.config['application']['base_url']
        
    def find_element(self, by, value, timeout=None):
        """Find an element with wait"""
        if timeout is None:
            timeout = self.config['timeouts']['element_wait']
            
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            print(f"Element not found with {by}={value} after {timeout} seconds")
            return None
            
    def find_elements(self, by, value, timeout=None):
        """Find multiple elements with wait"""
        if timeout is None:
            timeout = self.config['timeouts']['element_wait']
            
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((by, value))
            )
            return elements
        except TimeoutException:
            print(f"Elements not found with {by}={value} after {timeout} seconds")
            return []
            
    def click_element(self, by, value, timeout=None):
        """Click on an element with multiple retry strategies"""
        if timeout is None:
            timeout = self.config['timeouts']['element_wait']
            
        print(f"Intentando hacer clic en elemento: {by}={value}")
        
        # Estrategia 1: Método estándar
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            print("Clic exitoso (estrategia 1)")
            return True
        except Exception as e:
            print(f"Estrategia 1 falló: {e}")
        
        # Estrategia 2: Buscar el elemento y usar JavaScript para hacer clic
        try:
            element = self.find_element(by, value)
            if element:
                self.driver.execute_script("arguments[0].click();", element)
                print("Clic exitoso usando JavaScript (estrategia 2)")
                return True
        except Exception as e:
            print(f"Estrategia 2 falló: {e}")
        
        # Estrategia 3: Intentar con Actions
        try:
            element = self.find_element(by, value)
            if element:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                actions.move_to_element(element).click().perform()
                print("Clic exitoso usando ActionChains (estrategia 3)")
                return True
        except Exception as e:
            print(f"Estrategia 3 falló: {e}")
        
        print(f"No se pudo hacer clic en el elemento: {by}={value}")
        return False
        
    def input_text(self, by, value, text, clear_first=True, timeout=None):
        """Input text into an element"""
        element = self.find_element(by, value, timeout)
        if element:
            try:
                if clear_first:
                    element.clear()
                element.send_keys(text)
                return True
            except Exception as e:
                print(f"Failed to input text: {e}")
                return False
        return False
        
    def get_text(self, by, value, timeout=None):
        """Get text from an element"""
        element = self.find_element(by, value, timeout)
        if element:
            return element.text
        return None
        
    def is_element_present(self, by, value, timeout=None):
        """Check if element is present"""
        element = self.find_element(by, value, timeout)
        return element is not None
        
    def wait_for_element(self, by, value, timeout=None, condition=EC.visibility_of_element_located):
        """Wait for an element with a specific condition"""
        if timeout is None:
            timeout = self.config['timeouts']['element_wait']
            
        try:
            element = WebDriverWait(self.driver, timeout).until(
                condition((by, value))
            )
            return element
        except TimeoutException:
            print(f"Timeout waiting for element with {by}={value} after {timeout} seconds")
            return None
            
    def wait_for_url_contains(self, text, timeout=None):
        """Wait for URL to contain specific text"""
        if timeout is None:
            timeout = self.config['timeouts']['page_load']
            
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.url_contains(text)
            )
            return True
        except TimeoutException:
            print(f"Timeout waiting for URL to contain '{text}' after {timeout} seconds")
            return False
            
    def take_screenshot(self, name=None):
        """Take a screenshot and save it to the assets folder"""
        if name is None:
            name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        # Ensure the filename has .png extension
        if not name.endswith('.png'):
            name = f"{name}.png"
            
        # Create the assets directory if it doesn't exist
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'result', 'assets')
        os.makedirs(assets_dir, exist_ok=True)
        
        # Save the screenshot
        screenshot_path = os.path.join(assets_dir, name)
        try:
            self.driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            return screenshot_path
        except Exception as e:
            print(f"Failed to take screenshot: {e}")
            return None
            
    def scroll_to_element(self, element):
        """Scroll to an element"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            # Add a small delay to allow the page to settle after scrolling
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"Failed to scroll to element: {e}")
            return False
            
    def select_option_by_text(self, by, value, option_text, timeout=None):
        """Select an option from a dropdown by visible text"""
        from selenium.webdriver.support.ui import Select
        
        element = self.find_element(by, value, timeout)
        if element:
            try:
                select = Select(element)
                select.select_by_visible_text(option_text)
                return True
            except Exception as e:
                print(f"Failed to select option: {e}")
                return False
        return False
        
    def get_page_title(self):
        """Get the page title"""
        return self.driver.title
        
    def refresh_page(self):
        """Refresh the current page"""
        self.driver.refresh()
        
    def go_back(self):
        """Navigate back in browser history"""
        self.driver.back()
        
    def execute_script(self, script, *args):
        """Execute JavaScript in the browser"""
        return self.driver.execute_script(script, *args)
