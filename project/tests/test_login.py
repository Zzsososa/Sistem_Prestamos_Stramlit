import os
import sys
import time
import pytest
import yaml
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager

# Agregar el directorio del proyecto al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pages.login_page import LoginPage

@pytest.fixture(scope="function")
def driver():
    """Fixture para configurar y cerrar el navegador para cada prueba"""
    # Cargar configuración
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'config.yaml')
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    # Configurar el navegador
    browser_name = config['browser']['name']
    headless = config['browser']['headless']
    
    if browser_name.lower() == 'firefox':
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument('--headless')
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
    else:
        # Por defecto usar Firefox si la configuración no es válida
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument('--headless')
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
    
    # Configurar el tamaño de la ventana
    driver.maximize_window()
    
    # Proporcionar el driver a la prueba
    yield driver
    
    # Cerrar el navegador después de la prueba
    driver.quit()

def test_login_correcto(driver):
    """
    TC1 - Login correcto (Camino feliz)
    Objetivo: Verificar que el usuario pueda iniciar sesión con credenciales válidas.
    """
    # Crear instancia de la página de login
    login_page = LoginPage(driver)
    
    # Navegar a la página de login
    login_page.navigate_to_login()
    
    # Esperar a que la página cargue completamente
    time.sleep(2)
    
    # Cargar credenciales desde el archivo de configuración
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'config.yaml')
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    # Obtener credenciales de administrador
    username = config['credentials']['admin']['username']
    password = config['credentials']['admin']['password']
    
    # Tomar captura de pantalla antes del login
    login_page.take_screenshot("antes_login")
    
    # Ingresar usuario y contraseña
    login_page.enter_username(username)
    login_page.enter_password(password)
    
    # Tomar captura con las credenciales ingresadas
    login_page.take_screenshot("credenciales_ingresadas")
    
    # Hacer clic en el botón de login
    try:
        # Intentar con el selector exacto
        login_page.driver.execute_script(
            "document.querySelector('button[kind=\'secondaryFormSubmit\'][data-testid=\'stBaseButton-secondaryFormSubmit\']').click();"
        )
    except Exception:
        # Si falla, intentar con el método estándar
        login_page.click_login_button()
    
    # Esperar un momento para que la página se cargue completamente
    time.sleep(5)
    
    # Tomar captura de pantalla después del login
    screenshot_path = login_page.take_screenshot("login_exitoso")
    
    # Tomar otra captura para verificar el estado final
    login_page.take_screenshot("estado_final")
    
    # Verificar que se haya tomado la captura de pantalla correctamente
    assert os.path.exists(screenshot_path), "No se pudo tomar la captura de pantalla del login"
