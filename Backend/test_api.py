import pytest
import requests
import xml.etree.ElementTree as ET

# Definimos la URL base donde corre tu API (Asegúrate de que app.py esté corriendo)
BASE_URL = "http://127.0.0.1:5001/api"

def test_login_admin_exitoso():
    """Prueba 1: Verificar que el login de administrador funcione correctamente."""
    datos_login = {
        "usuario": "AdminPPCYL2",
        "contrasenia": "AdminPPCYL2771"
    }
    respuesta = requests.post(f"{BASE_URL}/login", json=datos_login)
    
    # Afirmaciones (Asserts): Lo que ESPERAMOS que suceda
    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "admin"

def test_login_credenciales_invalidas():
    """Prueba 2: Verificar que el sistema rechace usuarios inventados."""
    datos_login = {
        "usuario": "UsuarioFalso",
        "contrasenia": "1234"
    }
    respuesta = requests.post(f"{BASE_URL}/login", json=datos_login)
    
    assert respuesta.status_code == 401
    assert "error" in respuesta.json()

def test_cargar_xml_mal_formado():
    """Prueba 3: Verificar que el servidor NO explote si enviamos basura."""
    # Enviamos un texto que NO es XML
    xml_basura = "Esto no es un XML válido"
    respuesta = requests.post(
        f"{BASE_URL}/admin/cargar_xml", 
        data=xml_basura, 
        headers={'Content-Type': 'application/xml'}
    )
    
    assert respuesta.status_code == 400
    assert respuesta.json()["error"] == "El archivo XML está mal formado"

def test_top_notas_curso_inexistente():
    """Prueba 4: Verificar la ruta de notas cuando el curso no existe."""
    curso_falso ="CursoFantasmaInexistente"
    actividad = "Tarea1"
    
    respuesta = requests.get(f"{BASE_URL}/tutor/top_notas/{curso_falso}/{actividad}")
    
    assert respuesta.status_code == 404
    assert respuesta.json()["error"] == "Curso no encontrado" 
def test_matriz_dispersa_ordenamiento():
    """Prueba 5: Verificar que la Matriz Dispersa guarde y ordene las notas correctamente."""
    # 1. Inyectamos un XML de prueba directamente a la ruta de carga
    xml_notas = """<?xml version="1.0"?>
    <carga_notas>
        <curso codigo="999">Curso de Prueba Testing</curso>
        <notas>
            <actividad nombre="ExamenFinal" carnet="111">50</actividad>
            <actividad nombre="ExamenFinal" carnet="222">100</actividad>
            <actividad nombre="ExamenFinal" carnet="333">85</actividad>
        </notas>
    </carga_notas>
    """
    respuesta_carga = requests.post(
        f"{BASE_URL}/tutor/notas/cargar", 
        data=xml_notas.encode('utf-8'), 
        headers={'Content-Type': 'application/xml'}
    )
    assert respuesta_carga.status_code == 200

    # 2. Consultamos el Top de Notas para esa actividad
    respuesta_top = requests.get(f"{BASE_URL}/tutor/top_notas/999/ExamenFinal")
    assert respuesta_top.status_code == 200
    
    datos = respuesta_top.json()
    notas = datos["notas"]
    carnets = datos["carnets"]
    
    # 3. VERIFICACIÓN CRÍTICA: ¿Están ordenados de mayor a menor?
    assert notas[0] == 100.0
    assert carnets[0] == "222"  # El carnet 222 debe ser el primer lugar
    
    assert notas[1] == 85.0
    assert carnets[1] == "333"  # El carnet 333 debe ser el segundo lugar
    
    assert notas[2] == 50.0
    assert carnets[2] == "111"  # El carnet 111 debe ser el último