import requests

# Este es el formato estricto que pide tu documento PDF
xml_notas = """<?xml version="1.0"?>
<carga_notas>
    <curso codigo="770">Ciencias de la Computacion</curso>
    <notas>
        <actividad nombre="Tarea1" carnet="1234">90</actividad>
        <actividad nombre="Tarea1" carnet="5678">50</actividad> <!-- Promedio Tarea1: 70 -->
        
        <actividad nombre="Tarea2" carnet="1234">70</actividad>
        <actividad nombre="Tarea2" carnet="5678">100</actividad> <!-- Promedio Tarea2: 85 -->
        
        <actividad nombre="Tarea3" carnet="1234">85</actividad>
        <actividad nombre="Tarea3" carnet="5678">15</actividad> <!-- Promedio Tarea3: 50 -->
    </notas>
</carga_notas>
"""

# URL de tu Servicio 2 (Flask)
url = "http://localhost:5001/api/tutor/notas/cargar"

print("Enviando XML de notas al Backend...")

try:
    respuesta = requests.post(
        url, 
        data=xml_notas.encode('utf-8'), 
        headers={'Content-Type': 'application/xml'}
    )
    
    if respuesta.status_code == 200:
        print("✅ ¡Éxito!")
        print(respuesta.json())
    else:
        print("❌ Error:", respuesta.status_code)
        print(respuesta.text)
except Exception as e:
    print("No se pudo conectar. ¿Aseguraste que Flask está corriendo en el puerto 5001?")