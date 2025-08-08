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

def test_buscar_cliente_existente(driver):
    """
    TC5 - Prueba de búsqueda de cliente existente (Camino feliz)
    Objetivo: Verificar que el sistema devuelva resultados correctos al buscar un cliente existente.
    """
    print("\n===== INICIANDO PRUEBA DE BÚSQUEDA DE CLIENTE =====\n")
    
    try:
        # Cargar configuración
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'config.yaml')
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

        # Crear instancia de la página de login
        login_page = LoginPage(driver)
        
        # Navegar a la página de login
        login_page.navigate_to_login()
        print("Navegando a la página de login...")
        time.sleep(2)
        
        # Obtener credenciales de administrador
        username = config['credentials']['admin']['username']
        password = config['credentials']['admin']['password']
        
        # Realizar login
        print(f"Ingresando credenciales: {username} / {password}")
        login_page.enter_username(username)
        login_page.enter_password(password)
        login_page.click_login_button()
        time.sleep(5) # Esperar a que se complete el login
        print("Login exitoso!")
        
        # Crear instancia de la página de cliente
        cliente_page = ClientePage(driver)
        
        # Hacer clic en el botón de Clientes
        print("\n===== NAVEGANDO A LA SECCIÓN DE CLIENTES =====\n")
        cliente_page.click_clientes_button()
        time.sleep(3)
        
        # Hacer clic en la pestaña "Lista de Clientes"
        print("\n===== NAVEGANDO A LA PESTAÑA LISTA DE CLIENTES =====\n")
        cliente_page.click_lista_clientes_tab()
        time.sleep(2)
        
        # Buscar el cliente
        nombre_a_buscar = "Lorenzo alberto"
        print(f"\n===== BUSCANDO CLIENTE: '{nombre_a_buscar}' =====\n")
        cliente_page.buscar_cliente(nombre_a_buscar)
        time.sleep(3) # Esperar a que la tabla se filtre
        
        # Verificar que el cliente aparece en la lista
        print("\n===== VERIFICANDO RESULTADOS DE BÚSQUEDA =====\n")
        assert cliente_page.verificar_cliente_en_lista(nombre_a_buscar), f"El cliente '{nombre_a_buscar}' no fue encontrado en los resultados."
        print(f"Cliente '{nombre_a_buscar}' encontrado exitosamente.")
        
        cliente_page.take_screenshot("busqueda_cliente_exitosa")
        print("\n===== PRUEBA COMPLETADA CON ÉXITO =====\n")
        
    except Exception as e:
        print(f"\n===== ERROR EN LA PRUEBA: {e} =====\n")
        if 'cliente_page' in locals():
            cliente_page.take_screenshot("error_en_prueba_busqueda")
        raise
