import pytest
import os
from datetime import datetime

@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Configuración inicial para las pruebas"""
    # Crear directorios para resultados si no existen
    result_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'result')
    assets_dir = os.path.join(result_dir, 'assets')
    
    os.makedirs(result_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)
    
    # Configurar metadatos para el reporte HTML
    config._metadata = {
        "Proyecto": "Sistema de Préstamos",
        "Fecha de ejecución": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Entorno": "Pruebas"
    }

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook para personalizar el reporte de pruebas"""
    outcome = yield
    report = outcome.get_result()
    
    # Añadir capturas de pantalla al reporte HTML
    if report.when == "call":
        xfail = hasattr(report, "wasxfail")
        if (report.skipped and xfail) or (report.failed and not xfail):
            # Añadir información adicional al reporte en caso de fallo
            report.sections.append(("Información de fallo", "La prueba ha fallado. Revisar capturas de pantalla."))
