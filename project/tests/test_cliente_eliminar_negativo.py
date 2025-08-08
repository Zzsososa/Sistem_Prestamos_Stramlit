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

def test_cliente_eliminar_sin_seleccion(driver):
    """
    TC3 - Prueba negativa de eliminación de cliente
    Objetivo: Verificar que el sistema no permita eliminar si no hay cliente seleccionado.
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
    login_page.take_screenshot("login_completado_tc3")
    
    # Crear instancia de la página de cliente
    cliente_page = ClientePage(driver)
    
    # Hacer clic en el botón de Clientes
    cliente_page.click_clientes_button()
    
    # Esperar a que cargue la página de clientes
    time.sleep(3)
    
    # Tomar captura de pantalla de la página de clientes
    cliente_page.take_screenshot("pagina_clientes_tc3")
    
    # Hacer clic en la opción "Editar/Eliminar Cliente"
    cliente_page.click_editar_eliminar_tab()
    
    # Esperar a que cargue la sección de editar/eliminar
    time.sleep(3)
    
    # Tomar captura de pantalla de la sección de editar/eliminar
    cliente_page.take_screenshot("seccion_editar_eliminar")
    
    # Intentar hacer clic en el botón de eliminar sin seleccionar un cliente
    cliente_page.click_eliminar_cliente_button()
    
    # Esperar un momento para que aparezca el mensaje de error (si lo hay)
    time.sleep(2)
    
    # Tomar captura de pantalla después de intentar eliminar
    cliente_page.take_screenshot("intento_eliminar_sin_seleccion")
    
    # Verificar si aparece un mensaje de error o advertencia
    mensaje_error = cliente_page.get_mensaje_error()
    
    # Verificar que exista un mensaje de error o que no se haya realizado la acción
    assert mensaje_error != "", "No se mostró mensaje de error al intentar eliminar sin seleccionar cliente"
    
    # Tomar captura final
    cliente_page.take_screenshot("resultado_final_tc3")
