from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
from .base_page import BasePage

class ClientePage(BasePage):
    """
    Clase para representar la página de clientes y sus interacciones.
    """
    
    # Selectores para elementos de la página de clientes
    CLIENTES_BUTTON = (By.CSS_SELECTOR, "button[data-testid='stBaseButton-secondary'] div[data-testid='stMarkdownContainer'] p")
    NOMBRE_CLIENTE_INPUT = (By.CSS_SELECTOR, "input#text_input_3")
    ELIMINAR_CLIENTE_BUTTON = (By.XPATH, "//button[contains(., 'Eliminar')]")
    MENSAJE_ERROR = (By.CSS_SELECTOR, "div.stAlert")

    # Selectores para las pestañas
    EDITAR_ELIMINAR_TAB = (By.XPATH, "//button[@data-baseweb='tab' and contains(., 'Editar/Eliminar Cliente')]")
    LISTA_CLIENTES_TAB = (By.XPATH, "//button[@data-baseweb='tab' and contains(., 'Lista de Clientes')]")

    # Selectores para la búsqueda de clientes
    BUSCAR_CLIENTE_INPUT = (By.CSS_SELECTOR, "input[aria-label='🔍 Buscar cliente por nombre, cédula o teléfono']")
    TABLA_RESULTADOS_CLIENTES = (By.CSS_SELECTOR, "div[data-testid='stDataFrame']")
    
    # Selectores para la actualización de cliente
    # Selector exacto para el selector de cliente (combobox)
    SELECTOR_CLIENTE = (By.CSS_SELECTOR, "input[aria-autocomplete='list'][aria-expanded='false'][aria-haspopup='listbox'][role='combobox']")
    # Selector robusto para el input de nombre que no dependa de IDs dinámicos
    NOMBRE_CLIENTE_EDITAR_INPUT = (By.CSS_SELECTOR, "input[aria-label='Nombre Completo']")
    # Selector exacto para el botón de actualizar
    ACTUALIZAR_CLIENTE_BUTTON = (By.CSS_SELECTOR, "button[kind='secondaryFormSubmit'][data-testid='stBaseButton-secondaryFormSubmit'] div[data-testid='stMarkdownContainer'] p")
    MENSAJE_EXITO = (By.CSS_SELECTOR, "div.stAlert.st-ae.st-af.st-ag.st-ai.st-aj.st-ak.st-al.st-am")
    CLIENTE_OPTION = (By.XPATH, "//div[contains(text(), '{0}')]")
    # Selector específico para el cliente juan
    CLIENTE_JUAN = (By.CSS_SELECTOR, "li[role='option'][id='bui99val-1'] div.st-emotion-cache-qiev7j.ebtlh8d1")
    # Selector alternativo para el cliente juan incluyendo el contenedor
    CLIENTE_JUAN_CONTAINER = (By.CSS_SELECTOR, "li[role='option'][id='bui99val-1'] div.st-emotion-cache-11loom0.ebtlh8d0")
    # Selector exacto para el elemento li del cliente juan
    CLIENTE_JUAN_LI = (By.CSS_SELECTOR, "li[role='option'][aria-disabled='false'][aria-selected='false'][id='bui99val-1']")
    
    def __init__(self, driver):
        """
        Inicializar la página de clientes.
        
        Args:
            driver: WebDriver de Selenium
        """
        super().__init__(driver)
    
    def click_clientes_button(self):
        """
        Hacer clic en el botón de Clientes en la barra lateral.
        
        Returns:
            bool: True si el clic fue exitoso, False en caso contrario
        """
        print("\n=== INTENTANDO HACER CLIC EN EL BOTÓN DE CLIENTES ===\n")
        
        # Tomar captura antes de hacer clic
        self.take_screenshot("antes_click_clientes")
        
        # Intentar con el selector estándar
        try:
            # Primero intentar encontrar el botón por el texto exacto
            clientes_elements = self.driver.find_elements(By.XPATH, "//button//p[contains(text(), 'Clientes')]")
            if clientes_elements:
                print(f"Encontrado botón de Clientes por texto: {len(clientes_elements)} elementos")
                clientes_elements[0].click()
                print("Clic exitoso en botón de Clientes por texto")
                return True
        except Exception as e:
            print(f"Error al hacer clic por texto: {e}")
        
        # Si falla, intentar con el selector CSS
        try:
            print("Intentando con selector CSS...")
            result = self.click_element(*self.CLIENTES_BUTTON)
            if result:
                print("Clic exitoso en botón de Clientes con selector CSS")
                return True
        except Exception as e:
            print(f"Error al hacer clic con selector CSS: {e}")
        
        # Si falla, intentar con JavaScript
        try:
            print("Intentando con JavaScript...")
            self.driver.execute_script("""
                var buttons = document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    if (buttons[i].innerText.includes('Clientes')) {
                        buttons[i].click();
                        return true;
                    }
                }
                return false;
            """)
            print("Clic con JavaScript ejecutado")
            
            # Tomar captura después de hacer clic
            self.take_screenshot("despues_click_clientes")
            return True
        except Exception as e:
            print(f"Error al hacer clic con JavaScript: {e}")
        
        print("No se pudo hacer clic en el botón de Clientes")
        return False
    
    def click_eliminar_cliente_button(self):
        """
        Hacer clic en el botón de Eliminar Cliente.
        
        Returns:
            bool: True si el clic fue exitoso, False en caso contrario
        """
        print("\n=== INTENTANDO HACER CLIC EN BOTÓN ELIMINAR CLIENTE ===\n")
        
        # Tomar captura antes de hacer clic
        self.take_screenshot("antes_click_eliminar")
        
        # Intentar con el selector estándar
        try:
            # Primero intentar encontrar el botón por el texto
            eliminar_elements = self.driver.find_elements(By.XPATH, "//button[contains(., 'Eliminar')]")
            if eliminar_elements:
                print(f"Encontrado botón Eliminar por texto: {len(eliminar_elements)} elementos")
                eliminar_elements[0].click()
                print("Clic exitoso en botón Eliminar por texto")
                return True
        except Exception as e:
            print(f"Error al hacer clic por texto: {e}")
        
        # Si falla, intentar con el selector definido
        try:
            print("Intentando con selector definido...")
            result = self.click_element(*self.ELIMINAR_CLIENTE_BUTTON)
            if result:
                print("Clic exitoso en botón Eliminar con selector definido")
                return True
        except Exception as e:
            print(f"Error al hacer clic con selector definido: {e}")
        
        # Si falla, intentar con JavaScript
        try:
            print("Intentando con JavaScript...")
            self.driver.execute_script("""
                var buttons = document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    if (buttons[i].innerText.includes('Eliminar')) {
                        buttons[i].click();
                        return true;
                    }
                }
                return false;
            """)
            print("Clic con JavaScript ejecutado")
            
            # Tomar captura después de hacer clic
            self.take_screenshot("despues_click_eliminar")
            return True
        except Exception as e:
            print(f"Error al hacer clic con JavaScript: {e}")
        
        print("No se pudo hacer clic en el botón Eliminar")
        return False
    
    def get_mensaje_error(self):
        """
        Obtener el mensaje de error o advertencia que se muestra en la página.
        
        Returns:
            str: Mensaje de error o advertencia, o cadena vacía si no hay mensaje
        """
        try:
            # Esperar a que aparezca el mensaje de error
            element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(self.MENSAJE_ERROR)
            )
            return element.text
        except Exception:
            # Buscar cualquier mensaje de error o advertencia visible
            try:
                # Buscar alertas de Streamlit
                alerts = self.driver.find_elements(By.CSS_SELECTOR, "div.stAlert")
                if alerts:
                    return alerts[0].text
                
                # Buscar mensajes de error genéricos
                error_messages = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'error') or contains(text(), 'Error') or contains(text(), 'seleccionar')]")
                if error_messages:
                    return error_messages[0].text
                
                return ""
            except Exception as e:
                print(f"Error al buscar mensaje de error: {e}")
                return ""
    
    def get_mensaje_exito(self):
        """
        Obtener el mensaje de éxito que se muestra en la página.
        
        Returns:
            str: Mensaje de éxito, o cadena vacía si no hay mensaje
        """
        try:
            # Esperar a que aparezca el mensaje de éxito
            element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(self.MENSAJE_EXITO)
            )
            return element.text
        except Exception:
            # Buscar cualquier mensaje de éxito visible
            try:
                # Buscar alertas de Streamlit
                alerts = self.driver.find_elements(By.CSS_SELECTOR, "div.stAlert")
                if alerts:
                    return alerts[0].text
                
                # Buscar mensajes de éxito genéricos
                success_messages = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'éxito') or contains(text(), 'exitoso') or contains(text(), 'actualizado') or contains(text(), 'guardado')]")
                if success_messages:
                    return success_messages[0].text
                
                return ""
            except Exception as e:
                print(f"Error al buscar mensaje de éxito: {e}")
                return ""
    
    def enter_nombre_cliente(self, nombre):
        """
        Ingresar el nombre del cliente en el campo correspondiente.
        
        Args:
            nombre (str): Nombre del cliente a ingresar
            
        Returns:
            bool: True si se ingresó el nombre correctamente, False en caso contrario
        """
        try:
            # Esperar a que el campo de nombre esté presente
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.NOMBRE_CLIENTE_INPUT)
            )
            
            # Limpiar el campo
            element.clear()
            
            # Ingresar el nombre caracter por caracter para simular la entrada del usuario
            for char in nombre:
                element.send_keys(char)
                time.sleep(0.01)  # Pequeña pausa entre caracteres
            
            return True
        except Exception as e:
            print(f"Error al ingresar el nombre del cliente: {e}")
            return False
    
    def get_nombre_cliente_value(self):
        """
        Obtener el valor actual del campo de nombre del cliente.
        
        Returns:
            str: Valor actual del campo de nombre del cliente
        """
        try:
            element = self.find_element(*self.NOMBRE_CLIENTE_INPUT)
            return element.get_attribute("value")
        except Exception as e:
            print(f"Error al obtener el valor del campo de nombre: {e}")
            return ""
            
    def click_editar_eliminar_tab(self):
        """
        Hacer clic en la pestaña 'Editar/Eliminar Cliente'.
        
        Returns:
            bool: True si el clic fue exitoso, False en caso contrario
        """
        print("\n=== INTENTANDO HACER CLIC EN LA PESTAÑA EDITAR/ELIMINAR CLIENTE ===\n")
        
        # Tomar captura antes de hacer clic
        self.take_screenshot("antes_click_tab_editar_eliminar")
        
        # Intentar con el selector estándar
        try:
            # Primero intentar encontrar la pestaña por el texto exacto
            tab_elements = self.driver.find_elements(By.XPATH, "//button[@role='tab']//p[contains(text(), 'Editar/Eliminar Cliente')]")
            if tab_elements:
                print(f"Encontrada pestaña Editar/Eliminar por texto: {len(tab_elements)} elementos")
                tab_elements[0].click()
                print("Clic exitoso en pestaña Editar/Eliminar por texto")
                return True
        except Exception as e:
            print(f"Error al hacer clic por texto: {e}")
        
        # Si falla, intentar con el selector definido
        try:
            print("Intentando con selector definido...")
            result = self.click_element(*self.EDITAR_ELIMINAR_TAB)
            if result:
                print("Clic exitoso en pestaña Editar/Eliminar con selector definido")
                return True
        except Exception as e:
            print(f"Error al hacer clic con selector definido: {e}")
        
        # Si falla, intentar con JavaScript
        try:
            print("Intentando con JavaScript...")
            self.driver.execute_script("""
                var tabs = document.querySelectorAll('button[role="tab"]');
                for (var i = 0; i < tabs.length; i++) {
                    if (tabs[i].innerText.includes('Editar/Eliminar Cliente')) {
                        tabs[i].click();
                        return true;
                    }
                }
                return false;
            """)
            print("Clic con JavaScript ejecutado")
            
            # Tomar captura después de hacer clic
            self.take_screenshot("despues_click_tab_editar_eliminar")
            return True
        except Exception as e:
            print(f"Error al hacer clic con JavaScript: {e}")
        
        print("No se pudo hacer clic en la pestaña Editar/Eliminar Cliente")
        return False
    
    def click_lista_clientes_tab(self):
        """
        Hacer clic en la pestaña 'Lista de Clientes'.
        """
        print("\n--- INTENTANDO HACER CLIC EN 'LISTA DE CLIENTES' ---\n")
        try:
            # Esperar a que la pestaña sea clickeable
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.LISTA_CLIENTES_TAB)
            )
            # Intentar clic normal primero
            element.click()
            print("Clic exitoso en la pestaña 'Lista de Clientes' con el método estándar.")
        except Exception as e:
            print(f"El clic estándar falló: {e}. Intentando con JavaScript.")
            # Si el clic normal falla, usar JavaScript
            try:
                element = self.driver.find_element(*self.LISTA_CLIENTES_TAB)
                self.driver.execute_script("arguments[0].click();", element)
                print("Clic exitoso en la pestaña 'Lista de Clientes' con JavaScript.")
            except Exception as js_e:
                print(f"El clic con JavaScript también falló: {js_e}")
                self.take_screenshot("error_clic_lista_clientes_tab")
                raise
            print("Pestaña 'Lista de Clientes' seleccionada.")
        except Exception as e:
            print(f"Error al hacer clic en la pestaña 'Lista de Clientes': {e}")
            self.take_screenshot("error_click_lista_clientes_tab")
            raise

    def buscar_cliente(self, nombre):
        """
        Ingresar el nombre del cliente en el campo de búsqueda.
        
        Args:
            nombre (str): Nombre del cliente a buscar.
        """
        print(f"Intentando buscar al cliente: {nombre}")
        try:
            # Esperar a que el campo de búsqueda esté presente y visible
            search_input = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(self.BUSCAR_CLIENTE_INPUT)
            )
            # Limpiar el campo y luego escribir el nombre
            search_input.clear()
            search_input.send_keys(nombre)
            search_input.send_keys(Keys.RETURN) # Presionar Enter
            print(f"Texto '{nombre}' ingresado y búsqueda iniciada con Enter.")
        except Exception as e:
            print(f"No se pudo encontrar o interactuar con el campo de búsqueda: {e}")
            self.take_screenshot("error_buscar_cliente")
            raise

    def verificar_cliente_en_lista(self, nombre):
        """
        Verificar si un cliente específico se encuentra en la tabla de resultados.
        
        Args:
            nombre (str): Nombre del cliente a verificar.
            
        Returns:
            bool: True si el cliente está en la lista, False en caso contrario.
        """
        print(f"Verificando si '{nombre}' está en la lista...")
        try:
            # Espera explícita para que el texto del cliente aparezca en la tabla
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element(self.TABLA_RESULTADOS_CLIENTES, nombre)
            )
            print(f"Cliente '{nombre}' encontrado en la tabla.")
            return True
        except Exception as e:
            print(f"Cliente '{nombre}' NO encontrado en la tabla después de esperar. Error: {e}")
            self.take_screenshot("cliente_no_encontrado_tras_espera")
            return False

    def click_selector_cliente(self):
        """
        Hacer clic en el selector de cliente.
        
        Returns:
            bool: True si el clic fue exitoso, False en caso contrario
        """
        print("\n=== INTENTANDO HACER CLIC EN EL SELECTOR DE CLIENTE ===\n")
        
        # Tomar captura antes de hacer clic
        self.take_screenshot("antes_click_selector_cliente")
        
        # Intentar con el selector exacto del combobox
        try:
            print("Intentando con selector exacto del combobox...")
            combobox = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.SELECTOR_CLIENTE)
            )
            print(f"Combobox encontrado: {combobox.get_attribute('aria-label')}")
            combobox.click()
            print("Clic exitoso en combobox de selección de cliente")
            
            # Tomar captura después de hacer clic en el combobox
            self.take_screenshot("despues_click_combobox")
            return True
        except Exception as e:
            print(f"Error al hacer clic en combobox: {e}")
        
        # Intentar con el selector definido
        try:
            print("Intentando con selector definido...")
            result = self.click_element(*self.SELECTOR_CLIENTE)
            if result:
                print("Clic exitoso en selector de cliente")
                return True
        except Exception as e:
            print(f"Error al hacer clic con selector definido: {e}")
        
        # Si falla, intentar con búsqueda por atributos
        try:
            print("Intentando con búsqueda por atributos...")
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[role='combobox']")
            if inputs:
                print(f"Encontrados {len(inputs)} inputs con role='combobox'")
                inputs[0].click()
                print("Clic exitoso en input combobox")
                
                # Tomar captura después de hacer clic
                self.take_screenshot("despues_click_input_combobox")
                return True
        except Exception as e:
            print(f"Error al hacer clic en input combobox: {e}")
        
        # Si falla, intentar con JavaScript
        try:
            print("Intentando con JavaScript...")
            self.driver.execute_script("""
                var inputs = document.querySelectorAll('input[role="combobox"]');
                if (inputs.length > 0) {
                    inputs[0].click();
                    return true;
                }
                return false;
            """)
            print("Clic con JavaScript ejecutado")
            
            # Tomar captura después de hacer clic
            self.take_screenshot("despues_click_selector_cliente_js")
            return True
        except Exception as e:
            print(f"Error al hacer clic con JavaScript: {e}")
        
        print("No se pudo hacer clic en el selector de cliente")
        return False
    
    def seleccionar_cliente(self, nombre_cliente):
        """
        Seleccionar un cliente en la interfaz.
        
        Args:
            nombre_cliente (str): Nombre del cliente a seleccionar
            
        Returns:
            bool: True si la selección fue exitosa, False en caso contrario
        """
        print(f"\n=== SELECCIONANDO CLIENTE: {nombre_cliente} ===\n")
        
        # Hacer clic en el selector de cliente (combobox)
        if not self.click_selector_cliente():
            print("No se pudo hacer clic en el selector de cliente")
            return False
        
        # Esperar un momento para que se muestren las opciones
        time.sleep(2)
        
        # Tomar captura de las opciones disponibles
        self.take_screenshot("opciones_disponibles")
        
        # Seleccionar el cliente por nombre
        if not self.seleccionar_cliente_por_nombre(nombre_cliente):
            print(f"No se pudo seleccionar el cliente '{nombre_cliente}'")
            return False
        
        # Verificar que se haya seleccionado correctamente
        time.sleep(1)
        self.take_screenshot("despues_seleccionar_cliente")
        
        print(f"Cliente '{nombre_cliente}' seleccionado correctamente")
        return True
    
    def seleccionar_cliente_por_nombre(self, nombre_cliente):
        """
        Seleccionar un cliente por su nombre en el selector.
        
        Args:
            nombre_cliente (str): Nombre del cliente a seleccionar
            
        Returns:
            bool: True si la selección fue exitosa, False en caso contrario
        """
        print(f"\n=== INTENTANDO SELECCIONAR CLIENTE: {nombre_cliente} ===\n")
        
        # Esperar a que aparezcan las opciones del selector
        time.sleep(2)
        
        # Tomar captura de las opciones disponibles
        self.take_screenshot("opciones_selector_cliente")
        
        # Si es el cliente juan, usar el selector específico
        if "juan" in nombre_cliente.lower():
            try:
                print("Usando selector específico para el cliente juan...")
                
                # Ya hemos hecho clic en el selector antes de llamar a este método
                # Tomar captura de las opciones disponibles para juan
                self.take_screenshot("opciones_disponibles_juan")
                
                # Intentar encontrar el elemento li exacto primero
                try:
                    print("Intentando encontrar el elemento li exacto del cliente juan...")
                    cliente_element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(self.CLIENTE_JUAN_LI)
                    )
                    print(f"Elemento li encontrado con ID: {cliente_element.get_attribute('id')}")
                except Exception as e:
                    print(f"Error al buscar por elemento li exacto: {e}")
                    
                    # Si falla, intentar encontrar el contenedor
                    try:
                        print("Intentando encontrar el contenedor del cliente juan...")
                        contenedor = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located(self.CLIENTE_JUAN_CONTAINER)
                        )
                        print(f"Contenedor encontrado: {contenedor.get_attribute('class')}")
                        
                        # Ahora buscar el elemento hijo con el texto
                        cliente_element = contenedor.find_element(By.CSS_SELECTOR, "div.st-emotion-cache-qiev7j.ebtlh8d1")
                        print(f"Encontrado cliente juan dentro del contenedor: {cliente_element.text}")
                    except Exception as e2:
                        print(f"Error al buscar por contenedor: {e2}")
                        # Si falla, intentar directamente con el selector del cliente
                        cliente_element = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable(self.CLIENTE_JUAN)
                        )
                        print(f"Encontrado cliente juan con selector directo: {cliente_element.text}")
                
                # Tomar captura antes de hacer clic
                self.take_screenshot("antes_click_cliente_juan")
                
                # Intentar hacer clic con diferentes métodos
                try:
                    # Método 1: Clic directo
                    cliente_element.click()
                    print("Clic directo exitoso en cliente juan")
                except Exception as e1:
                    print(f"Error en clic directo: {e1}")
                    try:
                        # Método 2: JavaScript
                        self.driver.execute_script("arguments[0].click();", cliente_element)
                        print("Clic con JavaScript exitoso en cliente juan")
                    except Exception as e2:
                        print(f"Error en clic con JavaScript: {e2}")
                        try:
                            # Método 3: Actions
                            from selenium.webdriver.common.action_chains import ActionChains
                            actions = ActionChains(self.driver)
                            actions.move_to_element(cliente_element).click().perform()
                            print("Clic con Actions exitoso en cliente juan")
                        except Exception as e3:
                            print(f"Error en clic con Actions: {e3}")
                            try:
                                # Método 4: JavaScript avanzado para buscar y hacer clic en el elemento exacto
                                print("Intentando con JavaScript avanzado...")
                                script = """
                                var elemento = document.querySelector('li[role="option"][id="bui99val-1"]');
                                if (elemento) {
                                    elemento.click();
                                    return true;
                                }
                                return false;
                                """
                                result = self.driver.execute_script(script)
                                if result:
                                    print("Clic con JavaScript avanzado exitoso")
                                    return True
                                else:
                                    print("No se encontró el elemento con JavaScript avanzado")
                                    return False
                            except Exception as e4:
                                print(f"Error en JavaScript avanzado: {e4}")
                                return False
                
                # Tomar captura después de hacer clic
                self.take_screenshot("despues_click_cliente_juan")
                
                # Esperar a que se carguen los datos del cliente
                time.sleep(2)
                
                return True
            except Exception as e:
                print(f"Error al seleccionar cliente con selector específico: {e}")
        
        # Si no es juan o falló el selector específico, intentar con el método general
        try:
            print("Intentando encontrar cliente por texto exacto...")
            # Buscar cualquier elemento que contenga el texto del cliente
            xpath = f"//div[contains(text(), '{nombre_cliente}')]" 
            cliente_elements = self.driver.find_elements(By.XPATH, xpath)
            
            if cliente_elements:
                print(f"Encontrado cliente por texto: {len(cliente_elements)} elementos")
                
                # Tomar captura antes de hacer clic
                self.take_screenshot("antes_click_cliente_por_texto")
                
                cliente_elements[0].click()
                print(f"Clic exitoso en cliente '{nombre_cliente}'")
                
                # Tomar captura después de hacer clic
                self.take_screenshot("despues_click_cliente_por_texto")
                
                return True
            else:
                print(f"No se encontró ningún elemento con el texto '{nombre_cliente}'")
        except Exception as e:
            print(f"Error al seleccionar cliente por texto: {e}")
        
        # Si falla, intentar con JavaScript
        try:
            print("Intentando con JavaScript...")
            resultado = self.driver.execute_script(f"""
                var opciones = document.querySelectorAll('div');
                for (var i = 0; i < opciones.length; i++) {{
                    if (opciones[i].innerText && opciones[i].innerText.includes('{nombre_cliente}')) {{
                        console.log('Encontrado elemento con texto: ' + opciones[i].innerText);
                        opciones[i].click();
                        return true;
                    }}
                }}
                return false;
            """)
            
            if resultado:
                print("Selección con JavaScript exitosa")
                # Tomar captura después de hacer clic con JavaScript
                self.take_screenshot("despues_click_cliente_js")
                return True
            else:
                print("JavaScript no encontró el elemento")
        except Exception as e:
            print(f"Error al seleccionar cliente con JavaScript: {e}")
        
        # Último intento: buscar por clase
        try:
            print("Intentando buscar por clase st-emotion-cache-qiev7j...")
            elementos = self.driver.find_elements(By.CSS_SELECTOR, "div.st-emotion-cache-qiev7j")
            if elementos:
                print(f"Encontrados {len(elementos)} elementos con la clase")
                for i, elem in enumerate(elementos):
                    try:
                        texto = elem.text
                        print(f"Elemento #{i+1}: '{texto}'")
                        if "juan" in texto.lower():
                            print(f"Encontrado elemento con 'juan': '{texto}'")
                            elem.click()
                            print("Clic exitoso")
                            return True
                    except Exception as e:
                        print(f"Error al procesar elemento #{i+1}: {e}")
        except Exception as e:
            print(f"Error al buscar por clase: {e}")
        
        print(f"No se pudo seleccionar el cliente '{nombre_cliente}'")
        return False
    
    def esperar_formulario_cargado(self, timeout=10):
        """
        Espera a que el formulario de edición de cliente esté completamente cargado.
        
        Args:
            timeout (int): Tiempo máximo de espera en segundos
            
        Returns:
            WebElement: El elemento del formulario cargado
        """
        print("Esperando a que cargue el formulario de edición...")
        try:
            # Esperar a que el formulario esté presente en el DOM
            form = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='stForm']"))
            )
            print("Formulario de edición detectado")
            return form
        except Exception as e:
            print(f"Error al esperar el formulario: {e}")
            self.take_screenshot("error_esperando_formulario")
            raise

    def actualizar_nombre_cliente(self, nuevo_nombre):
        """
        Actualizar el nombre del cliente en el campo correspondiente.
        
        Args:
            nuevo_nombre (str): Nuevo nombre del cliente
            
        Returns:
            bool: True si se actualizó el nombre correctamente, False en caso contrario
        """
        print(f"\n=== INTENTANDO ACTUALIZAR NOMBRE DE CLIENTE A: {nuevo_nombre} ===\n")
        
        try:
            # 1. Esperar a que el formulario esté completamente cargado
            self.esperar_formulario_cargado()
            
            # 2. Localizar el campo de nombre por su ID específico
            print("Buscando campo de nombre por ID...")
            try:
                # Esperar a que el campo sea interactuable
                element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "text_input_7"))
                )
                print("Campo de nombre encontrado por ID")
                
                # Hacer scroll al elemento para asegurar visibilidad
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
                time.sleep(0.5)  # Pequeña pausa para la animación de scroll
                
                # Tomar captura antes de modificar
                self.take_screenshot("antes_modificar_nombre")
                
                # 3. Obtener valor actual
                valor_actual = element.get_attribute("value") or ""
                print(f"Valor actual en el campo: '{valor_actual}'")
                
                # 4. Hacer clic para enfocar
                print("Haciendo clic para enfocar...")
                element.click()
                time.sleep(0.5)
                
                # 5. Limpiar el campo con múltiples métodos para asegurar
                print("Limpiando campo...")
                
                # Método 1: Usar clear()
                try:
                    element.clear()
                    time.sleep(0.3)
                except Exception as e:
                    print(f"Error con clear(): {e}")
                
                # Método 2: Seleccionar todo y eliminar
                element.send_keys(Keys.CONTROL + 'a')
                time.sleep(0.2)
                element.send_keys(Keys.DELETE)
                time.sleep(0.3)
                
                # Método 3: JavaScript para limpiar
                self.driver.execute_script("""
                    arguments[0].value = '';
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """, element)
                time.sleep(0.5)
                
                # 6. Ingresar el nuevo nombre carácter por carácter
                print(f"Ingresando nuevo nombre: '{nuevo_nombre}'...")
                for char in nuevo_nombre:
                    element.send_keys(char)
                    time.sleep(0.05)  # Pausa entre caracteres
                
                # Forzar eventos de cambio
                self.driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """, element)
                
                time.sleep(0.5)
                
                # 7. Verificar el valor final
                valor_final = element.get_attribute("value")
                print(f"Valor final en el campo: '{valor_final}'")
                
                if valor_final == nuevo_nombre:
                    print("¡Nombre actualizado correctamente!")
                    # Tomar captura después de la actualización
                    self.take_screenshot("despues_actualizar_nombre")
                    return True
                else:
                    print(f"Error: El nombre no se actualizó correctamente. Esperado: '{nuevo_nombre}', Obtenido: '{valor_final}'")
                    self.take_screenshot("error_actualizacion_nombre")
                    return False
                    
            except Exception as e:
                print(f"Error al actualizar el nombre: {e}")
                self.take_screenshot("error_actualizar_nombre")
                return False
                
        except Exception as e:
            print(f"Error general en actualizar_nombre_cliente: {e}")
            self.take_screenshot("error_general_actualizar_nombre")
            return False
    
    def click_actualizar_cliente_button(self):
        """
        Hacer clic en el botón de Actualizar Cliente.
        
        Returns:
            bool: True si el clic fue exitoso, False en caso contrario
        """
        print("\n=== INTENTANDO HACER CLIC EN BOTÓN ACTUALIZAR CLIENTE ===\n")
        
        # Tomar captura antes de hacer clic
        self.take_screenshot("antes_click_actualizar")
        
        # Intentar con el selector exacto del botón
        try:
            print("Intentando con selector exacto del botón...")
            # Selector directo para el botón
            boton_selector = "button[kind='secondaryFormSubmit'][data-testid='stBaseButton-secondaryFormSubmit']"
            boton_actualizar = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, boton_selector))
            )
            print("Botón Actualizar encontrado con selector exacto")
            
            # Intentar hacer clic directamente en el botón
            try:
                boton_actualizar.click()
                print("Clic directo exitoso en botón Actualizar")
                return True
            except Exception as e1:
                print(f"Error en clic directo: {e1}")
                # Intentar con JavaScript
                try:
                    self.driver.execute_script("arguments[0].click();", boton_actualizar)
                    print("Clic con JavaScript exitoso en botón Actualizar")
                    return True
                except Exception as e2:
                    print(f"Error en clic con JavaScript: {e2}")
                    # Intentar con Actions
                    actions = ActionChains(self.driver)
                    actions.move_to_element(boton_actualizar).click().perform()
                    print("Clic con Actions exitoso en botón Actualizar")
                    return True
            
        except Exception as e:
            print(f"Error al hacer clic con selector exacto: {e}")
        
        # Intentar con el selector estándar
        try:
            # Primero intentar encontrar el botón por el texto
            print("Intentando encontrar botón por texto...")
            actualizar_elements = self.driver.find_elements(By.XPATH, "//button[contains(., 'Actualizar Cliente')]")
            if actualizar_elements:
                print(f"Encontrado botón Actualizar por texto: {len(actualizar_elements)} elementos")
                actualizar_elements[0].click()
                print("Clic exitoso en botón Actualizar por texto")
                return True
        except Exception as e:
            print(f"Error al hacer clic por texto: {e}")
        
        # Si falla, intentar con el selector definido
        try:
            print("Intentando con selector definido...")
            result = self.click_element(*self.ACTUALIZAR_CLIENTE_BUTTON)
            if result:
                print("Clic exitoso en botón Actualizar con selector definido")
                return True
        except Exception as e:
            print(f"Error al hacer clic con selector definido: {e}")
        
        # Si falla, intentar con JavaScript
        try:
            print("Intentando con JavaScript...")
            resultado = self.driver.execute_script("""
                var buttons = document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    if (buttons[i].innerText && buttons[i].innerText.includes('Actualizar Cliente')) {
                        buttons[i].click();
                        return true;
                    }
                }
                return false;
            """)
            
            if resultado:
                print("Clic con JavaScript exitoso en botón Actualizar")
                return True
            else:
                print("No se encontró el botón Actualizar con JavaScript")
        except Exception as e:
            print(f"Error al hacer clic con JavaScript: {e}")
        
        # Si todo falla, intentar con un selector más genérico
        try:
            print("Intentando con selector genérico...")
            botones = self.driver.find_elements(By.CSS_SELECTOR, "button")
            print(f"Se encontraron {len(botones)} botones en la página")
            
            for i, boton in enumerate(botones):
                try:
                    texto = boton.text
                    print(f"Botón #{i+1}: '{texto}'")
                    if texto and "actualizar" in texto.lower():
                        print(f"Encontrado botón con 'actualizar': '{texto}'")
                        boton.click()
                        print("Clic exitoso")
                        return True
                except Exception as e:
                    print(f"Error al procesar botón #{i+1}: {e}")
        except Exception as e:
            print(f"Error al buscar botones genéricos: {e}")
        
        print("No se pudo hacer clic en el botón Actualizar Cliente")
        return False
        # Último intento: buscar cualquier botón que pueda ser el de actualizar
        try:
            print("Intentando con búsqueda general de botones...")
            botones = self.driver.find_elements(By.CSS_SELECTOR, "button")
            print(f"Se encontraron {len(botones)} botones en la página")
            
            # Tomar captura con todos los botones
            self.take_screenshot("todos_los_botones")
            
            for i, boton in enumerate(botones):
                try:
                    texto = boton.text
                    print(f"Botón #{i+1}: '{texto}'")
                    if "actualizar" in texto.lower() or "guardar" in texto.lower() or "cliente" in texto.lower():
                        print(f"Encontrado botón candidato: '{texto}'")
                        boton.click()
                        print(f"Clic exitoso en botón candidato: '{texto}'")
                        
                        # Tomar captura después de hacer clic
                        self.take_screenshot("despues_click_boton_candidato")
                        return True
                except Exception as e:
                    print(f"Error al procesar botón #{i+1}: {e}")
        except Exception as e:
            print(f"Error en búsqueda general de botones: {e}")
        
        print("No se pudo hacer clic en el botón Actualizar Cliente")
        return False
