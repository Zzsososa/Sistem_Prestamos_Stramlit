import os
import sys
import time
import pytest
import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

# Agregar el directorio del proyecto al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pages.login_page import LoginPage
from pages.cliente_page import ClientePage

@pytest.fixture(scope="function")
def driver():
    """
    Fixture para inicializar el driver de Selenium antes de cada prueba
    y cerrarlo después de que se complete.
    """
    # Cargar configuración
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'config.yaml')
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    # Configurar el driver según el navegador especificado en la configuración
    browser = config['browser']['name'].lower()
    
    if browser == 'firefox':
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service)
    else:
        # Por defecto usar Firefox si no se especifica o no se reconoce
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service)
    
    # Configurar el tamaño de la ventana
    driver.set_window_size(1366, 768)
    
    # Devolver el driver inicializado
    yield driver
    
    # Cerrar el driver después de la prueba
    driver.quit()

def test_cliente_limite_caracteres(driver):
    """
    TC2 - Prueba de límite de caracteres en el nombre del cliente
    Objetivo: Verificar que el sistema valide el límite de caracteres en el nombre del cliente.
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
    
    # Realizar login
    login_page.enter_username(username)
    login_page.enter_password(password)
    login_page.click_login_button()
    
    # Esperar a que se complete el login
    time.sleep(5)
    
    # Tomar captura de pantalla después del login
    login_page.take_screenshot("login_completado_tc2")
    
    # Crear instancia de la página de cliente
    cliente_page = ClientePage(driver)
    
    # Hacer clic en el botón de Clientes
    cliente_page.click_clientes_button()
    
    # Esperar a que cargue la página de clientes
    time.sleep(3)
    
    # Tomar captura de pantalla de la página de clientes
    cliente_page.take_screenshot("pagina_clientes")
    
    # Generar un string de 51 caracteres (excediendo el límite de 50)
    nombre_largo = "A" * 51
    
    # Intentar ingresar el nombre largo en el campo de nombre
    cliente_page.enter_nombre_cliente(nombre_largo)
    
    # Tomar captura de pantalla después de intentar ingresar el nombre largo
    cliente_page.take_screenshot("nombre_cliente_largo")
    
    # Obtener el valor actual del campo (debería estar truncado a 50 caracteres)
    valor_actual = cliente_page.get_nombre_cliente_value()
    
    # Verificar que el valor se haya truncado a 50 caracteres
    assert len(valor_actual) <= 50, f"El campo permite más de 50 caracteres. Longitud actual: {len(valor_actual)}"
    
    # Verificar el valor exacto
    assert len(valor_actual) == 50, f"El campo debería contener exactamente 50 caracteres, pero contiene {len(valor_actual)}"
    assert valor_actual == "A" * 50, "El valor del campo no coincide con el esperado"
