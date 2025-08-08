# Sistema de Préstamos con Pruebas Automatizadas

Este proyecto es un sistema de gestión de préstamos desarrollado en Python con Streamlit, y cuenta con un conjunto de pruebas automatizadas utilizando Selenium.

## Información

-   **Sustentante**: Victor Lorenzo Hernandez Sosa
-   **Facilitador**: Kelyn Tejada Belliard

## Sobre el Proyecto

Hola, soy Victor Lorenzo Hernandez Sosa, un estudiante del Instituto Tecnológico de las Américas (ITLA).

Este es un sistema de préstamos que había realizado previamente con Python y Streamlit. Lo he tomado como base para implementar pruebas automatizadas con Selenium, como parte de una asignación facilitada por mi maestro Kelyn Tejada Belliard.

El objetivo es demostrar la aplicación de pruebas automatizadas en un proyecto real, asegurando la calidad y el correcto funcionamiento de la aplicación.

## Agradecimientos

Quisiera agradecer a **Luis Aneuris Tavarez** y a **Kelyn Tejada Belliard** por su apoyo en esta asignación, la cual estoy seguro que me beneficiará a la hora de trabajar en ambientes laborales futuros.

## Tecnologías Utilizadas

-   **Lenguaje de Programación**: Python
-   **Framework Web**: Streamlit
-   **Pruebas Automatizadas**: Selenium

## Estructura del Proyecto

El repositorio está organizado de la siguiente manera:

-   `project/`: Contiene todos los archivos relacionados con las pruebas automatizadas, incluyendo los scripts de prueba, configuraciones y resultados.
-   `app.py`: El archivo principal para ejecutar la aplicación Streamlit.
-   `requirements.txt`: Lista de dependencias de Python para el proyecto.

## Cómo Empezar

Para ejecutar este proyecto localmente, sigue estos pasos:

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/Zzsososa/Sistem_Prestamos_Stramlit.git
    cd prestamos_streamlit

2.  **Crea un entorno virtual e instala las dependencias:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Ejecuta la aplicación de Streamlit:**
    ```bash
    streamlit run app.py
    ```

4.  **Ejecuta las pruebas de Selenium:**
    ```bash
    python -m pytest tests\test_login.py tests\test_cliente_limite.py tests\test_cliente_eliminar_negativo.py tests\test_cliente_actualizar.py tests/test_cliente_busqueda.py -v --html=result\report.html
    ```
