import os
import sys
import traceback

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Intentar importar los módulos necesarios
    from selenium import webdriver
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from webdriver_manager.firefox import GeckoDriverManager
    from pages.login_page import LoginPage
    import yaml
    
    print("Importaciones exitosas")
    
    # Cargar configuración
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'config.yaml')
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    print("Configuración cargada correctamente")
    
    # Configurar el navegador
    browser_name = config['browser']['name']
    headless = config['browser']['headless']
    
    print(f"Configurando navegador: {browser_name}, headless: {headless}")
    
    # Inicializar el driver
    options = webdriver.FirefoxOptions()
    if headless:
        options.add_argument('--headless')
    
    driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
    
    print("Driver inicializado correctamente")
    
    # Configurar el tamaño de la ventana
    driver.maximize_window()
    
    # Crear instancia de la página de login
    login_page = LoginPage(driver)
    
    print("Página de login creada correctamente")
    
    # Navegar a la página de login
    login_page.navigate_to_login()
    
    print("Navegación a la página de login exitosa")
    
    # Obtener credenciales
    username = config['credentials']['admin']['username']
    password = config['credentials']['admin']['password']
    
    # Realizar login
    login_page.login(username, password)
    
    print("Login realizado correctamente")
    
    # Verificar si el login fue exitoso
    if login_page.is_logged_in():
        print("Login exitoso")
    else:
        print("Login fallido")
    
    # Tomar captura de pantalla
    screenshot_path = login_page.take_screenshot("login_exitoso")
    print(f"Captura de pantalla guardada en: {screenshot_path}")
    
    # Cerrar el navegador
    driver.quit()
    
except Exception as e:
    print(f"Error: {e}")
    print("Traceback:")
    traceback.print_exc()
