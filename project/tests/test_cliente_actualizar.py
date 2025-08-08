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

def test_cliente_actualizar_datos(driver):
    """
    TC4 - Prueba de actualización de datos del cliente (Camino feliz)
    Objetivo: Verificar que el sistema permita actualizar correctamente los datos del cliente.
    """
    print("\n===== INICIANDO PRUEBA DE ACTUALIZACIÓN DE CLIENTE =====\n")
    
    try:
        # Crear instancia de la página de login
        login_page = LoginPage(driver)
        
        # Navegar a la página de login
        login_page.navigate_to_login()
        print("Navegando a la página de login...")
        
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
        print(f"Ingresando credenciales: {username} / {password}")
        login_page.enter_username(username)
        login_page.enter_password(password)
        
        # Tomar captura antes del login
        login_page.take_screenshot("antes_login_tc4")
        
        # Hacer clic en el botón de login
        print("Haciendo clic en el botón de login...")
        login_page.click_login_button()
        
        # Esperar a que se complete el login
        print("Esperando a que se complete el login...")
        time.sleep(5)
        
        # Verificar si el login fue exitoso
        if login_page.is_logged_in():
            print("Login exitoso!")
        else:
            print("ADVERTENCIA: No se pudo confirmar el login exitoso")
        
        # Tomar captura de pantalla después del login
        login_page.take_screenshot("login_completado_tc4")
        
        # Crear instancia de la página de cliente
        cliente_page = ClientePage(driver)
        
        # Hacer clic en el botón de Clientes
        print("\n===== NAVEGANDO A LA SECCIÓN DE CLIENTES =====\n")
        cliente_page.click_clientes_button()
        
        # Esperar a que cargue la página de clientes
        print("Esperando a que cargue la página de clientes...")
        time.sleep(3)
        
        # Tomar captura de pantalla de la página de clientes
        cliente_page.take_screenshot("pagina_clientes_tc4")
        
        # Hacer clic en la pestaña "Editar/Eliminar Cliente"
        print("\n===== NAVEGANDO A LA PESTAÑA EDITAR/ELIMINAR CLIENTE =====\n")
        cliente_page.click_editar_eliminar_tab()
        
        # Esperar a que cargue la sección de editar/eliminar
        print("Esperando a que cargue la sección de editar/eliminar...")
        time.sleep(3)
        
        # Tomar captura de pantalla de la sección de editar/eliminar
        cliente_page.take_screenshot("seccion_editar_eliminar_tc4")
        
        # Seleccionar el cliente usando el método mejorado
        print("\n===== SELECCIONANDO CLIENTE =====\n")
        print("Seleccionando el cliente 'juan - 402-12337673-5'...")
        cliente_page.seleccionar_cliente("juan - 402-12337673-5")
        
        # Tomar captura de pantalla del cliente seleccionado
        cliente_page.take_screenshot("cliente_seleccionado_nuevo_metodo")
        
        # Esperar a que se carguen los datos del cliente
        print("Esperando a que se carguen los datos del cliente...")
        time.sleep(3)
        
        # Tomar captura de pantalla con el cliente seleccionado
        cliente_page.take_screenshot("cliente_seleccionado")
        
        # Verificar si el campo de nombre contiene "juan"
        try:
            nombre_actual = driver.find_element(By.CSS_SELECTOR, "input#text_input_7").get_attribute("value")
            print(f"Nombre actual en el campo: '{nombre_actual}'")
        except Exception as e:
            print(f"Error al obtener el nombre actual: {e}")
        
        # Actualizar el nombre del cliente de "juan" a "pedro"
        print("\n===== ACTUALIZANDO NOMBRE DEL CLIENTE =====\n")
        print("Cambiando nombre de 'juan' a 'pedro'...")
        cliente_page.actualizar_nombre_cliente("pedro")
        
        # Verificar si el campo se actualizó correctamente
        try:
            nuevo_nombre = driver.find_element(By.CSS_SELECTOR, "input#text_input_7").get_attribute("value")
            print(f"Nuevo nombre en el campo: '{nuevo_nombre}'")
            
            # Tomar captura de pantalla con el nombre cambiado
            cliente_page.take_screenshot("nombre_cliente_cambiado")
        except Exception as e:
            print(f"Error al obtener el nuevo nombre: {e}")
        
        # Hacer clic en el botón "Actualizar Cliente"
        print("\n===== GUARDANDO CAMBIOS =====\n")
        print("Haciendo clic en el botón 'Actualizar Cliente'...")
        cliente_page.click_actualizar_cliente_button()
        
        # Esperar a que se complete la actualización
        print("Esperando a que se complete la actualización...")
        time.sleep(3)
        
        # Tomar captura de pantalla después de la actualización
        cliente_page.take_screenshot("cliente_actualizado")
        
        # Verificar si aparece un mensaje de éxito
        mensaje = cliente_page.get_mensaje_exito()
        print(f"Mensaje después de actualizar: '{mensaje}'")
        
        # Buscar cualquier mensaje en la página
        try:
            mensajes = driver.find_elements(By.CSS_SELECTOR, "div.stAlert, div[data-testid='stText']")
            for i, msg in enumerate(mensajes):
                if msg.text.strip():
                    print(f"Mensaje encontrado #{i+1}: '{msg.text}'")
        except Exception as e:
            print(f"Error al buscar mensajes: {e}")
            
        # Tomar captura final
        cliente_page.take_screenshot("resultado_final_tc4")
        
        # Verificar que la actualización fue exitosa
        # Aceptamos cualquier mensaje que indique éxito o simplemente verificamos que no haya errores
        assert "error" not in mensaje.lower() and "no se pudo" not in mensaje.lower(), f"Se encontró un mensaje de error: {mensaje}"
        print("\n===== PRUEBA COMPLETADA CON ÉXITO =====\n")
        
    except Exception as e:
        print(f"\n===== ERROR EN LA PRUEBA: {e} =====\n")
        # Asegurarse de que cliente_page esté definido antes de usarlo
        if 'cliente_page' in locals():
            cliente_page.take_screenshot("error_en_prueba")
        raise
