import os
import time
import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

def main():
    print("Iniciando diagnóstico del botón de inicio de sesión...")
    
    # Cargar configuración
    with open(os.path.join('data', 'config.yaml'), 'r') as file:
        config = yaml.safe_load(file)
    
    # Configurar el driver
    print("Configurando el driver de Firefox...")
    driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
    driver.maximize_window()
    
    try:
        # Navegar a la página
        print(f"Navegando a {config['url']}...")
        driver.get(config['url'])
        time.sleep(3)
        
        # Tomar captura de pantalla inicial
        print("Tomando captura de pantalla inicial...")
        driver.save_screenshot("result/assets/diagnostico_inicial.png")
        
        # Buscar campos de entrada
        print("Buscando campos de entrada...")
        username_input = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        
        # Ingresar credenciales
        print("Ingresando credenciales...")
        username = config['credentials']['admin']['username']
        password = config['credentials']['admin']['password']
        username_input.send_keys(username)
        password_input.send_keys(password)
        
        # Tomar captura después de ingresar credenciales
        print("Tomando captura después de ingresar credenciales...")
        driver.save_screenshot("result/assets/diagnostico_credenciales.png")
        
        # Buscar y analizar todos los botones en la página
        print("\nAnalizando todos los botones en la página:")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"Se encontraron {len(buttons)} botones.")
        
        for i, button in enumerate(buttons):
            try:
                is_displayed = button.is_displayed()
                button_text = button.text if button.text else "Sin texto"
                button_class = button.get_attribute("class")
                button_id = button.get_attribute("id") or "Sin ID"
                button_type = button.get_attribute("type") or "Sin tipo"
                button_testid = button.get_attribute("data-testid") or "Sin data-testid"
                button_kind = button.get_attribute("kind") or "Sin kind"
                
                print(f"\nBotón #{i+1}:")
                print(f"  - Visible: {is_displayed}")
                print(f"  - Texto: '{button_text}'")
                print(f"  - Clase: {button_class}")
                print(f"  - ID: {button_id}")
                print(f"  - Tipo: {button_type}")
                print(f"  - TestID: {button_testid}")
                print(f"  - Kind: {button_kind}")
                
                # Verificar si parece ser el botón de login
                if any(word in button_text.lower() for word in ['iniciar', 'sesión', 'login', 'ingresar']):
                    print("  ¡ESTE PARECE SER EL BOTÓN DE LOGIN!")
                    
                    # Intentar hacer clic en el botón
                    if is_displayed:
                        print("  Intentando hacer clic en este botón...")
                        driver.save_screenshot(f"result/assets/diagnostico_antes_clic_{i+1}.png")
                        
                        try:
                            # Intento 1: Clic normal
                            button.click()
                            print("  ✓ Clic exitoso con método normal")
                        except Exception as e:
                            print(f"  ✗ Error con clic normal: {e}")
                            
                            try:
                                # Intento 2: Clic con JavaScript
                                driver.execute_script("arguments[0].click();", button)
                                print("  ✓ Clic exitoso con JavaScript")
                            except Exception as e:
                                print(f"  ✗ Error con clic JavaScript: {e}")
                        
                        # Esperar un momento para ver los efectos del clic
                        time.sleep(3)
                        driver.save_screenshot(f"result/assets/diagnostico_despues_clic_{i+1}.png")
                        
                        # Verificar si seguimos en la página de login
                        if "login" not in driver.current_url.lower():
                            print("  ✓ Navegación exitosa! Ya no estamos en la página de login.")
                        else:
                            print("  ✗ Seguimos en la página de login.")
            except Exception as e:
                print(f"Error al analizar botón #{i+1}: {e}")
        
        # Si no se encontró ningún botón específico, intentar con selectores específicos
        print("\nProbando selectores específicos:")
        selectors = [
            ("CSS", "button[kind='secondaryFormSubmit'][data-testid='stBaseButton-secondaryFormSubmit']"),
            ("CSS", "div.stButton button"),
            ("XPATH", "//button//div/p[contains(text(), 'Iniciar Sesión')]/ancestor::button"),
            ("XPATH", "//button[contains(text(), 'Iniciar') or contains(text(), 'Login')]")
        ]
        
        for selector_type, selector in selectors:
            try:
                print(f"\nProbando selector {selector_type}: {selector}")
                if selector_type == "CSS":
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                else:
                    elements = driver.find_elements(By.XPATH, selector)
                
                print(f"Se encontraron {len(elements)} elementos con este selector.")
                
                for i, element in enumerate(elements):
                    try:
                        is_displayed = element.is_displayed()
                        element_text = element.text if element.text else "Sin texto"
                        
                        print(f"  Elemento #{i+1}:")
                        print(f"    - Visible: {is_displayed}")
                        print(f"    - Texto: '{element_text}'")
                        
                        if is_displayed:
                            print("    Intentando hacer clic en este elemento...")
                            driver.save_screenshot(f"result/assets/diagnostico_selector_{selector_type}_{i+1}_antes.png")
                            
                            try:
                                # Intento 1: Clic normal
                                element.click()
                                print("    ✓ Clic exitoso con método normal")
                            except Exception as e:
                                print(f"    ✗ Error con clic normal: {e}")
                                
                                try:
                                    # Intento 2: Clic con JavaScript
                                    driver.execute_script("arguments[0].click();", element)
                                    print("    ✓ Clic exitoso con JavaScript")
                                except Exception as e:
                                    print(f"    ✗ Error con clic JavaScript: {e}")
                            
                            # Esperar un momento para ver los efectos del clic
                            time.sleep(3)
                            driver.save_screenshot(f"result/assets/diagnostico_selector_{selector_type}_{i+1}_despues.png")
                            
                            # Verificar si seguimos en la página de login
                            if "login" not in driver.current_url.lower():
                                print("    ✓ Navegación exitosa! Ya no estamos en la página de login.")
                                return  # Terminar si tuvimos éxito
                            else:
                                print("    ✗ Seguimos en la página de login.")
                    except Exception as e:
                        print(f"    Error al interactuar con elemento #{i+1}: {e}")
            except Exception as e:
                print(f"Error al probar selector {selector_type} - {selector}: {e}")
        
        # Último recurso: Probar con envío de formulario
        print("\nProbando envío de formulario como último recurso...")
        try:
            # Buscar formulario
            forms = driver.find_elements(By.TAG_NAME, "form")
            print(f"Se encontraron {len(forms)} formularios.")
            
            if len(forms) > 0:
                print("Intentando enviar el primer formulario...")
                driver.save_screenshot("result/assets/diagnostico_antes_submit.png")
                forms[0].submit()
                time.sleep(3)
                driver.save_screenshot("result/assets/diagnostico_despues_submit.png")
            else:
                print("No se encontraron formularios para enviar.")
                
            # Intentar con script para enviar cualquier formulario
            print("Intentando enviar cualquier formulario con JavaScript...")
            driver.save_screenshot("result/assets/diagnostico_antes_js_submit.png")
            driver.execute_script("document.querySelector('form') && document.querySelector('form').submit();")
            time.sleep(3)
            driver.save_screenshot("result/assets/diagnostico_despues_js_submit.png")
        except Exception as e:
            print(f"Error al intentar enviar formulario: {e}")
        
        # Captura final
        print("\nTomando captura final...")
        driver.save_screenshot("result/assets/diagnostico_final.png")
        
    except Exception as e:
        print(f"Error durante el diagnóstico: {e}")
    finally:
        # Cerrar el navegador
        print("\nCerrando el navegador...")
        driver.quit()
        
        print("\nDiagnóstico completado. Revisa las capturas de pantalla en la carpeta result/assets/")

if __name__ == "__main__":
    main()
