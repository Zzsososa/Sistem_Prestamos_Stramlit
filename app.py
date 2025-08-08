import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import plotly.express as px
import plotly.graph_objects as go
from passlib.hash import pbkdf2_sha256
import uuid
import json
import time
import io
from xlsxwriter import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Préstamos",
    page_icon="💰",
    layout="wide"
)

# Funciones para manejo de contraseñas y seguridad
def hash_password(password):
    """Genera un hash seguro para la contraseña"""
    return pbkdf2_sha256.hash(password)

def verify_password(stored_password, provided_password):
    """Verifica si la contraseña proporcionada coincide con el hash almacenado"""
    return pbkdf2_sha256.verify(provided_password, stored_password)

def registrar_actividad(usuario, accion, detalles=None):
    """Registra una actividad en el log de auditoría"""
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ip_address = "local"  # En un entorno real, se obtendría la IP del cliente
    
    if detalles:
        detalles_json = json.dumps(detalles)
    else:
        detalles_json = None
        
    c.execute(
        "INSERT INTO log_auditoria (timestamp, usuario, accion, detalles, ip_address) VALUES (?, ?, ?, ?, ?)", 
        (timestamp, usuario, accion, detalles_json, ip_address)
    )
    
    conn.commit()
    conn.close()

def autenticar(usuario, contrasena):
    """Autentica a un usuario verificando su contraseña hasheada"""
    try:
        conn = sqlite3.connect('prestamos.db')
        c = conn.cursor()
        
        # Verificar que los campos no estén vacíos
        if not usuario or not contrasena:
            return False, None, "Usuario y contraseña son obligatorios"
        
        # Buscar el usuario en la base de datos
        c.execute("SELECT id, usuario, password_hash, nivel_acceso, activo FROM usuarios WHERE usuario = ?", (usuario,))
        resultado = c.fetchone()
        
        if not resultado:
            conn.close()
            # Registrar intento fallido
            registrar_actividad("sistema", "intento_login_fallido", {"usuario_intentado": usuario, "motivo": "usuario_no_existe"})
            return False, None, "Usuario no encontrado"
        
        user_id, username, password_hash, nivel_acceso, activo = resultado
        
        # Verificar si la cuenta está activa
        if activo != 1:
            conn.close()
            registrar_actividad("sistema", "intento_login_fallido", {"usuario": usuario, "motivo": "cuenta_inactiva"})
            return False, None, "Cuenta desactivada. Contacte al administrador."
        
        # Verificar la contraseña
        try:
            if verify_password(password_hash, contrasena):
                # Actualizar último acceso
                ultimo_acceso = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                c.execute("UPDATE usuarios SET ultimo_acceso = ? WHERE id = ?", (ultimo_acceso, user_id))
                conn.commit()
                conn.close()
                
                # Registrar login exitoso
                registrar_actividad(usuario, "login_exitoso")
                
                return True, nivel_acceso, "Autenticación exitosa"
            else:
                conn.close()
                # Registrar intento fallido
                registrar_actividad("sistema", "intento_login_fallido", {"usuario": usuario, "motivo": "contrasena_incorrecta"})
                return False, None, "Contraseña incorrecta"
        except Exception as e:
            conn.close()
            # Registrar error en verificación de contraseña
            registrar_actividad("sistema", "error_autenticacion", {"usuario": usuario, "error": str(e)})
            return False, None, f"Error en la verificación: {str(e)}"
    except Exception as e:
        # Capturar cualquier error inesperado
        try:
            conn.close()
        except:
            pass
        return False, None, f"Error de autenticación: {str(e)}"

def obtener_usuarios():
    """Obtiene la lista de usuarios del sistema"""
    conn = sqlite3.connect('prestamos.db')
    query = """
    SELECT id, usuario, nivel_acceso, nombre_completo, email, ultimo_acceso, activo 
    FROM usuarios
    ORDER BY usuario
    """
    usuarios = pd.read_sql_query(query, conn)
    conn.close()
    return usuarios

def crear_usuario(usuario, contrasena, nivel_acceso, nombre_completo=None, email=None):
    """Crea un nuevo usuario en el sistema"""
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    
    try:
        # Verificar si el usuario ya existe
        c.execute("SELECT id FROM usuarios WHERE usuario = ?", (usuario,))
        if c.fetchone():
            conn.close()
            return False, "El nombre de usuario ya está en uso"
        
        # Hash de la contraseña
        password_hash = hash_password(contrasena)
        
        # Insertar nuevo usuario
        c.execute(
            "INSERT INTO usuarios (usuario, password_hash, nivel_acceso, nombre_completo, email, activo) VALUES (?, ?, ?, ?, ?, 1)",
            (usuario, password_hash, nivel_acceso, nombre_completo, email)
        )
        
        conn.commit()
        
        # Registrar la creación del usuario
        usuario_actual = st.session_state.get('usuario', 'sistema')
        registrar_actividad(usuario_actual, "creacion_usuario", {"usuario_creado": usuario, "nivel": nivel_acceso})
        
        conn.close()
        return True, "Usuario creado exitosamente"
    except Exception as e:
        conn.close()
        return False, f"Error al crear usuario: {str(e)}"

def cambiar_contrasena(usuario_id, contrasena_actual, nueva_contrasena):
    """Cambia la contraseña de un usuario"""
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    
    try:
        # Obtener hash actual
        c.execute("SELECT password_hash FROM usuarios WHERE id = ?", (usuario_id,))
        resultado = c.fetchone()
        
        if not resultado:
            conn.close()
            return False, "Usuario no encontrado"
        
        password_hash = resultado[0]
        
        # Verificar contraseña actual
        if not verify_password(password_hash, contrasena_actual):
            conn.close()
            return False, "Contraseña actual incorrecta"
        
        # Generar nuevo hash
        nuevo_hash = hash_password(nueva_contrasena)
        
        # Actualizar contraseña
        c.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?", (nuevo_hash, usuario_id))
        conn.commit()
        
        # Registrar cambio de contraseña
        c.execute("SELECT usuario FROM usuarios WHERE id = ?", (usuario_id,))
        nombre_usuario = c.fetchone()[0]
        
        usuario_actual = st.session_state.get('usuario', 'sistema')
        registrar_actividad(usuario_actual, "cambio_contrasena", {"usuario_modificado": nombre_usuario})
        
        conn.close()
        return True, "Contraseña actualizada exitosamente"
    except Exception as e:
        conn.close()
        return False, f"Error al cambiar contraseña: {str(e)}"

def actualizar_estado_usuario(usuario_id, activo):
    """Activa o desactiva un usuario"""
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    
    try:
        # Verificar si el usuario existe
        c.execute("SELECT usuario FROM usuarios WHERE id = ?", (usuario_id,))
        resultado = c.fetchone()
        
        if not resultado:
            conn.close()
            return False, "Usuario no encontrado"
        
        nombre_usuario = resultado[0]
        
        # No permitir desactivar al usuario admin
        if nombre_usuario == 'admin' and activo == 0:
            conn.close()
            return False, "No se puede desactivar al usuario administrador principal"
        
        # Actualizar estado
        c.execute("UPDATE usuarios SET activo = ? WHERE id = ?", (activo, usuario_id))
        conn.commit()
        
        # Registrar cambio de estado
        estado = "activado" if activo == 1 else "desactivado"
        usuario_actual = st.session_state.get('usuario', 'sistema')
        registrar_actividad(usuario_actual, f"usuario_{estado}", {"usuario_modificado": nombre_usuario})
        
        conn.close()
        return True, f"Usuario {estado} exitosamente"
    except Exception as e:
        conn.close()
        return False, f"Error al actualizar estado del usuario: {str(e)}"

def obtener_log_auditoria(limite=100, filtro_usuario=None, filtro_accion=None):
    """Obtiene el registro de actividad del sistema"""
    conn = sqlite3.connect('prestamos.db')
    
    query = "SELECT id, timestamp, usuario, accion, detalles, ip_address FROM log_auditoria"
    params = []
    
    # Aplicar filtros si existen
    where_clauses = []
    if filtro_usuario:
        where_clauses.append("usuario = ?")
        params.append(filtro_usuario)
    
    if filtro_accion:
        where_clauses.append("accion LIKE ?")
        params.append(f"%{filtro_accion}%")
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limite)
    
    log = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return log

def cerrar_sesion():
    """Cierra la sesión del usuario actual"""
    # Registrar la actividad de cierre de sesión
    if st.session_state.get('usuario'):
        registrar_actividad(st.session_state.usuario, "logout")
    
    # Reiniciar variables de sesión
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.session_state.nivel_acceso = None
    st.session_state.menu = "Dashboard"

def verificar_permiso(nivel_requerido):
    """Verifica si el usuario tiene el nivel de acceso requerido"""
    niveles = {
        "consulta": 1,
        "operador": 2,
        "administrador": 3
    }
    
    nivel_usuario = niveles.get(st.session_state.nivel_acceso, 0)
    nivel_necesario = niveles.get(nivel_requerido, 0)
    
    return nivel_usuario >= nivel_necesario

# Crear base de datos si no existe
def init_db():
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    
    # Crear tabla de usuarios con nivel de acceso
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            usuario TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nivel_acceso TEXT NOT NULL,
            nombre_completo TEXT,
            email TEXT,
            ultimo_acceso TEXT,
            activo INTEGER DEFAULT 1
        )
    ''')
    
    # Crear tabla de log de auditoría
    c.execute('''
        CREATE TABLE IF NOT EXISTS log_auditoria (
            id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            usuario TEXT NOT NULL,
            accion TEXT NOT NULL,
            detalles TEXT,
            ip_address TEXT
        )
    ''')
    
    # Verificar si existe el usuario admin
    c.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
    if not c.fetchone():
        # Crear usuario admin con contraseña hasheada
        admin_password_hash = hash_password('admin123')
        c.execute(
            "INSERT INTO usuarios (usuario, password_hash, nivel_acceso, nombre_completo, email) VALUES (?, ?, ?, ?, ?)", 
            ('admin', admin_password_hash, 'administrador', 'Administrador del Sistema', 'admin@sistema.com')
        )
        
        # Registrar la creación del usuario admin en el log
        c.execute(
            "INSERT INTO log_auditoria (timestamp, usuario, accion, detalles, ip_address) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'sistema', 'creacion_usuario', json.dumps({'usuario': 'admin', 'nivel': 'administrador'}), 'local')
        )
    
    # Crear tabla de clientes
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            cedula TEXT UNIQUE NOT NULL,
            telefono TEXT NOT NULL
        )
    ''')
    
    # Crear tabla de préstamos
    c.execute('''
        CREATE TABLE IF NOT EXISTS prestamos (
            id INTEGER PRIMARY KEY,
            cliente_id INTEGER NOT NULL,
            monto REAL NOT NULL,
            fecha_prestamo DATE NOT NULL,
            fecha_vencimiento DATE NOT NULL,
            tasa_interes REAL,
            estado TEXT DEFAULT 'Pendiente',
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    ''')
    
    # Crear tabla de pagos
    c.execute('''
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY,
            prestamo_id INTEGER NOT NULL,
            fecha_pago DATE NOT NULL,
            monto_pagado REAL NOT NULL,
            FOREIGN KEY (prestamo_id) REFERENCES prestamos(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Inicializar la base de datos
init_db()

# La función de autenticación ya está definida al inicio del archivo

# Inicializar estado de la sesión
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    
if 'menu' not in st.session_state:
    st.session_state.menu = "Dashboard"
    
# Inicializar estado de creación de préstamo
if 'prestamo_creado' not in st.session_state:
    st.session_state.prestamo_creado = False

# Función para cerrar sesión
def cerrar_sesion():
    st.session_state.autenticado = False

# Funciones para gestión de clientes
def agregar_cliente(nombre, cedula, telefono):
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO clientes (nombre, cedula, telefono) VALUES (?, ?, ?)", 
                 (nombre, cedula, telefono))
        conn.commit()
        exito = True
        mensaje = "Cliente agregado exitosamente"
    except sqlite3.IntegrityError:
        exito = False
        mensaje = "Error: La cédula ya existe en la base de datos"
    conn.close()
    return exito, mensaje

def obtener_clientes():
    conn = sqlite3.connect('prestamos.db')
    query = "SELECT id, nombre, cedula, telefono FROM clientes"
    clientes = pd.read_sql_query(query, conn)
    conn.close()
    return clientes

def obtener_cliente(id_cliente):
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    c.execute("SELECT id, nombre, cedula, telefono FROM clientes WHERE id = ?", (id_cliente,))
    cliente = c.fetchone()
    conn.close()
    return cliente

def actualizar_cliente(id_cliente, nombre, cedula, telefono):
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    try:
        c.execute("UPDATE clientes SET nombre = ?, cedula = ?, telefono = ? WHERE id = ?", 
                 (nombre, cedula, telefono, id_cliente))
        conn.commit()
        exito = True
        mensaje = "Cliente actualizado exitosamente"
    except sqlite3.IntegrityError:
        exito = False
        mensaje = "Error: La cédula ya existe en la base de datos"
    conn.close()
    return exito, mensaje

def eliminar_cliente(id_cliente):
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    c.execute("DELETE FROM clientes WHERE id = ?", (id_cliente,))
    conn.commit()
    conn.close()

# Funciones para gestión de préstamos
def crear_prestamo(cliente_id, monto, fecha_prestamo, fecha_vencimiento, tasa_interes=None):
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO prestamos (cliente_id, monto, fecha_prestamo, fecha_vencimiento, tasa_interes) VALUES (?, ?, ?, ?, ?)", 
                 (cliente_id, monto, fecha_prestamo, fecha_vencimiento, tasa_interes))
        conn.commit()
        exito = True
        mensaje = "Préstamo registrado exitosamente"
    except Exception as e:
        exito = False
        mensaje = f"Error al registrar el préstamo: {str(e)}"
    conn.close()
    return exito, mensaje

def obtener_prestamos():
    conn = sqlite3.connect('prestamos.db')
    query = """
    SELECT p.id, c.nombre, c.cedula, p.monto, p.fecha_prestamo, p.fecha_vencimiento, 
           p.tasa_interes, p.estado, p.cliente_id
    FROM prestamos p
    JOIN clientes c ON p.cliente_id = c.id
    """
    prestamos = pd.read_sql_query(query, conn)
    conn.close()
    return prestamos

def obtener_prestamos_cliente(cliente_id):
    conn = sqlite3.connect('prestamos.db')
    query = """
    SELECT p.id, c.nombre, c.cedula, p.monto, p.fecha_prestamo, p.fecha_vencimiento, 
           p.tasa_interes, p.estado
    FROM prestamos p
    JOIN clientes c ON p.cliente_id = c.id
    WHERE p.cliente_id = ?
    """
    prestamos = pd.read_sql_query(query, conn, params=(cliente_id,))
    conn.close()
    return prestamos

def obtener_prestamo(id_prestamo):
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    c.execute("""
    SELECT p.id, p.cliente_id, c.nombre, p.monto, p.fecha_prestamo, p.fecha_vencimiento, 
           p.tasa_interes, p.estado
    FROM prestamos p
    JOIN clientes c ON p.cliente_id = c.id
    WHERE p.id = ?
    """, (id_prestamo,))
    prestamo = c.fetchone()
    conn.close()
    return prestamo

def actualizar_estado_prestamo(id_prestamo, estado):
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    c.execute("UPDATE prestamos SET estado = ? WHERE id = ?", (estado, id_prestamo))
    conn.commit()
    conn.close()

def actualizar_estados_prestamos():
    # Actualiza el estado de los préstamos según la fecha actual
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    
    # Marcar préstamos como atrasados si la fecha de vencimiento ha pasado
    c.execute("""
    UPDATE prestamos 
    SET estado = 'Atrasado' 
    WHERE fecha_vencimiento < ? AND estado = 'Pendiente'
    """, (fecha_actual,))
    
    conn.commit()
    conn.close()
    
# Función para editar un préstamo
def editar_prestamo(id_prestamo, monto, fecha_prestamo, fecha_vencimiento, tasa_interes, estado):
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    try:
        c.execute("""
        UPDATE prestamos 
        SET monto = ?, fecha_prestamo = ?, fecha_vencimiento = ?, tasa_interes = ?, estado = ? 
        WHERE id = ?
        """, (monto, fecha_prestamo, fecha_vencimiento, tasa_interes, estado, id_prestamo))
        conn.commit()
        exito = True
        mensaje = "Préstamo actualizado exitosamente"
    except Exception as e:
        exito = False
        mensaje = f"Error al actualizar el préstamo: {str(e)}"
    conn.close()
    return exito, mensaje

# Función para eliminar un préstamo
def eliminar_prestamo(id_prestamo):
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    try:
        # Primero eliminar los pagos asociados al préstamo
        c.execute("DELETE FROM pagos WHERE prestamo_id = ?", (id_prestamo,))
        
        # Luego eliminar el préstamo
        c.execute("DELETE FROM prestamos WHERE id = ?", (id_prestamo,))
        
        conn.commit()
        exito = True
        mensaje = "Préstamo eliminado exitosamente"
    except Exception as e:
        exito = False
        mensaje = f"Error al eliminar el préstamo: {str(e)}"
    conn.close()
    return exito, mensaje

# Obtiene distribución de préstamos por cliente (top 10)
def obtener_top_clientes():
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT c.nombre, COUNT(p.id) as num_prestamos, SUM(p.monto) as monto_total
        FROM prestamos p
        JOIN clientes c ON p.cliente_id = c.id
        GROUP BY p.cliente_id
        ORDER BY monto_total DESC
        LIMIT 10
    """)
    
    resultados = c.fetchall()
    conn.close()
    
    if not resultados:
        return pd.DataFrame(columns=['nombre', 'num_prestamos', 'monto_total'])
    
    return pd.DataFrame(resultados, columns=['nombre', 'num_prestamos', 'monto_total'])

# Funciones para calculadora de préstamos
def calcular_plan_pagos(monto, tasa_interes, plazo_meses, fecha_inicio=None):
    """
    Calcula un plan de pagos para un préstamo.
    
    Args:
        monto: Monto del préstamo
        tasa_interes: Tasa de interés anual (en porcentaje)
        plazo_meses: Plazo en meses
        fecha_inicio: Fecha de inicio del préstamo (opcional)
    
    Returns:
        DataFrame con el plan de pagos
    """
    if fecha_inicio is None:
        fecha_inicio = datetime.now()
    elif isinstance(fecha_inicio, str):
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    
    # Convertir tasa anual a mensual
    tasa_mensual = tasa_interes / 100 / 12
    
    # Calcular cuota mensual (fórmula de amortización francesa)
    if tasa_mensual > 0:
        cuota_mensual = monto * (tasa_mensual * (1 + tasa_mensual) ** plazo_meses) / ((1 + tasa_mensual) ** plazo_meses - 1)
    else:
        cuota_mensual = monto / plazo_meses
    
    # Generar plan de pagos
    plan = []
    saldo = monto
    
    for mes in range(1, plazo_meses + 1):
        # Calcular fecha de pago
        fecha_pago = fecha_inicio + timedelta(days=30 * mes)
        
        # Calcular interés del periodo
        interes = saldo * tasa_mensual
        
        # Calcular amortización
        amortizacion = cuota_mensual - interes
        
        # Actualizar saldo
        nuevo_saldo = saldo - amortizacion
        
        # Ajuste para el último pago (por redondeos)
        if mes == plazo_meses:
            amortizacion = saldo
            cuota_mensual = amortizacion + interes
            nuevo_saldo = 0
        
        # Agregar al plan
        plan.append({
            'num_pago': mes,
            'fecha_pago': fecha_pago.strftime('%Y-%m-%d'),
            'cuota': cuota_mensual,
            'capital': amortizacion,
            'interes': interes,
            'saldo': nuevo_saldo
        })
        
        # Actualizar saldo para el siguiente mes
        saldo = nuevo_saldo
    
    return pd.DataFrame(plan)

# Funciones para dashboard
def obtener_datos_tendencias(meses=6):
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    
    # Fecha actual
    fecha_actual = datetime.now()
    
    # Obtener datos de los últimos X meses
    datos_meses = []
    
    for i in range(meses, 0, -1):
        # Calcular el primer y último día del mes
        fecha_mes = fecha_actual - timedelta(days=30*i)
        primer_dia = datetime(fecha_mes.year, fecha_mes.month, 1).strftime('%Y-%m-%d')
        
        if fecha_mes.month == 12:
            ultimo_dia = datetime(fecha_mes.year + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = datetime(fecha_mes.year, fecha_mes.month + 1, 1) - timedelta(days=1)
        ultimo_dia = ultimo_dia.strftime('%Y-%m-%d')
        
        # Nombre del mes para mostrar
        nombre_mes = fecha_mes.strftime('%b %Y')
        
        # Contar préstamos creados en ese mes
        c.execute("""
            SELECT COUNT(*), SUM(monto) 
            FROM prestamos 
            WHERE fecha_prestamo BETWEEN ? AND ?
        """, (primer_dia, ultimo_dia))
        prestamos_creados = c.fetchone()
        num_prestamos = prestamos_creados[0] if prestamos_creados[0] else 0
        monto_prestamos = prestamos_creados[1] if prestamos_creados[1] else 0
        
        # Contar pagos realizados en ese mes
        c.execute("""
            SELECT COUNT(*), SUM(monto_pagado) 
            FROM pagos 
            WHERE fecha_pago BETWEEN ? AND ?
        """, (primer_dia, ultimo_dia))
        pagos_realizados = c.fetchone()
        num_pagos = pagos_realizados[0] if pagos_realizados[0] else 0
        monto_pagos = pagos_realizados[1] if pagos_realizados[1] else 0
        
        # Contar préstamos morosos al final del mes
        c.execute("""
            SELECT COUNT(*) 
            FROM prestamos 
            WHERE estado = 'Atrasado' AND fecha_vencimiento <= ?
        """, (ultimo_dia,))
        morosos = c.fetchone()
        num_morosos = morosos[0] if morosos[0] else 0
        
        datos_meses.append({
            'mes': nombre_mes,
            'num_prestamos': num_prestamos,
            'monto_prestamos': monto_prestamos,
            'num_pagos': num_pagos,
            'monto_pagos': monto_pagos,
            'num_morosos': num_morosos
        })
    
    conn.close()
    return pd.DataFrame(datos_meses)

def obtener_distribucion_estados():
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT estado, COUNT(*) as cantidad, SUM(monto) as monto_total
        FROM prestamos
        GROUP BY estado
    """)
    
    resultados = c.fetchall()
    conn.close()
    
    if not resultados:
        return pd.DataFrame(columns=['estado', 'cantidad', 'monto_total'])
    
    return pd.DataFrame(resultados, columns=['estado', 'cantidad', 'monto_total'])

# Calcular estadísticas generales para el dashboard
def calcular_estadisticas_prestamos():
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    
    # Total de préstamos y monto total
    c.execute("""
        SELECT COUNT(*), SUM(monto) 
        FROM prestamos
    """)
    resultado = c.fetchone()
    total_prestamos = resultado[0] if resultado[0] else 0
    monto_total = resultado[1] if resultado[1] else 0
    
    # Total de préstamos pendientes y atrasados y su monto
    c.execute("""
        SELECT SUM(monto) 
        FROM prestamos 
        WHERE estado IN ('Pendiente', 'Atrasado')
    """)
    resultado = c.fetchone()
    monto_pendiente = resultado[0] if resultado[0] else 0
    
    # Total de préstamos morosos
    c.execute("""
        SELECT COUNT(*) 
        FROM prestamos 
        WHERE estado = 'Atrasado'
    """)
    resultado = c.fetchone()
    total_morosos = resultado[0] if resultado[0] else 0
    
    # Total de pagos realizados
    c.execute("""
        SELECT COUNT(*), SUM(monto_pagado) 
        FROM pagos
    """)
    resultado = c.fetchone()
    total_pagos = resultado[0] if resultado[0] else 0
    monto_pagado = resultado[1] if resultado[1] else 0
    
    conn.close()
    
    return {
        'total_prestamos': total_prestamos,
        'monto_total': monto_total,
        'monto_pendiente': monto_pendiente,
        'total_morosos': total_morosos,
        'total_pagos': total_pagos,
        'monto_pagado': monto_pagado
    }

# Funciones para reportes
def obtener_prestamos_activos():
    """Obtiene todos los préstamos activos (pendientes o atrasados)"""
    conn = sqlite3.connect('prestamos.db')
    query = """
    SELECT p.id, c.nombre, c.cedula, p.monto, p.fecha_prestamo, p.fecha_vencimiento, 
           p.tasa_interes, p.estado, c.id as cliente_id
    FROM prestamos p
    JOIN clientes c ON p.cliente_id = c.id
    WHERE p.estado != 'Pagado'
    ORDER BY p.fecha_vencimiento ASC
    """
    prestamos = pd.read_sql_query(query, conn)
    conn.close()
    return prestamos

def obtener_prestamos_morosos():
    """Obtiene todos los préstamos morosos (atrasados)"""
    conn = sqlite3.connect('prestamos.db')
    query = """
    SELECT p.id, c.nombre, c.cedula, p.monto, p.fecha_prestamo, p.fecha_vencimiento, 
           p.tasa_interes, p.estado, c.id as cliente_id
    FROM prestamos p
    JOIN clientes c ON p.cliente_id = c.id
    WHERE p.estado = 'Atrasado'
    ORDER BY p.fecha_vencimiento ASC
    """
    prestamos = pd.read_sql_query(query, conn)
    conn.close()
    return prestamos

def calcular_estadisticas_prestamos():
    """Calcula estadísticas generales de los préstamos"""
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    
    # Total de préstamos
    c.execute("SELECT COUNT(*) FROM prestamos")
    total_prestamos = c.fetchone()[0]
    
    # Total de préstamos activos
    c.execute("SELECT COUNT(*) FROM prestamos WHERE estado != 'Pagado'")
    total_activos = c.fetchone()[0]
    
    # Total de préstamos morosos
    c.execute("SELECT COUNT(*) FROM prestamos WHERE estado = 'Atrasado'")
    total_morosos = c.fetchone()[0]
    
    # Monto total prestado
    c.execute("SELECT SUM(monto) FROM prestamos")
    monto_total = c.fetchone()[0] or 0
    
    # Monto total pendiente
    monto_pendiente = 0
    c.execute("SELECT id FROM prestamos WHERE estado != 'Pagado'")
    prestamos_activos = c.fetchall()
    for prestamo in prestamos_activos:
        monto_pendiente += calcular_saldo_pendiente(prestamo[0])
    
    conn.close()
    
    return {
        "total_prestamos": total_prestamos,
        "total_activos": total_activos,
        "total_morosos": total_morosos,
        "monto_total": monto_total,
        "monto_pendiente": monto_pendiente
    }

# Funciones para gestión de pagos
def registrar_pago(prestamo_id, fecha_pago, monto_pagado):
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO pagos (prestamo_id, fecha_pago, monto_pagado) VALUES (?, ?, ?)", 
                 (prestamo_id, fecha_pago, monto_pagado))
        conn.commit()
        
        # Actualizar estado del préstamo si ya se pagó completamente
        saldo_pendiente = calcular_saldo_pendiente(prestamo_id)
        if saldo_pendiente <= 0:
            c.execute("UPDATE prestamos SET estado = 'Pagado' WHERE id = ?", (prestamo_id,))
            conn.commit()
        
        exito = True
        mensaje = "Pago registrado exitosamente"
    except Exception as e:
        exito = False
        mensaje = f"Error al registrar el pago: {str(e)}"
    conn.close()
    return exito, mensaje

def obtener_pagos(prestamo_id):
    conn = sqlite3.connect('prestamos.db')
    query = """
    SELECT id, prestamo_id, fecha_pago, monto_pagado
    FROM pagos
    WHERE prestamo_id = ?
    ORDER BY fecha_pago DESC
    """
    pagos = pd.read_sql_query(query, conn, params=(prestamo_id,))
    conn.close()
    return pagos

def calcular_saldo_pendiente(prestamo_id):
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    
    # Obtener monto total del préstamo
    c.execute("SELECT monto, tasa_interes FROM prestamos WHERE id = ?", (prestamo_id,))
    prestamo = c.fetchone()
    if not prestamo:
        conn.close()
        return 0
    
    monto_prestamo = float(prestamo[0])
    tasa_interes = float(prestamo[1] or 0)
    
    # Calcular monto total a pagar (incluyendo interés)
    monto_total = monto_prestamo * (1 + tasa_interes / 100)
    
    # Obtener suma de pagos realizados
    c.execute("SELECT SUM(monto_pagado) FROM pagos WHERE prestamo_id = ?", (prestamo_id,))
    total_pagado = float(c.fetchone()[0] or 0)
    
    # Calcular saldo pendiente
    saldo_pendiente = monto_total - total_pagado
    
    conn.close()
    return max(0, round(saldo_pendiente, 2))  # No permitir saldos negativos y redondear a 2 decimales

def eliminar_pago(pago_id):
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    
    # Obtener el préstamo_id antes de eliminar el pago
    c.execute("SELECT prestamo_id FROM pagos WHERE id = ?", (pago_id,))
    resultado = c.fetchone()
    if not resultado:
        conn.close()
        return False, "Pago no encontrado"
    
    prestamo_id = resultado[0]
    
    try:
        c.execute("DELETE FROM pagos WHERE id = ?", (pago_id,))
        conn.commit()
        
        # Actualizar estado del préstamo después de eliminar el pago
        saldo_pendiente = calcular_saldo_pendiente(prestamo_id)
        if saldo_pendiente > 0:
            # Verificar si la fecha de vencimiento ha pasado
            fecha_actual = datetime.now().strftime('%Y-%m-%d')
            c.execute("SELECT fecha_vencimiento FROM prestamos WHERE id = ?", (prestamo_id,))
            fecha_vencimiento = c.fetchone()[0]
            
            if fecha_vencimiento < fecha_actual:
                nuevo_estado = "Atrasado"
            else:
                nuevo_estado = "Pendiente"
                
            c.execute("UPDATE prestamos SET estado = ? WHERE id = ?",(nuevo_estado, prestamo_id))
            conn.commit()
        
        exito = True
        mensaje = "Pago eliminado correctamente"
        
        # Registrar la actividad
        registrar_actividad(st.session_state.usuario, "eliminar_pago", {"pago_id": pago_id, "prestamo_id": prestamo_id})
    except Exception as e:
        exito = False
        mensaje = f"Error al eliminar el pago: {str(e)}"
    finally:
        conn.close()
        
    return exito, mensaje

# Funciones de exportación avanzada
def exportar_a_excel(df, filename):
    """Exporta un DataFrame a un archivo Excel con formato mejorado"""
    output = io.BytesIO()
    workbook = Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Datos')
    
    # Agregar formatos
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#0066cc',
        'font_color': 'white',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'border': 1
    })
    
    money_format = workbook.add_format({
        'border': 1,
        'num_format': '$#,##0.00'
    })
    
    date_format = workbook.add_format({
        'border': 1,
        'num_format': 'dd/mm/yyyy'
    })
    
    # Escribir encabezados
    for col_num, column in enumerate(df.columns):
        worksheet.write(0, col_num, column, header_format)
    
    # Escribir datos
    for row_num, row in enumerate(df.values):
        for col_num, cell_value in enumerate(row):
            # Detectar si es un valor monetario (si contiene $)
            if isinstance(cell_value, str) and '$' in cell_value:
                # Extraer el valor numérico
                try:
                    numeric_value = float(cell_value.replace('$', '').replace(',', ''))
                    worksheet.write(row_num + 1, col_num, numeric_value, money_format)
                except ValueError:
                    worksheet.write(row_num + 1, col_num, cell_value, cell_format)
            # Detectar si es una fecha
            elif isinstance(cell_value, str) and len(cell_value.split('/')) == 3:
                try:
                    # Intentar convertir a fecha
                    parts = cell_value.split('/')
                    if len(parts[2]) == 4:  # Formato dd/mm/yyyy
                        worksheet.write(row_num + 1, col_num, cell_value, date_format)
                    else:
                        worksheet.write(row_num + 1, col_num, cell_value, cell_format)
                except:
                    worksheet.write(row_num + 1, col_num, cell_value, cell_format)
            else:
                worksheet.write(row_num + 1, col_num, cell_value, cell_format)
    
    # Ajustar ancho de columnas
    for col_num, column in enumerate(df.columns):
        max_length = max(df[column].astype(str).apply(len).max(), len(column))
        worksheet.set_column(col_num, col_num, max_length + 2)
    
    # Agregar filtros
    worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
    
    # Agregar información del sistema
    info_sheet = workbook.add_worksheet('Información')
    info_sheet.write(0, 0, 'Reporte generado desde Sistema de Préstamos')
    info_sheet.write(1, 0, f'Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
    if 'usuario' in st.session_state:
        info_sheet.write(2, 0, f'Usuario: {st.session_state.usuario}')
    
    workbook.close()
    output.seek(0)
    
    return output.getvalue()

def exportar_a_pdf(df, titulo):
    """Exporta un DataFrame a un archivo PDF con formato mejorado"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']
    
    # Título
    elements.append(Paragraph(titulo, title_style))
    elements.append(Spacer(1, 12))
    
    # Información del reporte
    elements.append(Paragraph(f"Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
    if 'usuario' in st.session_state:
        elements.append(Paragraph(f"Usuario: {st.session_state.usuario}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Convertir DataFrame a lista para la tabla
    data = [df.columns.tolist()] + df.values.tolist()
    
    # Crear tabla
    table = Table(data)
    
    # Estilo de tabla
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    
    # Aplicar estilo a filas alternas para mejor legibilidad
    for i in range(1, len(data)):
        if i % 2 == 0:
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer.getvalue()

def mostrar_opciones_exportacion(df, nombre_reporte):
    """Muestra un expander con opciones para exportar datos en diferentes formatos"""
    with st.expander("Opciones de Exportación"):
        st.write("Exportar datos en diferentes formatos:")
        
        col1, col2, col3 = st.columns(3)
        
        # Exportar a CSV
        with col1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 Exportar a CSV",
                data=csv,
                file_name=f"{nombre_reporte}.csv",
                mime="text/csv",
                help="Exportar datos en formato CSV para usar en Excel u otras aplicaciones"
            )
        
        # Exportar a Excel
        with col2:
            excel_data = exportar_a_excel(df, nombre_reporte)
            st.download_button(
                label="📊 Exportar a Excel",
                data=excel_data,
                file_name=f"{nombre_reporte}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Exportar datos en formato Excel con formato mejorado"
            )
        
        # Exportar a PDF
        with col3:
            pdf_data = exportar_a_pdf(df, f"Reporte: {nombre_reporte}")
            st.download_button(
                label="📑 Exportar a PDF",
                data=pdf_data,
                file_name=f"{nombre_reporte}.pdf",
                mime="application/pdf",
                help="Exportar datos en formato PDF para imprimir o compartir"
            )

# Interfaz de usuario
def main():
    # Inicializar variables de sesión si no existen
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'nivel_acceso' not in st.session_state:
        st.session_state.nivel_acceso = None
    if 'menu' not in st.session_state:
        st.session_state.menu = "Dashboard"
    
    # Actualizar estados de préstamos
    actualizar_estados_prestamos()
    
    # Mostrar título
    st.title("Sistema de Préstamos")
    
    # Verificar si el usuario está autenticado
    if not st.session_state.autenticado:
        st.subheader("Iniciar Sesión")
        
        # Espacio para mejor presentación
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Formulario de login
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            contrasena = st.text_input("Contraseña", type="password")
            submit_button = st.form_submit_button("Iniciar Sesión")
            
            if submit_button:
                exito, nivel_acceso, mensaje = autenticar(usuario, contrasena)
                if exito:
                    st.session_state.autenticado = True
                    st.session_state.usuario = usuario
                    st.session_state.nivel_acceso = nivel_acceso
                    st.session_state.menu = "Dashboard"
                    st.rerun()
                else:
                    st.error(mensaje)
    else:
        # Mostrar menú y contenido para usuarios autenticados
        st.sidebar.title("Sistema de Préstamos")
        
        # Mostrar información del usuario
        nivel = st.session_state.nivel_acceso.capitalize()
        st.sidebar.success(f"Sesión iniciada como: **{st.session_state.usuario}** | Nivel: **{nivel}**")
        
        # Separador
        st.sidebar.markdown("---")
        
        # Estilo CSS personalizado para hacer los botones más grandes
        st.markdown("""
        <style>
        div.stButton > button {
            width: 100%;
            height: 60px;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            border-radius: 10px;
        }
        div.row-widget.stRadio > div {
            flex-direction: column;
            gap: 10px;
        }
        div.row-widget.stRadio > div[role="radiogroup"] > label {
            padding: 15px;
            background-color: #f0f2f6;
            border-radius: 10px;
            text-align: center;
            font-size: 16px;
            font-weight: 500;
        }
        div.row-widget.stRadio > div[role="radiogroup"] > label:hover {
            background-color: #e0e2e6;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Menú con botones en lugar de radio
        st.sidebar.markdown("### Navegación Principal")
        
        # Usar botones para la navegación en lugar de radio buttons
        menu_options = ["Dashboard", "Gestión de Clientes", "Gestión de Préstamos", "Gestión de Pagos", "Reportes", "Calculadora"]
        
        # Crear botones para cada opción del menú
        col1_sidebar, col2_sidebar = st.sidebar.columns(2)
        
        with col1_sidebar:
            if st.button("📊 Dashboard", help="Panel principal", use_container_width=True):
                st.session_state.menu = "Dashboard"
                st.rerun()
                
        with col2_sidebar:
            if st.button("📈 Calculadora", help="Simulador de préstamos", use_container_width=True):
                st.session_state.menu = "Calculadora"
                st.rerun()
            
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("👤 Clientes", help="Administrar clientes", use_container_width=True):
                st.session_state.menu = "Gestión de Clientes"
                st.rerun()
                
            if st.button("💰 Pagos", help="Gestionar pagos", use_container_width=True):
                st.session_state.menu = "Gestión de Pagos"
                st.rerun()
                
            # Opción solo para administradores
            if st.session_state.nivel_acceso == "administrador":
                if st.button("🔐 Seguridad", help="Gestión de usuarios y auditoría", use_container_width=True):
                    st.session_state.menu = "Seguridad"
                    st.rerun()
                
        with col2:
            if st.button("💵 Préstamos", help="Administrar préstamos", use_container_width=True):
                st.session_state.menu = "Gestión de Préstamos"
                st.rerun()
                
            if st.button("📊 Reportes", help="Ver reportes", use_container_width=True):
                st.session_state.menu = "Reportes"
                st.rerun()
        
        # Mostrar la opción seleccionada actualmente
        st.sidebar.info(f"Sección actual: **{st.session_state.menu}**")
        
        # Separador
        st.sidebar.markdown("---")
        
        # Botón para cerrar sesión
        if st.sidebar.button("🔒 Cerrar Sesión", type="primary"):
            cerrar_sesion()
            st.rerun()
        
        # Usar st.session_state.menu en lugar de la variable menu
        current_menu = st.session_state.menu
        
        # Dashboard Principal
        if current_menu == "Dashboard":
            st.header("📊 Dashboard del Sistema de Préstamos")
            
            # Obtener estadísticas generales
            stats = calcular_estadisticas_prestamos()
            
            # Mostrar métricas principales en tarjetas
            st.subheader("Resumen General")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Total Préstamos", 
                    value=f"{stats['total_prestamos']}",
                    help="Número total de préstamos en el sistema"
                )
            with col2:
                st.metric(
                    label="Monto Total Prestado", 
                    value=f"${stats['monto_total']:,.2f}",
                    help="Suma de todos los montos prestados"
                )
            with col3:
                st.metric(
                    label="Monto Pendiente", 
                    value=f"${stats['monto_pendiente']:,.2f}",
                    delta=f"-${stats['monto_total'] - stats['monto_pendiente']:,.2f}",
                    help="Monto total aún por cobrar"
                )
            with col4:
                indice_morosidad = (stats['total_morosos'] / stats['total_prestamos'] * 100) if stats['total_prestamos'] > 0 else 0
                st.metric(
                    label="Índice de Morosidad", 
                    value=f"{indice_morosidad:.1f}%",
                    delta=f"{stats['total_morosos']} préstamos",
                    delta_color="inverse",
                    help="Porcentaje de préstamos en estado moroso"
                )
            
            # Separador
            st.markdown("---")
            
            # Tendencias de los últimos meses
            st.subheader("Tendencias de los últimos 6 meses")
            
            try:
                # Obtener datos de tendencias
                datos_tendencias = obtener_datos_tendencias()
                
                if not datos_tendencias.empty:
                    # Crear pestañas para diferentes gráficos
                    tab1, tab2, tab3 = st.tabs(["Préstamos Otorgados", "Pagos Recibidos", "Morosidad"])
                    
                    # Pestaña 1: Préstamos Otorgados
                    with tab1:
                        # Gráfico de tendencia de préstamos otorgados
                        fig = px.bar(
                            datos_tendencias,
                            x="mes",
                            y="monto_prestamos",
                            title="Monto de Préstamos Otorgados por Mes",
                            labels={"mes": "Mes", "monto_prestamos": "Monto ($)"},
                            text_auto=True
                        )
                        fig.update_traces(texttemplate='$%{y:,.2f}', textposition='outside')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Gráfico de cantidad de préstamos
                        fig2 = px.line(
                            datos_tendencias,
                            x="mes",
                            y="num_prestamos",
                            title="Cantidad de Préstamos Otorgados por Mes",
                            labels={"mes": "Mes", "num_prestamos": "Cantidad"},
                            markers=True
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                    
                    # Pestaña 2: Pagos Recibidos
                    with tab2:
                        # Gráfico de tendencia de pagos recibidos
                        fig = px.bar(
                            datos_tendencias,
                            x="mes",
                            y="monto_pagos",
                            title="Monto de Pagos Recibidos por Mes",
                            labels={"mes": "Mes", "monto_pagos": "Monto ($)"},
                            text_auto=True,
                            color_discrete_sequence=['#2ecc71']
                        )
                        fig.update_traces(texttemplate='$%{y:,.2f}', textposition='outside')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Gráfico de cantidad de pagos
                        fig2 = px.line(
                            datos_tendencias,
                            x="mes",
                            y="num_pagos",
                            title="Cantidad de Pagos Recibidos por Mes",
                            labels={"mes": "Mes", "num_pagos": "Cantidad"},
                            markers=True,
                            color_discrete_sequence=['#2ecc71']
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                    
                    # Pestaña 3: Morosidad
                    with tab3:
                        # Gráfico de tendencia de morosidad
                        fig = px.line(
                            datos_tendencias,
                            x="mes",
                            y="num_morosos",
                            title="Evolución de Préstamos Morosos",
                            labels={"mes": "Mes", "num_morosos": "Cantidad"},
                            markers=True,
                            color_discrete_sequence=['#e74c3c']
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay suficientes datos para mostrar tendencias. Registre préstamos y pagos para ver estadísticas.")
            except Exception as e:
                st.error(f"Error al cargar los gráficos de tendencias: {str(e)}")
            
            # Separador
            st.markdown("---")
            
            # Distribución de préstamos por estado y clientes
            st.subheader("Distribución de Préstamos")
            
            col1, col2 = st.columns(2)
            
            with col1:
                try:
                    # Obtener distribución por estado
                    distribucion_estados = obtener_distribucion_estados()
                    
                    if not distribucion_estados.empty:
                        # Asignar colores según estado
                        colores = {'Pendiente': '#3498db', 'Pagado': '#2ecc71', 'Atrasado': '#e74c3c'}
                        colores_lista = [colores.get(estado, '#95a5a6') for estado in distribucion_estados['estado']]
                        
                        # Gráfico de torta para distribución por estado
                        fig = px.pie(
                            distribucion_estados,
                            values="cantidad",
                            names="estado",
                            title="Distribución de Préstamos por Estado",
                            color="estado",
                            color_discrete_map=colores
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No hay datos suficientes para mostrar la distribución por estado.")
                except Exception as e:
                    st.error(f"Error al cargar el gráfico de distribución por estado: {str(e)}")
            
            with col2:
                try:
                    # Obtener top clientes
                    top_clientes = obtener_top_clientes()
                    
                    if not top_clientes.empty and len(top_clientes) > 0:
                        # Gráfico de barras horizontales para top clientes
                        fig = px.bar(
                            top_clientes,
                            y="nombre",
                            x="monto_total",
                            title="Top Clientes por Monto Prestado",
                            labels={"nombre": "Cliente", "monto_total": "Monto Total ($)"},
                            text_auto=True,
                            orientation='h',
                            color_discrete_sequence=['#9b59b6']
                        )
                        fig.update_traces(texttemplate='$%{x:,.2f}', textposition='outside')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No hay suficientes datos de clientes para mostrar estadísticas.")
                except Exception as e:
                    st.error(f"Error al cargar el gráfico de top clientes: {str(e)}")
            
            # Acciones rápidas
            st.markdown("---")
            st.subheader("Acciones Rápidas")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💵 Nuevo Préstamo", use_container_width=True):
                    st.session_state.menu = "Gestión de Préstamos"
                    st.rerun()
            with col2:
                if st.button("💰 Registrar Pago", use_container_width=True):
                    st.session_state.menu = "Gestión de Pagos"
                    st.rerun()
            with col3:
                if st.button("📈 Ver Reportes Detallados", use_container_width=True):
                    st.session_state.menu = "Reportes"
                    st.rerun()
        
        # Calculadora de Préstamos
        elif current_menu == "Calculadora":
            st.header("📈 Calculadora de Préstamos")
            st.write("Simula diferentes escenarios de préstamos y visualiza el plan de pagos proyectado.")
            
            # Formulario para la simulación
            with st.form(key="calculadora_form"):
                st.subheader("Parámetros del Préstamo")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    monto = st.number_input("Monto del Préstamo ($)", min_value=100.0, value=5000.0, step=100.0)
                    tasa_interes = st.number_input("Tasa de Interés Anual (%)", min_value=0.0, max_value=100.0, value=12.0, step=0.5)
                
                with col2:
                    plazo_meses = st.number_input("Plazo (meses)", min_value=1, max_value=120, value=12, step=1)
                    fecha_inicio = st.date_input("Fecha de Inicio", value=datetime.now())
                
                submitted = st.form_submit_button("Calcular", use_container_width=True)
            
            if submitted or 'plan_pagos' in st.session_state:
                # Si es la primera vez, calcular el plan de pagos
                if submitted or 'plan_pagos' not in st.session_state:
                    plan_pagos = calcular_plan_pagos(monto, tasa_interes, plazo_meses, fecha_inicio)
                    st.session_state.plan_pagos = plan_pagos
                    st.session_state.parametros = {
                        'monto': monto,
                        'tasa_interes': tasa_interes,
                        'plazo_meses': plazo_meses,
                        'fecha_inicio': fecha_inicio
                    }
                else:
                    plan_pagos = st.session_state.plan_pagos
                    parametros = st.session_state.parametros
                
                # Mostrar resumen
                st.subheader("Resumen del Préstamo")
                col1, col2, col3 = st.columns(3)
                
                # Calcular totales
                total_pagos = plan_pagos['cuota'].sum()
                total_intereses = plan_pagos['interes'].sum()
                cuota_mensual = plan_pagos['cuota'].iloc[0]
                
                with col1:
                    st.metric("Monto Total a Pagar", f"${total_pagos:,.2f}")
                
                with col2:
                    st.metric("Total Intereses", f"${total_intereses:,.2f}")
                
                with col3:
                    st.metric("Cuota Mensual", f"${cuota_mensual:,.2f}")
                
                # Mostrar gráfico de distribución
                st.subheader("Distribución del Préstamo")
                
                # Datos para el gráfico
                datos_grafico = [
                    {'categoria': 'Capital', 'valor': monto},
                    {'categoria': 'Intereses', 'valor': total_intereses}
                ]
                df_grafico = pd.DataFrame(datos_grafico)
                
                # Crear gráfico
                fig = px.pie(
                    df_grafico, 
                    values='valor', 
                    names='categoria',
                    title="Distribución Capital vs. Intereses",
                    color='categoria',
                    color_discrete_map={'Capital': '#3498db', 'Intereses': '#e74c3c'}
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
                
                # Mostrar plan de pagos con mejor experiencia de usuario
                st.subheader("📋 Plan de Pagos Proyectado")
                
                # Crear pestañas para diferentes vistas del plan de pagos
                tab_resumen, tab_detalle, tab_grafico = st.tabs(["✅ Resumen", "📊 Detalle de Pagos", "📈 Evolución de Pagos"])
                
                # Formatear la tabla
                plan_pagos_display = plan_pagos.copy()
                
                # Calcular totales para el resumen
                total_capital = plan_pagos['capital'].sum()
                total_interes = plan_pagos['interes'].sum()
                total_pagos = total_capital + total_interes
                
                # Pestaña de resumen
                with tab_resumen:
                    st.write("### Resumen del Plan de Pagos")
                    
                    # Información clave del préstamo
                    st.info(f"💡 **Información del préstamo:** Monto de ${monto:,.2f} a {plazo_meses} meses con tasa de interés del {tasa_interes}% anual")
                    
                    # Mostrar métricas clave
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Primera cuota", plan_pagos_display['cuota'].iloc[0])
                        st.metric("Fecha primera cuota", pd.to_datetime(plan_pagos['fecha_pago'].iloc[0]).strftime('%d/%m/%Y'))
                    with col2:
                        st.metric("Última cuota", plan_pagos_display['cuota'].iloc[-1])
                        st.metric("Fecha última cuota", pd.to_datetime(plan_pagos['fecha_pago'].iloc[-1]).strftime('%d/%m/%Y'))
                    with col3:
                        st.metric("Total a pagar", f"${total_pagos:,.2f}")
                        st.metric("Total intereses", f"${total_interes:,.2f}", delta=f"{total_interes/monto*100:.1f}%")
                    
                    # Mostrar progresión de pagos en un gráfico simplificado
                    st.write("### Progresión de Pagos")
                    
                    # Crear datos para gráfico de barras apiladas
                    hitos = [0, int(plazo_meses/4), int(plazo_meses/2), int(3*plazo_meses/4), plazo_meses-1]
                    hitos = [i for i in hitos if i < len(plan_pagos)]
                    if hitos[-1] != len(plan_pagos)-1:
                        hitos.append(len(plan_pagos)-1)
                    
                    hitos_df = plan_pagos.iloc[hitos].copy()
                    hitos_df['num_pago'] = hitos_df['num_pago'].astype(str)
                    
                    # Gráfico de barras apiladas para mostrar la evolución
                    fig = px.bar(hitos_df, x='num_pago', y=['capital', 'interes'], 
                                 title="Composición de las cuotas a lo largo del préstamo",
                                 labels={'value': 'Monto ($)', 'num_pago': 'Número de cuota', 'variable': 'Componente'},
                                 color_discrete_map={'capital': '#3498db', 'interes': '#e74c3c'})
                    fig.update_layout(legend_title_text='')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Pestaña de detalle
                with tab_detalle:
                    # Formatear para visualización
                    plan_pagos_display['cuota'] = plan_pagos_display['cuota'].map('${:,.2f}'.format)
                    plan_pagos_display['capital'] = plan_pagos_display['capital'].map('${:,.2f}'.format)
                    plan_pagos_display['interes'] = plan_pagos_display['interes'].map('${:,.2f}'.format)
                    plan_pagos_display['saldo'] = plan_pagos_display['saldo'].map('${:,.2f}'.format)
                    
                    # Formatear fechas
                    plan_pagos_display['fecha_pago'] = pd.to_datetime(plan_pagos_display['fecha_pago']).dt.strftime('%d/%m/%Y')
                    
                    # Renombrar columnas para mejor visualización
                    plan_pagos_display = plan_pagos_display.rename(columns={
                        'num_pago': 'Nro.',
                        'fecha_pago': 'Fecha de Pago',
                        'cuota': 'Cuota',
                        'capital': 'Capital',
                        'interes': 'Interés',
                        'saldo': 'Saldo'
                    })
                    
                    # Filtros para la tabla
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        # Opciones de visualización
                        mostrar_filas = st.radio(
                            "Mostrar:",
                            ["Todas las cuotas", "Primeras cuotas", "Últimas cuotas", "Cuotas específicas"]
                        )
                    
                    with col2:
                        if mostrar_filas == "Primeras cuotas":
                            num_filas = st.slider("Número de cuotas a mostrar", 1, min(12, len(plan_pagos_display)), 6)
                            filas_a_mostrar = plan_pagos_display.head(num_filas)
                        elif mostrar_filas == "Últimas cuotas":
                            num_filas = st.slider("Número de cuotas a mostrar", 1, min(12, len(plan_pagos_display)), 6)
                            filas_a_mostrar = plan_pagos_display.tail(num_filas)
                        elif mostrar_filas == "Cuotas específicas":
                            rango = st.slider("Rango de cuotas", 1, len(plan_pagos_display), (1, min(12, len(plan_pagos_display))))
                            filas_a_mostrar = plan_pagos_display.iloc[rango[0]-1:rango[1]]
                        else:  # Todas las cuotas
                            if len(plan_pagos_display) > 12:
                                pagina = st.selectbox(
                                    "Página", 
                                    options=range(1, (len(plan_pagos_display) // 12) + 2),
                                    format_func=lambda x: f"Página {x} de {(len(plan_pagos_display) // 12) + 1}"
                                )
                                inicio = (pagina - 1) * 12
                                fin = min(inicio + 12, len(plan_pagos_display))
                                filas_a_mostrar = plan_pagos_display.iloc[inicio:fin]
                            else:
                                filas_a_mostrar = plan_pagos_display
                    
                    # Mostrar tabla con mejor formato
                    st.write("### Detalle de cuotas")
                    st.dataframe(
                        filas_a_mostrar,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Nro.": st.column_config.NumberColumn("#", format="%d"),
                            "Fecha de Pago": st.column_config.DateColumn("Fecha"),
                            "Cuota": st.column_config.TextColumn("Cuota"),
                            "Capital": st.column_config.TextColumn("Capital"),
                            "Interés": st.column_config.TextColumn("Interés"),
                            "Saldo": st.column_config.TextColumn("Saldo Restante")
                        }
                    )
                
                # Pestaña de evolución gráfica
                with tab_grafico:
                    st.write("### Evolución del Préstamo")
                    
                    # Gráfico de evolución del saldo
                    fig1 = px.line(
                        plan_pagos, x='num_pago', y='saldo',
                        title="Evolución del Saldo Pendiente",
                        labels={'num_pago': 'Número de Cuota', 'saldo': 'Saldo Pendiente ($)'},
                        markers=True
                    )
                    fig1.update_traces(line=dict(color='#3498db', width=3))
                    st.plotly_chart(fig1, use_container_width=True)
                    
                    # Gráfico de composición de cuotas
                    st.write("### Composición de las Cuotas")
                    
                    # Preparar datos para el gráfico de área
                    fig2 = px.area(
                        plan_pagos, x='num_pago', y=['capital', 'interes'],
                        title="Composición de Cuotas (Capital vs Interés)",
                        labels={'num_pago': 'Número de Cuota', 'value': 'Monto ($)', 'variable': 'Componente'},
                        color_discrete_map={'capital': '#2ecc71', 'interes': '#e74c3c'}
                    )
                    fig2.update_layout(legend_title_text='')
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Opciones para descargar el plan de pagos en diferentes formatos
                with st.expander("Opciones de Exportación del Plan de Pagos"):
                    st.write("Exportar plan de pagos en diferentes formatos:")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    # Exportar a CSV
                    with col1:
                        csv = plan_pagos_display.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📄 Exportar a CSV",
                            data=csv,
                            file_name="plan_pagos.csv",
                            mime="text/csv",
                            help="Exportar plan de pagos en formato CSV para usar en Excel u otras aplicaciones"
                        )
                    
                    # Exportar a Excel
                    with col2:
                        # Convertir a DataFrame original para mejor formato en Excel
                        plan_pagos_excel = plan_pagos.copy()
                        plan_pagos_excel = plan_pagos_excel.rename(columns={
                            'num_pago': 'Nro.',
                            'fecha_pago': 'Fecha de Pago',
                            'cuota': 'Cuota',
                            'capital': 'Capital',
                            'interes': 'Interés',
                            'saldo': 'Saldo'
                        })
                        excel_data = exportar_a_excel(plan_pagos_excel, "plan_pagos")
                        st.download_button(
                            label="📊 Exportar a Excel",
                            data=excel_data,
                            file_name="plan_pagos.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            help="Exportar plan de pagos en formato Excel con formato mejorado"
                        )
                    
                    # Exportar a PDF
                    with col3:
                        pdf_data = exportar_a_pdf(plan_pagos_display, "Plan de Pagos Proyectado")
                        st.download_button(
                            label="📑 Exportar a PDF",
                            data=pdf_data,
                            file_name="plan_pagos.pdf",
                            mime="application/pdf",
                            help="Exportar plan de pagos en formato PDF para imprimir o compartir"
                        )
                
                # Gráfico de evolución del saldo
                st.subheader("Evolución del Saldo")
                
                # Preparar datos para el gráfico
                fig = px.line(
                    plan_pagos,
                    x='num_pago',
                    y='saldo',
                    title="Evolución del Saldo Pendiente",
                    labels={'num_pago': 'Número de Pago', 'saldo': 'Saldo Pendiente ($)'},
                    markers=True
                )
                
                # Personalizar gráfico
                fig.update_traces(line=dict(color='#3498db', width=3))
                fig.update_layout(
                    yaxis=dict(tickprefix='$'),
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Opción para crear un nuevo préstamo con estos parámetros
                st.markdown("---")
                if st.button("💵 Crear Préstamo con estos Parámetros", use_container_width=True):
                    # Guardar los parámetros para autocompletar el formulario
                    st.session_state.autocompletar_prestamo = True
                    st.session_state.nuevo_prestamo_params = {
                        'monto': monto,
                        'tasa_interes': tasa_interes,
                        'plazo_meses': plazo_meses,
                        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d')
                    }
                    # Cambiar a la pestaña de creación de préstamos
                    st.session_state.menu = "Gestión de Préstamos"
                    # Activar bandera para ir directamente a la pestaña de creación
                    st.session_state.prestamo_tab = 0
                    st.rerun()
        
        # Gestión de Clientes
        elif current_menu == "Gestión de Clientes":
            st.header("Gestión de Clientes")
            
            # Verificar permisos - solo operadores y administradores pueden gestionar clientes
            if not verificar_permiso("operador"):
                st.warning("No tiene permisos suficientes para modificar clientes. Solo puede ver la información.")
                solo_lectura = True
            else:
                solo_lectura = False
            
            # Pestañas para diferentes acciones de clientes
            tab1, tab2, tab3 = st.tabs(["Registrar Cliente", "Lista de Clientes", "Editar/Eliminar Cliente"])
            
            # Pestaña para registrar nuevo cliente
            with tab1:
                st.subheader("Registrar Nuevo Cliente")
                
                if solo_lectura:
                    st.info("No tiene permisos para registrar nuevos clientes")
                else:
                    with st.form(key="registro_cliente"):
                        nombre = st.text_input("Nombre Completo", max_chars=50, help="Máximo 50 caracteres")
                        cedula = st.text_input("Cédula")
                        telefono = st.text_input("Teléfono")
                        submit_button = st.form_submit_button(label="Registrar Cliente")
                        
                        if submit_button:
                            if nombre and cedula and telefono:
                                # Validar longitud del nombre
                                if len(nombre) > 50:
                                    st.error("El nombre no puede exceder los 50 caracteres")
                                else:
                                    exito, mensaje = agregar_cliente(nombre, cedula, telefono)
                                    if exito:
                                        st.success(mensaje)
                                        # Registrar la actividad
                                        registrar_actividad(st.session_state.usuario, "registro_cliente", {"cliente": nombre, "cedula": cedula})
                                    else:
                                        st.error(mensaje)
                            else:
                                st.error("Todos los campos son obligatorios")
            
            # Pestaña para listar clientes
            with tab2:
                st.subheader("Lista de Clientes")
                clientes = obtener_clientes()
                if not clientes.empty:
                    # Formatear y renombrar columnas para mejor visualización
                    clientes_display = clientes.copy()
                    clientes_display = clientes_display.rename(columns={
                        'id': 'ID',
                        'nombre': 'Nombre Completo',
                        'cedula': 'Cédula',
                        'telefono': 'Teléfono'
                    })
                    
                    # Agregar campo de búsqueda
                    busqueda = st.text_input("🔍 Buscar cliente por nombre, cédula o teléfono", key="buscar_cliente")
                    
                    # Filtrar clientes según la búsqueda
                    if busqueda:
                        # Convertir todo a minúsculas para búsqueda insensible a mayúsculas/minúsculas
                        busqueda = busqueda.lower()
                        clientes_filtrados = clientes_display[
                            clientes_display['Nombre Completo'].str.lower().str.contains(busqueda) |
                            clientes_display['Cédula'].str.lower().str.contains(busqueda) |
                            clientes_display['Teléfono'].str.lower().str.contains(busqueda)
                        ]
                        
                        # Mostrar resultados o mensaje de no encontrado
                        if not clientes_filtrados.empty:
                            st.dataframe(
                                clientes_filtrados,
                                use_container_width=True,
                                hide_index=True
                            )
                            st.caption(f"Resultados encontrados: {len(clientes_filtrados)} de {len(clientes_display)} clientes")
                        else:
                            st.warning("No se encontraron resultados para la búsqueda.")
                    else:
                        # Si no hay búsqueda, mostrar todos los clientes
                        st.dataframe(
                            clientes_display,
                            use_container_width=True,
                            hide_index=True
                        )
                        st.caption(f"Total de clientes registrados: {len(clientes_display)}")
                    
                    # Opciones de exportación avanzada
                    mostrar_opciones_exportacion(clientes_display, "lista_clientes")
                else:
                    st.info("No hay clientes registrados")
            
            # Pestaña para editar o eliminar cliente
            with tab3:
                st.subheader("Editar o Eliminar Cliente")
                
                # Obtener lista de clientes
                clientes = obtener_clientes()
                
                if not clientes.empty:
                    # Verificar permisos - solo administradores pueden editar/eliminar clientes
                    if not verificar_permiso("operador"):
                        st.warning("No tiene permisos suficientes para editar o eliminar clientes. Solo puede ver la información.")
                        solo_lectura = True
                    else:
                        solo_lectura = False
                    
                    # Selector de cliente con opción vacía por defecto
                    opciones_clientes = [None] + clientes['id'].tolist()
                    cliente_seleccionado = st.selectbox(
                        "Seleccione un cliente:",
                        opciones_clientes,
                        format_func=lambda x: "Seleccione un cliente" if x is None else f"{clientes[clientes['id'] == x]['nombre'].values[0]} - {clientes[clientes['id'] == x]['cedula'].values[0]}"
                    )
                    
                    if cliente_seleccionado is not None:
                        cliente = obtener_cliente(cliente_seleccionado)
                        if cliente:
                            # Mostrar información del cliente
                            with st.form(key="editar_cliente"):
                                nombre_edit = st.text_input("Nombre Completo", value=cliente[1], max_chars=50, help="Máximo 50 caracteres")
                                cedula_edit = st.text_input("Cédula", value=cliente[2])
                                telefono_edit = st.text_input("Teléfono", value=cliente[3])
                                
                                # Solo mostrar botones de acción si el usuario tiene permisos
                                if not solo_lectura:
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        submit_edit = st.form_submit_button(label="Actualizar Cliente")
                                    with col2:
                                        # Solo administradores pueden eliminar clientes
                                        if verificar_permiso("administrador"):
                                            submit_delete = st.form_submit_button(label="Eliminar Cliente", type="primary")
                                        else:
                                            submit_delete = False
                                            st.info("Solo administradores pueden eliminar clientes")
                                else:
                                    submit_edit = False
                                    submit_delete = False
                                    st.info("Modo de solo lectura. No puede modificar clientes.")
                                
                                if submit_edit:
                                    if nombre_edit and cedula_edit and telefono_edit:
                                        # Validar longitud del nombre
                                        if len(nombre_edit) > 50:
                                            st.error("El nombre no puede exceder los 50 caracteres")
                                        else:
                                            exito, mensaje = actualizar_cliente(cliente_seleccionado, nombre_edit, cedula_edit, telefono_edit)
                                            if exito:
                                                st.success(mensaje)
                                                # Registrar la actividad
                                                registrar_actividad(st.session_state.usuario, "actualizar_cliente", {"cliente_id": cliente_seleccionado, "nombre": nombre_edit})
                                                st.rerun()
                                            else:
                                                st.error(mensaje)
                                    else:
                                        st.error("Todos los campos son obligatorios")
                                
                                if submit_delete:
                                    # Verificar que se haya seleccionado un cliente
                                    if cliente_seleccionado is None:
                                        st.error("Debe seleccionar un cliente para eliminarlo")
                                    else:
                                        # Configurar el estado para mostrar el diálogo de confirmación
                                        if 'mostrar_confirmacion' not in st.session_state:
                                            st.session_state.mostrar_confirmacion = True
                                            st.session_state.cliente_a_eliminar = cliente_seleccionado
                                            st.session_state.nombre_cliente = cliente[1]
                                            st.rerun()
                            
                            # Mostrar diálogo de confirmación fuera del formulario
                            if 'mostrar_confirmacion' in st.session_state and st.session_state.mostrar_confirmacion:
                                st.warning(f"¿Está seguro que desea eliminar el cliente {st.session_state.nombre_cliente}? Esta acción no se puede deshacer.")
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("Confirmar", key="confirmar_eliminar", type="primary"):
                                        # Confirmar eliminación
                                        eliminar_cliente(st.session_state.cliente_a_eliminar)
                                        st.success("Cliente eliminado exitosamente")
                                        # Registrar la actividad
                                        registrar_actividad(st.session_state.usuario, "eliminar_cliente", 
                                                          {"cliente_id": st.session_state.cliente_a_eliminar, 
                                                           "nombre": st.session_state.nombre_cliente})
                                        # Limpiar el estado
                                        del st.session_state.mostrar_confirmacion
                                        del st.session_state.cliente_a_eliminar
                                        del st.session_state.nombre_cliente
                                        st.rerun()
                                with col2:
                                    if st.button("Cancelar", key="cancelar_eliminar"):
                                        # Limpiar el estado
                                        del st.session_state.mostrar_confirmacion
                                        del st.session_state.cliente_a_eliminar
                                        del st.session_state.nombre_cliente
                                        st.info("Eliminación cancelada")
                                        st.rerun()
                else:
                    st.info("No hay clientes registrados")
        
        # Gestión de Préstamos
        elif current_menu == "Gestión de Préstamos":
            st.header("Gestión de Préstamos")
            
            # Verificar permisos - solo operadores y administradores pueden gestionar préstamos
            if not verificar_permiso("operador"):
                st.warning("No tiene permisos suficientes para modificar préstamos. Solo puede ver la información.")
                solo_lectura = True
            else:
                solo_lectura = False
            
            # Mostrar resumen de préstamos
            prestamos = obtener_prestamos()
            if not prestamos.empty:
                # Contar préstamos por estado
                total_prestamos = len(prestamos)
                pendientes = len(prestamos[prestamos['estado'] == 'Pendiente'])
                pagados = len(prestamos[prestamos['estado'] == 'Pagado'])
                atrasados = len(prestamos[prestamos['estado'] == 'Atrasado'])
                
                # Mostrar métricas de resumen
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Préstamos", total_prestamos)
                with col2:
                    st.metric("Pendientes", pendientes)
                with col3:
                    st.metric("Pagados", pagados)
                with col4:
                    st.metric("Atrasados", atrasados, delta=None, delta_color="inverse")
            
            # Pestañas para diferentes acciones de préstamos
            tab1, tab2, tab3 = st.tabs(["Crear Préstamo", "Lista de Préstamos", "Editar/Eliminar Préstamo"])
            
            # Si venimos de la calculadora, seleccionar la pestaña de creación
            if 'prestamo_tab' in st.session_state:
                # Activar la pestaña correspondiente (0 = Crear Préstamo)
                st.session_state.active_tab = st.session_state.prestamo_tab
                # Limpiar para no activarla nuevamente
                del st.session_state.prestamo_tab
            
            # Pestaña para crear nuevo préstamo
            with tab1:
                st.subheader("Registrar Nuevo Préstamo")
                
                # Verificar si el usuario tiene permisos para crear préstamos
                if solo_lectura:
                    st.info("No tiene permisos para registrar nuevos préstamos. Solo puede ver la información.")
                else:
                    # Obtener lista de clientes para seleccionar
                    clientes = obtener_clientes()
                    if not clientes.empty:
                        with st.form(key="registro_prestamo"):
                            # Seleccionar cliente con búsqueda
                            st.write("### Información del Cliente")
                        
                            # Crear un formato más amigable para mostrar clientes
                            clientes['display_name'] = clientes.apply(
                                lambda x: f"{x['nombre']} - Cédula: {x['cedula']}", axis=1
                            )
                            
                            # Ordenar clientes por nombre para fácil búsqueda
                            clientes = clientes.sort_values('nombre')
                            
                            cliente_id = st.selectbox(
                                "Seleccione un cliente:",
                                clientes['id'].tolist(),
                                format_func=lambda x: clientes[clientes['id'] == x]['display_name'].values[0]
                            )
                            
                            # Mostrar información del cliente seleccionado
                            cliente_seleccionado = clientes[clientes['id'] == cliente_id]
                            st.info(f"Cliente seleccionado: **{cliente_seleccionado['nombre'].values[0]}** | Teléfono: **{cliente_seleccionado['telefono'].values[0]}**")
                            
                            st.write("### Información del Préstamo")
                            # Verificar si hay parámetros de la calculadora para autocompletar
                            monto_valor = 5000.0
                            tasa_valor = 5.0
                            fecha_inicio_valor = datetime.now()
                            fecha_fin_valor = datetime.now().replace(month=datetime.now().month + 1 if datetime.now().month < 12 else 1)
                        
                            # Si venimos de la calculadora, usar esos valores
                            if 'autocompletar_prestamo' in st.session_state and st.session_state.autocompletar_prestamo:
                                if 'nuevo_prestamo_params' in st.session_state:
                                    params = st.session_state.nuevo_prestamo_params
                                    monto_valor = float(params['monto'])
                                    tasa_valor = float(params['tasa_interes'])
                                    fecha_inicio_valor = datetime.strptime(params['fecha_inicio'], '%Y-%m-%d')
                                    
                                    # Calcular fecha de vencimiento basada en el plazo
                                    plazo = int(params['plazo_meses'])
                                    fecha_fin_valor = fecha_inicio_valor
                                    # Sumar meses al año y mes actual
                                    nuevo_mes = fecha_inicio_valor.month + plazo
                                    nuevo_anio = fecha_inicio_valor.year + (nuevo_mes - 1) // 12
                                    nuevo_mes = ((nuevo_mes - 1) % 12) + 1
                                    # Crear nueva fecha con el mes y año calculados
                                    fecha_fin_valor = fecha_inicio_valor.replace(year=nuevo_anio, month=nuevo_mes)
                                    
                                    # Limpiar el flag para no autocompletar en futuras visitas
                                    st.session_state.autocompletar_prestamo = False
                            
                            # Datos del préstamo con mejor formato
                            monto = st.number_input(
                                "Monto del Préstamo ($)", 
                                min_value=0.01, 
                                step=100.0,
                                value=monto_valor,
                                format="%.2f",
                                help="Ingrese el monto total del préstamo"
                            )
                        
                            # Fechas con mejor explicación
                            col1, col2 = st.columns(2)
                            with col1:
                                fecha_prestamo = st.date_input(
                                    "Fecha del Préstamo", 
                                    fecha_inicio_valor,
                                    help="Fecha en que se entrega el dinero"
                                )
                            with col2:
                                fecha_vencimiento = st.date_input(
                                    "Fecha de Vencimiento", 
                                    fecha_fin_valor,
                                    help="Fecha límite para el pago total"
                                )
                            
                            # Tasa de interés con cálculo automático
                            st.write("### Interés y Montos Finales")
                            tasa_interes = st.number_input(
                                "Tasa de Interés (%)", 
                                min_value=0.0, 
                                max_value=100.0, 
                                step=0.5, 
                                value=tasa_valor,
                                format="%.1f",
                                help="Porcentaje de interés a aplicar sobre el monto del préstamo"
                            )
                        
                            # Mostrar cálculo del monto final
                            if tasa_interes > 0:
                                monto_final = monto * (1 + tasa_interes / 100)
                                st.metric(
                                    "Monto Total a Pagar (con interés)", 
                                    f"${monto_final:,.2f}", 
                                    delta=f"+${monto_final - monto:,.2f}",
                                    delta_color="inverse"
                                )
                            else:
                                st.metric("Monto Total a Pagar", f"${monto:,.2f}")
                                tasa_interes = None
                            
                            submit_button = st.form_submit_button(label="Registrar Préstamo", type="primary")
                            
                            if submit_button:
                                if monto > 0 and fecha_vencimiento >= fecha_prestamo:
                                    # Convertir fechas a formato string para SQLite
                                    fecha_prestamo_str = fecha_prestamo.strftime('%Y-%m-%d')
                                    fecha_vencimiento_str = fecha_vencimiento.strftime('%Y-%m-%d')
                                    
                                    exito, mensaje = crear_prestamo(
                                        cliente_id, monto, fecha_prestamo_str, 
                                        fecha_vencimiento_str, tasa_interes
                                    )
                                    
                                    if exito:
                                        st.success(mensaje)
                                        st.balloons()
                                        # Guardar estado para mostrar botón después del form
                                        st.session_state.prestamo_creado = True
                                        # Registrar la actividad
                                        registrar_actividad(st.session_state.usuario, "crear_prestamo", {"cliente_id": cliente_id, "monto": monto})
                                    else:
                                        st.error(mensaje)
                                else:
                                    if monto <= 0:
                                        st.error("El monto debe ser mayor que cero")
                                    if fecha_vencimiento < fecha_prestamo:
                                        st.error("La fecha de vencimiento debe ser posterior a la fecha del préstamo")
                    
                        # Mostrar botón para ir a pagos si se creó un préstamo exitosamente
                        if 'prestamo_creado' in st.session_state and st.session_state.prestamo_creado:
                            if st.button("Ir a Gestión de Pagos", type="primary"):
                                st.session_state.menu = "Gestión de Pagos"
                                st.session_state.prestamo_creado = False  # Resetear el estado
                                st.rerun()
                    else:
                        st.warning("Debe registrar al menos un cliente antes de crear un préstamo")
                        if st.button("Ir a Gestión de Clientes", type="primary"):
                            st.session_state.menu = "Gestión de Clientes"
                            st.rerun()
            
            # Pestaña para listar préstamos
            with tab2:
                st.subheader("Lista de Préstamos")
                
                # Filtros en una sola línea con más opciones
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    filtro_tipo = st.selectbox(
                        "Filtrar por:",
                        ["Todos los préstamos", "Por cliente", "Por estado"]
                    )
                
                # Obtener préstamos según filtro
                if filtro_tipo == "Por cliente":
                    with col2:
                        if not clientes.empty:
                            cliente_filtro = st.selectbox(
                                "Seleccione cliente:",
                                clientes['id'].tolist(),
                                format_func=lambda x: f"{clientes[clientes['id'] == x]['nombre'].values[0]} - {clientes[clientes['id'] == x]['cedula'].values[0]}"
                            )
                            prestamos = obtener_prestamos_cliente(cliente_filtro)
                        else:
                            st.info("No hay clientes registrados")
                            prestamos = pd.DataFrame()
                elif filtro_tipo == "Por estado":
                    with col2:
                        estado_filtro = st.selectbox(
                            "Seleccione estado:",
                            ["Pendiente", "Pagado", "Atrasado"]
                        )
                        prestamos = obtener_prestamos()
                        if not prestamos.empty:
                            prestamos = prestamos[prestamos['estado'] == estado_filtro]
                else:
                    prestamos = obtener_prestamos()
                
                # Botón para actualizar la lista
                with col3:
                    if st.button("Actualizar", type="primary"):
                        st.rerun()
                
                # Mostrar préstamos
                if not prestamos.empty:
                    # Formatear fechas para mejor visualización
                    prestamos_display = prestamos.copy()
                    prestamos_display['fecha_prestamo'] = pd.to_datetime(prestamos_display['fecha_prestamo']).dt.strftime('%d/%m/%Y')
                    prestamos_display['fecha_vencimiento'] = pd.to_datetime(prestamos_display['fecha_vencimiento']).dt.strftime('%d/%m/%Y')
                    
                    # Formatear montos y tasas
                    prestamos_display['monto'] = prestamos_display['monto'].apply(lambda x: f"${x:,.2f}")
                    prestamos_display['tasa_interes'] = prestamos_display['tasa_interes'].apply(lambda x: f"{x}%" if pd.notnull(x) else "N/A")
                    
                    # Aplicar colores a los estados
                    def color_estado(val):
                        if val == 'Pagado':
                            return 'green'
                        elif val == 'Atrasado':
                            return 'red'
                        else:
                            return 'orange'
                    
                    # Renombrar columnas para mejor visualización
                    prestamos_display = prestamos_display.rename(columns={
                        'id': 'ID', 
                        'nombre': 'Cliente',
                        'monto': 'Monto',
                        'fecha_prestamo': 'Fecha Préstamo',
                        'fecha_vencimiento': 'Fecha Vencimiento',
                        'tasa_interes': 'Tasa Interés',
                        'estado': 'Estado'
                    })
                    
                    # Columnas a mostrar (excluir cliente_id)
                    columnas_mostrar = prestamos_display.columns.tolist()
                    if 'cliente_id' in columnas_mostrar:
                        columnas_mostrar.remove('cliente_id')
                    
                    # Mostrar tabla con mejor formato
                    st.dataframe(
                        prestamos_display[columnas_mostrar],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Estado": st.column_config.TextColumn(
                                "Estado",
                                help="Estado actual del préstamo",
                                width="medium",
                            ),
                            "Monto": st.column_config.TextColumn(
                                "Monto",
                                help="Monto original del préstamo",
                                width="medium",
                            )
                        }
                    )
                    
                    # Mostrar total de préstamos filtrados
                    st.caption(f"Total de préstamos mostrados: {len(prestamos_display)}")
                    
                    # Opciones de exportación avanzada
                    mostrar_opciones_exportacion(prestamos_display[columnas_mostrar], "lista_prestamos")
                else:
                    st.info("No hay préstamos que coincidan con los filtros seleccionados")
            
            # Pestaña para editar/eliminar préstamos
            with tab3:
                st.subheader("Editar o Eliminar Préstamo")
                
                # Obtener todos los préstamos
                prestamos = obtener_prestamos()
                
                if not prestamos.empty:
                    # Crear un formato para mostrar en el selectbox
                    prestamos['display'] = prestamos.apply(
                        lambda x: f"ID: {x['id']} - Cliente: {x['nombre']} - Monto: ${x['monto']} - Vence: {x['fecha_vencimiento']}", 
                        axis=1
                    )
                    
                    # Seleccionar préstamo a editar/eliminar
                    prestamo_id = st.selectbox(
                        "Seleccione un préstamo:",
                        prestamos['id'].tolist(),
                        format_func=lambda x: prestamos[prestamos['id'] == x]['display'].values[0]
                    )
                    
                    if prestamo_id:
                        # Obtener datos del préstamo seleccionado
                        prestamo = obtener_prestamo(prestamo_id)
                        
                        if prestamo:
                            with st.form(key="editar_prestamo"):
                                st.write(f"Cliente: {prestamo[2]}")
                                
                                # Campos para editar
                                monto = st.number_input("Monto del Préstamo", min_value=0.01, value=float(prestamo[3]), step=100.0)
                                
                                # Convertir fechas de string a datetime para el date_input
                                fecha_prestamo_dt = datetime.strptime(prestamo[4], '%Y-%m-%d')
                                fecha_vencimiento_dt = datetime.strptime(prestamo[5], '%Y-%m-%d')
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    fecha_prestamo = st.date_input("Fecha del Préstamo", fecha_prestamo_dt)
                                with col2:
                                    fecha_vencimiento = st.date_input("Fecha de Vencimiento", fecha_vencimiento_dt)
                                
                                # Tasa de interés
                                tasa_actual = prestamo[6] if prestamo[6] is not None else 0.0
                                tasa_interes = st.number_input("Tasa de Interés (%)", min_value=0.0, value=float(tasa_actual), max_value=100.0, step=0.5)
                                if tasa_interes == 0.0:
                                    tasa_interes = None
                                
                                # Estado del préstamo
                                estado = st.selectbox(
                                    "Estado del Préstamo",
                                    ["Pendiente", "Pagado", "Atrasado"],
                                    index=["Pendiente", "Pagado", "Atrasado"].index(prestamo[7])
                                )
                                
                                # Botones para actualizar o eliminar
                                col1, col2 = st.columns(2)
                                with col1:
                                    submit_edit = st.form_submit_button(label="Actualizar Préstamo")
                                with col2:
                                    submit_delete = st.form_submit_button(label="Eliminar Préstamo", type="primary")
                                
                                # Procesar actualización
                                if submit_edit:
                                    if monto > 0 and fecha_vencimiento >= fecha_prestamo:
                                        # Convertir fechas a formato string para SQLite
                                        fecha_prestamo_str = fecha_prestamo.strftime('%Y-%m-%d')
                                        fecha_vencimiento_str = fecha_vencimiento.strftime('%Y-%m-%d')
                                        
                                        exito, mensaje = editar_prestamo(
                                            prestamo_id, monto, fecha_prestamo_str, 
                                            fecha_vencimiento_str, tasa_interes, estado
                                        )
                                        
                                        if exito:
                                            st.success(mensaje)
                                            st.rerun()
                                        else:
                                            st.error(mensaje)
                                    else:
                                        if monto <= 0:
                                            st.error("El monto debe ser mayor que cero")
                                        if fecha_vencimiento < fecha_prestamo:
                                            st.error("La fecha de vencimiento debe ser posterior a la fecha del préstamo")
                                
                                # Procesar eliminación
                                if submit_delete:
                                    exito, mensaje = eliminar_prestamo(prestamo_id)
                                    if exito:
                                        st.success(mensaje)
                                        st.rerun()
                                    else:
                                        st.error(mensaje)
                else:
                    st.info("No hay préstamos registrados")
            
        elif current_menu == "Gestión de Pagos":
            st.header("Gestión de Pagos")
            
            # Mostrar mensaje de confirmación de pago si existe
            if 'pago_exitoso' in st.session_state and st.session_state.pago_exitoso:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.success(f"✅ {st.session_state.mensaje_pago} - Monto: ${st.session_state.monto_pagado:,.2f}")
                        if 'prestamo_pagado' in st.session_state and st.session_state.prestamo_pagado:
                            st.balloons()
                            st.success("🎉 ¡Felicidades! El préstamo ha sido pagado completamente")
                    with col2:
                        if st.button("✖ Cerrar", key="cerrar_notificacion"):
                            # Limpiar mensajes de confirmación
                            st.session_state.pago_exitoso = False
                            if 'prestamo_pagado' in st.session_state:
                                del st.session_state.prestamo_pagado
                            st.rerun()
                st.markdown("---")
            
            # Verificar permisos - solo operadores y administradores pueden registrar pagos
            if not verificar_permiso("operador"):
                st.warning("No tiene permisos suficientes para registrar pagos. Solo puede ver la información.")
                solo_lectura = True
            else:
                solo_lectura = False
            
            # Obtener todos los préstamos activos
            prestamos = obtener_prestamos()
            if not prestamos.empty:
                # Filtrar préstamos que no estén pagados
                prestamos_activos = prestamos[prestamos['estado'] != 'Pagado']
                
                if not prestamos_activos.empty:
                    # Crear un formato para mostrar en el selectbox
                    prestamos_activos['display'] = prestamos_activos.apply(
                        lambda x: f"ID: {x['id']} - Cliente: {x['nombre']} - Monto: {x['monto']} - Estado: {x['estado']}", 
                        axis=1
                    )
                    
                    # Seleccionar préstamo para registrar pago
                    prestamo_id = st.selectbox(
                        "Seleccione un préstamo para gestionar pagos:",
                        prestamos_activos['id'].tolist(),
                        format_func=lambda x: prestamos_activos[prestamos_activos['id'] == x]['display'].values[0]
                    )
                    
                    if prestamo_id:
                        # Obtener datos del préstamo seleccionado
                        prestamo = obtener_prestamo(prestamo_id)
                        cliente_id = prestamo[1]
                        cliente_nombre = prestamo[2]
                        monto_prestamo = prestamo[3]
                        tasa_interes = prestamo[6] or 0
                        
                        # Calcular monto total con interés
                        monto_total = monto_prestamo * (1 + tasa_interes / 100)
                        
                        # Calcular saldo pendiente
                        saldo_pendiente = calcular_saldo_pendiente(prestamo_id)
                        
                        # Mostrar información del préstamo
                        st.subheader(f"Préstamo de {cliente_nombre}")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Monto Original", f"${monto_prestamo:,.2f}")
                        with col2:
                            st.metric("Monto Total (con interés)", f"${monto_total:,.2f}")
                        with col3:
                            st.metric("Saldo Pendiente", f"${saldo_pendiente:,.2f}")
                        
                        # Pestañas para registrar pagos y ver historial
                        tab1, tab2 = st.tabs(["Registrar Pago", "Historial de Pagos"])
                        
                        # Pestaña para registrar nuevo pago
                        with tab1:
                            if solo_lectura:
                                st.info("No tiene permisos para registrar pagos. Solo puede ver la información.")
                            
                            with st.form(key="registro_pago"):
                                st.subheader("Registrar Nuevo Pago")
                                
                                # Fecha del pago
                                fecha_pago = st.date_input("Fecha del Pago", datetime.now())
                                
                                # Opciones de pago
                                opcion_pago = st.radio(
                                    "Tipo de pago:",
                                    ["Pago parcial", "Pago completo"]
                                )
                                
                                # Monto pagado
                                if opcion_pago == "Pago completo":
                                    monto_pagado = float(saldo_pendiente)
                                    st.info(f"Se registrará un pago por el saldo total: ${monto_pagado:,.2f}")
                                else:
                                    monto_pagado = st.number_input(
                                        "Monto Pagado", 
                                        min_value=0.01, 
                                        max_value=float(saldo_pendiente),
                                        value=min(float(saldo_pendiente), 100.0), 
                                        step=10.0,
                                        format="%.2f"
                                    )
                                
                                # Mostrar saldo que quedará después del pago
                                saldo_despues = max(0, saldo_pendiente - monto_pagado)
                                st.write(f"Saldo pendiente después del pago: **${saldo_despues:,.2f}**")
                                
                                # Mostrar el botón de registro solo si tiene permisos
                                if solo_lectura:
                                    st.info("No tiene permisos para registrar pagos.")
                                    submit_button = False
                                else:
                                    submit_button = st.form_submit_button(label="Registrar Pago")
                                
                                if submit_button:
                                    if monto_pagado > 0:
                                        # Convertir fecha a formato string para SQLite
                                        fecha_pago_str = fecha_pago.strftime('%Y-%m-%d')
                                        
                                        exito, mensaje = registrar_pago(prestamo_id, fecha_pago_str, monto_pagado)
                                        
                                        if exito:
                                            # Guardar el mensaje de éxito en session_state para mostrarlo después del rerun
                                            st.session_state.pago_exitoso = True
                                            st.session_state.monto_pagado = monto_pagado
                                            st.session_state.mensaje_pago = mensaje
                                            
                                            if saldo_despues <= 0:
                                                st.session_state.prestamo_pagado = True
                                                # Actualizar estado del préstamo a Pagado si corresponde
                                                actualizar_estado_prestamo(prestamo_id, "Pagado")
                                            else:
                                                st.session_state.prestamo_pagado = False
                                                
                                            # Registrar la actividad
                                            registrar_actividad(st.session_state.usuario, "registrar_pago", {"prestamo_id": prestamo_id, "monto": monto_pagado})
                                            st.rerun()
                                        else:
                                            st.error(mensaje)
                                    else:
                                        st.error("El monto debe ser mayor que cero")
                        
                        # Pestaña para ver historial de pagos
                        with tab2:
                            st.subheader("Historial de Pagos")
                            pagos = obtener_pagos(prestamo_id)
                            
                            if not pagos.empty:
                                # Calcular el total pagado
                                total_pagado = pagos['monto_pagado'].sum()
                                st.metric("Total Pagado", f"${total_pagado:,.2f}")
                                
                                # Formatear fechas y montos para mejor visualización
                                pagos_display = pagos.copy()
                                pagos_display['fecha_pago'] = pd.to_datetime(pagos_display['fecha_pago']).dt.strftime('%d/%m/%Y')
                                pagos_display['monto_pagado'] = pagos_display['monto_pagado'].apply(lambda x: f"${x:,.2f}")
                                
                                # Renombrar columnas para mejor visualización
                                pagos_display = pagos_display.rename(columns={
                                    'id': 'ID', 
                                    'fecha_pago': 'Fecha de Pago', 
                                    'monto_pagado': 'Monto Pagado'
                                })
                                
                                # Mostrar tabla de pagos con mejor formato
                                st.dataframe(
                                    pagos_display[['ID', 'Fecha de Pago', 'Monto Pagado']],
                                    use_container_width=True,
                                    hide_index=True
                                )
                                
                                # Opciones de exportación avanzada
                                mostrar_opciones_exportacion(
                                    pagos_display[['ID', 'Fecha de Pago', 'Monto Pagado']], 
                                    f"historial_pagos_prestamo_{prestamo_id}"
                                )
                                
                                # Opción para eliminar pagos
                                with st.expander("Eliminar Pago"):
                                    st.warning("Tenga cuidado al eliminar pagos. Esta acción no se puede deshacer.")
                                    pago_a_eliminar = st.selectbox(
                                        "Seleccione un pago para eliminar:",
                                        pagos['id'].tolist(),
                                        format_func=lambda x: f"ID: {x} - Fecha: {pd.to_datetime(pagos[pagos['id'] == x]['fecha_pago'].values[0]).strftime('%d/%m/%Y')} - Monto: ${float(pagos[pagos['id'] == x]['monto_pagado'].values[0]):,.2f}"
                                    )
                                    
                                    col1, col2 = st.columns([1, 3])
                                    with col1:
                                        if st.button("Eliminar Pago", type="primary"):
                                            exito, mensaje = eliminar_pago(pago_a_eliminar)
                                            if exito:
                                                st.success(mensaje)
                                                st.rerun()
                                            else:
                                                st.error(mensaje)
                            else:
                                st.info("No hay pagos registrados para este préstamo")
                else:
                    st.info("No hay préstamos pendientes o atrasados")
                    if st.button("Ir a Gestión de Préstamos"):
                        st.session_state.menu = "Gestión de Préstamos"
                        st.rerun()
            else:
                st.warning("No hay préstamos registrados en el sistema")
                if st.button("Ir a Gestión de Préstamos"):
                    st.session_state.menu = "Gestión de Préstamos"
                    st.rerun()
            
        elif current_menu == "Reportes":
            st.header("Reportes del Sistema")
            
            # Obtener estadísticas generales
            stats = calcular_estadisticas_prestamos()
            
            # Mostrar dashboard de estadísticas
            st.subheader("Dashboard General")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Préstamos", f"{stats['total_prestamos']}")
                st.metric("Monto Total Prestado", f"${stats['monto_total']:,.2f}")
            with col2:
                st.metric("Préstamos Activos", f"{stats['total_activos']}")
                st.metric("Monto Pendiente de Cobro", f"${stats['monto_pendiente']:,.2f}")
            with col3:
                st.metric("Préstamos Morosos", f"{stats['total_morosos']}", 
                          delta=f"{stats['total_morosos']}", 
                          delta_color="inverse")
                porcentaje_morosidad = (stats['total_morosos'] / stats['total_prestamos'] * 100) if stats['total_prestamos'] > 0 else 0
                st.metric("Índice de Morosidad", f"{porcentaje_morosidad:.1f}%")
            
            # Separador
            st.markdown("---")
            
            # Pestañas para diferentes tipos de reportes
            tab1, tab2, tab3 = st.tabs(["Préstamos Activos", "Préstamos por Cliente", "Préstamos Morosos"])
            
            # Pestaña 1: Préstamos Activos
            with tab1:
                st.subheader("Préstamos Activos")
                prestamos_activos = obtener_prestamos_activos()
                
                if not prestamos_activos.empty:
                    # Formatear fechas para mejor visualización
                    prestamos_display = prestamos_activos.copy()
                    prestamos_display['fecha_prestamo'] = pd.to_datetime(prestamos_display['fecha_prestamo']).dt.strftime('%d/%m/%Y')
                    prestamos_display['fecha_vencimiento'] = pd.to_datetime(prestamos_display['fecha_vencimiento']).dt.strftime('%d/%m/%Y')
                    
                    # Formatear montos y tasas
                    prestamos_display['monto'] = prestamos_display['monto'].apply(lambda x: f"${x:,.2f}")
                    prestamos_display['tasa_interes'] = prestamos_display['tasa_interes'].apply(lambda x: f"{x}%" if pd.notnull(x) else "N/A")
                    
                    # Calcular saldo pendiente para cada préstamo
                    saldos = []
                    for id_prestamo in prestamos_activos['id']:
                        saldos.append(calcular_saldo_pendiente(id_prestamo))
                    prestamos_display['saldo_pendiente'] = saldos
                    prestamos_display['saldo_pendiente'] = prestamos_display['saldo_pendiente'].apply(lambda x: f"${x:,.2f}")
                    
                    # Renombrar columnas para mejor visualización
                    prestamos_display = prestamos_display.rename(columns={
                        'id': 'ID', 
                        'nombre': 'Cliente',
                        'cedula': 'Cédula',
                        'monto': 'Monto Original',
                        'fecha_prestamo': 'Fecha Préstamo',
                        'fecha_vencimiento': 'Fecha Vencimiento',
                        'tasa_interes': 'Tasa Interés',
                        'estado': 'Estado',
                        'saldo_pendiente': 'Saldo Pendiente'
                    })
                    
                    # Columnas a mostrar
                    columnas_mostrar = ['ID', 'Cliente', 'Cédula', 'Monto Original', 'Saldo Pendiente', 
                                       'Fecha Préstamo', 'Fecha Vencimiento', 'Estado']
                    
                    # Mostrar tabla con mejor formato
                    st.dataframe(
                        prestamos_display[columnas_mostrar],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Estado": st.column_config.TextColumn(
                                "Estado",
                                help="Estado actual del préstamo",
                                width="medium",
                            )
                        }
                    )
                    
                    # Mostrar total de préstamos activos
                    st.caption(f"Total de préstamos activos: {len(prestamos_display)}")
                    
                    # Opciones de exportación avanzada
                    mostrar_opciones_exportacion(prestamos_display[columnas_mostrar], "prestamos_activos")
                else:
                    st.info("No hay préstamos activos en el sistema")
            
            # Pestaña 2: Préstamos por Cliente
            with tab2:
                st.subheader("Préstamos por Cliente")
                
                # Obtener lista de clientes
                clientes = obtener_clientes()
                if not clientes.empty:
                    # Crear un formato más amigable para mostrar clientes
                    clientes['display_name'] = clientes.apply(
                        lambda x: f"{x['nombre']} - Cédula: {x['cedula']}", axis=1
                    )
                    
                    # Ordenar clientes por nombre para fácil búsqueda
                    clientes = clientes.sort_values('nombre')
                    
                    # Selector de cliente
                    cliente_id = st.selectbox(
                        "Seleccione un cliente:",
                        clientes['id'].tolist(),
                        format_func=lambda x: clientes[clientes['id'] == x]['display_name'].values[0],
                        key="reporte_cliente"
                    )
                    
                    # Mostrar información del cliente seleccionado
                    cliente_seleccionado = clientes[clientes['id'] == cliente_id]
                    st.info(f"Cliente seleccionado: **{cliente_seleccionado['nombre'].values[0]}** | Teléfono: **{cliente_seleccionado['telefono'].values[0]}**")
                    
                    # Obtener préstamos del cliente
                    prestamos_cliente = obtener_prestamos_cliente(cliente_id)
                    
                    if not prestamos_cliente.empty:
                        # Formatear fechas para mejor visualización
                        prestamos_display = prestamos_cliente.copy()
                        prestamos_display['fecha_prestamo'] = pd.to_datetime(prestamos_display['fecha_prestamo']).dt.strftime('%d/%m/%Y')
                        prestamos_display['fecha_vencimiento'] = pd.to_datetime(prestamos_display['fecha_vencimiento']).dt.strftime('%d/%m/%Y')
                        
                        # Formatear montos y tasas
                        prestamos_display['monto'] = prestamos_display['monto'].apply(lambda x: f"${x:,.2f}")
                        prestamos_display['tasa_interes'] = prestamos_display['tasa_interes'].apply(lambda x: f"{x}%" if pd.notnull(x) else "N/A")
                        
                        # Calcular saldo pendiente para cada préstamo
                        saldos = []
                        for id_prestamo in prestamos_cliente['id']:
                            saldos.append(calcular_saldo_pendiente(id_prestamo))
                        prestamos_display['saldo_pendiente'] = saldos
                        prestamos_display['saldo_pendiente'] = prestamos_display['saldo_pendiente'].apply(lambda x: f"${x:,.2f}")
                        
                        # Renombrar columnas para mejor visualización
                        prestamos_display = prestamos_display.rename(columns={
                            'id': 'ID', 
                            'monto': 'Monto Original',
                            'fecha_prestamo': 'Fecha Préstamo',
                            'fecha_vencimiento': 'Fecha Vencimiento',
                            'tasa_interes': 'Tasa Interés',
                            'estado': 'Estado',
                            'saldo_pendiente': 'Saldo Pendiente'
                        })
                        
                        # Columnas a mostrar
                        columnas_mostrar = ['ID', 'Monto Original', 'Saldo Pendiente', 
                                           'Fecha Préstamo', 'Fecha Vencimiento', 'Estado']
                        
                        # Mostrar tabla con mejor formato
                        st.dataframe(
                            prestamos_display[columnas_mostrar],
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Calcular estadísticas del cliente
                        total_prestamos = len(prestamos_cliente)
                        total_monto = prestamos_cliente['monto'].sum()
                        total_pendiente = sum(saldos)
                        
                        # Mostrar estadísticas del cliente
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total de Préstamos", f"{total_prestamos}")
                        with col2:
                            st.metric("Monto Total Prestado", f"${total_monto:,.2f}")
                        with col3:
                            st.metric("Saldo Pendiente Total", f"${total_pendiente:,.2f}")
                        
                        # Opciones de exportación avanzada
                        mostrar_opciones_exportacion(
                            prestamos_display[columnas_mostrar], 
                            f"prestamos_{cliente_seleccionado['nombre'].values[0].replace(' ', '_')}"
                        )
                    else:
                        st.info(f"No hay préstamos registrados para {cliente_seleccionado['nombre'].values[0]}")
                else:
                    st.warning("No hay clientes registrados en el sistema")
            
            # Pestaña 3: Préstamos Morosos
            with tab3:
                st.subheader("Préstamos Morosos (Atrasados)")
                prestamos_morosos = obtener_prestamos_morosos()
                
                if not prestamos_morosos.empty:
                    # Formatear fechas para mejor visualización
                    prestamos_display = prestamos_morosos.copy()
                    prestamos_display['fecha_prestamo'] = pd.to_datetime(prestamos_display['fecha_prestamo']).dt.strftime('%d/%m/%Y')
                    prestamos_display['fecha_vencimiento'] = pd.to_datetime(prestamos_display['fecha_vencimiento']).dt.strftime('%d/%m/%Y')
                    
                    # Formatear montos y tasas
                    prestamos_display['monto'] = prestamos_display['monto'].apply(lambda x: f"${x:,.2f}")
                    prestamos_display['tasa_interes'] = prestamos_display['tasa_interes'].apply(lambda x: f"{x}%" if pd.notnull(x) else "N/A")
                    
                    # Calcular saldo pendiente y días de atraso para cada préstamo
                    saldos = []
                    dias_atraso = []
                    fecha_actual = datetime.now().date()
                    for idx, row in prestamos_morosos.iterrows():
                        saldos.append(calcular_saldo_pendiente(row['id']))
                        fecha_venc = pd.to_datetime(row['fecha_vencimiento']).date()
                        dias_atraso.append((fecha_actual - fecha_venc).days)
                    
                    prestamos_display['saldo_pendiente'] = saldos
                    prestamos_display['saldo_pendiente'] = prestamos_display['saldo_pendiente'].apply(lambda x: f"${x:,.2f}")
                    prestamos_display['dias_atraso'] = dias_atraso
                    
                    # Renombrar columnas para mejor visualización
                    prestamos_display = prestamos_display.rename(columns={
                        'id': 'ID', 
                        'nombre': 'Cliente',
                        'cedula': 'Cédula',
                        'monto': 'Monto Original',
                        'fecha_prestamo': 'Fecha Préstamo',
                        'fecha_vencimiento': 'Fecha Vencimiento',
                        'tasa_interes': 'Tasa Interés',
                        'estado': 'Estado',
                        'saldo_pendiente': 'Saldo Pendiente',
                        'dias_atraso': 'Días de Atraso'
                    })
                    
                    # Columnas a mostrar
                    columnas_mostrar = ['ID', 'Cliente', 'Cédula', 'Monto Original', 'Saldo Pendiente', 
                                       'Fecha Vencimiento', 'Días de Atraso']
                    
                    # Mostrar tabla con mejor formato
                    st.dataframe(
                        prestamos_display[columnas_mostrar],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Mostrar total de préstamos morosos y monto total pendiente
                    total_morosos = len(prestamos_morosos)
                    total_pendiente = sum(saldos)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total de Préstamos Morosos", f"{total_morosos}")
                    with col2:
                        st.metric("Monto Total en Mora", f"${total_pendiente:,.2f}")
                    
                    # Opciones de exportación avanzada
                    mostrar_opciones_exportacion(prestamos_display[columnas_mostrar], "prestamos_morosos")
                else:
                    st.success("No hay préstamos morosos en el sistema")
                    st.balloons()
        
        elif current_menu == "Seguridad":
            st.header("🔐 Seguridad del Sistema")
            
            # Verificar que el usuario tenga nivel de administrador
            if st.session_state.nivel_acceso != "administrador":
                st.error("No tiene permisos para acceder a esta sección")
                st.button("Volver al Dashboard", on_click=lambda: setattr(st.session_state, 'menu', 'Dashboard'))
            else:
                # Pestañas para diferentes opciones de seguridad
                tab1, tab2, tab3 = st.tabs(["Gestión de Usuarios", "Registro de Actividad", "Cambiar Contraseña"])
                
                # Pestaña 1: Gestión de Usuarios
                with tab1:
                    st.subheader("Gestión de Usuarios")
                    
                    # Mostrar usuarios existentes
                    usuarios = obtener_usuarios()
                    
                    if not usuarios.empty:
                        # Formatear datos para mejor visualización
                        usuarios_display = usuarios.copy()
                        usuarios_display['activo'] = usuarios_display['activo'].apply(lambda x: "Activo" if x == 1 else "Inactivo")
                        
                        # Renombrar columnas para mejor visualización
                        usuarios_display = usuarios_display.rename(columns={
                            'id': 'ID',
                            'usuario': 'Usuario',
                            'nivel_acceso': 'Nivel de Acceso',
                            'nombre_completo': 'Nombre Completo',
                            'email': 'Email',
                            'ultimo_acceso': 'Último Acceso',
                            'activo': 'Estado'
                        })
                        
                        # Mostrar tabla con mejor formato
                        st.dataframe(
                            usuarios_display,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Sección para crear nuevo usuario
                        st.subheader("Crear Nuevo Usuario")
                        with st.form("crear_usuario"):
                            col1, col2 = st.columns(2)
                            with col1:
                                nuevo_usuario = st.text_input("Nombre de Usuario")
                                nueva_contrasena = st.text_input("Contraseña", type="password")
                            with col2:
                                nivel_acceso = st.selectbox(
                                    "Nivel de Acceso",
                                    ["administrador", "operador", "consulta"]
                                )
                                nombre_completo = st.text_input("Nombre Completo (opcional)")
                            
                            email = st.text_input("Email (opcional)")
                            
                            submit_button = st.form_submit_button("Crear Usuario")
                            
                            if submit_button:
                                if nuevo_usuario and nueva_contrasena:
                                    exito, mensaje = crear_usuario(
                                        nuevo_usuario, nueva_contrasena, nivel_acceso, 
                                        nombre_completo if nombre_completo else None,
                                        email if email else None
                                    )
                                    
                                    if exito:
                                        st.success(mensaje)
                                        st.rerun()
                                    else:
                                        st.error(mensaje)
                                else:
                                    st.error("El nombre de usuario y la contraseña son obligatorios")
                        
                        # Sección para activar/desactivar usuarios
                        st.subheader("Activar/Desactivar Usuario")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            usuario_id = st.selectbox(
                                "Seleccione un usuario:",
                                usuarios['id'].tolist(),
                                format_func=lambda x: f"{usuarios[usuarios['id'] == x]['usuario'].values[0]} ({usuarios[usuarios['id'] == x]['nivel_acceso'].values[0]})"
                            )
                        
                        with col2:
                            usuario_activo = usuarios[usuarios['id'] == usuario_id]['activo'].values[0] == 1
                            nuevo_estado = not usuario_activo
                            accion = "Desactivar" if usuario_activo else "Activar"
                            
                            if st.button(f"{accion} Usuario"):
                                if usuarios[usuarios['id'] == usuario_id]['usuario'].values[0] == 'admin' and accion == "Desactivar":
                                    st.error("No se puede desactivar al usuario administrador principal")
                                else:
                                    exito, mensaje = actualizar_estado_usuario(usuario_id, 1 if nuevo_estado else 0)
                                    if exito:
                                        st.success(mensaje)
                                        st.rerun()
                                    else:
                                        st.error(mensaje)
                    else:
                        st.info("No hay usuarios registrados en el sistema")
                
                # Pestaña 2: Registro de Actividad
                with tab2:
                    st.subheader("Registro de Actividad del Sistema")
                    
                    # Filtros para el log de auditoría
                    col1, col2 = st.columns(2)
                    with col1:
                        filtro_usuario = st.selectbox(
                            "Filtrar por usuario:",
                            ["Todos"] + list(obtener_usuarios()['usuario']),
                            index=0
                        )
                    
                    with col2:
                        filtro_accion = st.text_input("Filtrar por acción (contiene):", "")
                    
                    limite = st.slider("Número de registros a mostrar:", 10, 500, 100)
                    
                    # Obtener log de auditoría con filtros
                    usuario_filtro = None if filtro_usuario == "Todos" else filtro_usuario
                    accion_filtro = filtro_accion if filtro_accion else None
                    
                    log = obtener_log_auditoria(limite, usuario_filtro, accion_filtro)
                    
                    if not log.empty:
                        # Formatear datos para mejor visualización
                        log_display = log.copy()
                        
                        # Convertir detalles JSON a formato legible
                        def formatear_detalles(detalles):
                            if pd.isna(detalles) or detalles is None:
                                return ""
                            try:
                                datos = json.loads(detalles)
                                return ", ".join([f"{k}: {v}" for k, v in datos.items()])
                            except:
                                return str(detalles)
                        
                        log_display['detalles'] = log_display['detalles'].apply(formatear_detalles)
                        
                        # Renombrar columnas para mejor visualización
                        log_display = log_display.rename(columns={
                            'id': 'ID',
                            'timestamp': 'Fecha y Hora',
                            'usuario': 'Usuario',
                            'accion': 'Acción',
                            'detalles': 'Detalles',
                            'ip_address': 'Dirección IP'
                        })
                        
                        # Mostrar tabla con mejor formato
                        st.dataframe(
                            log_display,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Opción para exportar a CSV
                        if st.button("Exportar a CSV", key="export_log"):
                            csv = log_display.to_csv(index=False)
                            st.download_button(
                                label="Descargar CSV",
                                data=csv,
                                file_name="registro_actividad.csv",
                                mime="text/csv",
                            )
                    else:
                        st.info("No hay registros de actividad que coincidan con los filtros")
                
                # Pestaña 3: Cambiar Contraseña
                with tab3:
                    st.subheader("Cambiar Contraseña")
                    
                    with st.form("cambiar_contrasena"):
                        # Obtener ID del usuario actual
                        conn = sqlite3.connect('prestamos.db')
                        c = conn.cursor()
                        c.execute("SELECT id FROM usuarios WHERE usuario = ?", (st.session_state.usuario,))
                        usuario_id = c.fetchone()[0]
                        conn.close()
                        
                        contrasena_actual = st.text_input("Contraseña Actual", type="password")
                        nueva_contrasena = st.text_input("Nueva Contraseña", type="password")
                        confirmar_contrasena = st.text_input("Confirmar Nueva Contraseña", type="password")
                        
                        submit_button = st.form_submit_button("Cambiar Contraseña")
                        
                        if submit_button:
                            if not contrasena_actual or not nueva_contrasena or not confirmar_contrasena:
                                st.error("Todos los campos son obligatorios")
                            elif nueva_contrasena != confirmar_contrasena:
                                st.error("Las contraseñas nuevas no coinciden")
                            else:
                                exito, mensaje = cambiar_contrasena(usuario_id, contrasena_actual, nueva_contrasena)
                                if exito:
                                    st.success(mensaje)
                                else:
                                    st.error(mensaje)

# Ejecutar la aplicación
if __name__ == "__main__":
    main()
