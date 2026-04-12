import urllib.parse
import graphviz
import base64
from flask import Flask, request, jsonify
import xml.etree.ElementTree as ET
import re
from flasgger import Swagger
from flask import redirect

# Importamos la lógica de las Fases 1 y 2
from xml_processor import extraer_horario_con_pila
from matriz_dispersa import MatrizDispersa

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'AcadNet API Documentation',
    'uiversion': 3
}
swagger = Swagger(app)

@app.route('/')
def index():
    # Si alguien entra a la raíz, lo mandamos directo a la documentación
    return redirect('/apidocs/')

# ========================================================
# SIMULACIÓN DE BASE DE DATOS (En memoria)
# ========================================================
db_usuarios = {"estudiantes": {}, "tutores": {}}
# Diccionario para almacenar una Matriz Dispersa por cada curso
db_cursos = {}

db_tutores = {
    "1111": {"contrasenia": "1234", "nombre": "tutor 1"}
}
db_estudiantes = {
    "1234": {"contrasenia": "1234", "nombre": "estudiante 1"}
}

# ========================================================
# ENDPOINTS (RUTAS HTTP)
# ========================================================

@app.route('/api/admin/cargar_xml', methods=['POST'])
def cargar_configuracion():
    """
    Carga masiva de usuarios (Tutores y Estudiantes) desde XML.
    ---
    tags:
      - Administrador
    consumes:
      - application/xml
    responses:
      200:
        description: Usuarios cargados exitosamente.
      400:
        description: XML mal formado.
    """
    xml_data = request.data.decode('utf-8')
    try:
        root = ET.fromstring(xml_data)
        
        # 1. Extraer y guardar Tutores
        tutores_cargados = 0
        for tutor in root.findall('.//tutor'):
            reg = tutor.get('registro_personal')
            pwd = tutor.get('contrasenia')
            nombre = tutor.text
            db_usuarios["tutores"][reg] = {"nombre": nombre, "password": pwd}
            tutores_cargados += 1
            
        # 2. Extraer y guardar Estudiantes
        estudiantes_cargados = 0
        for est in root.findall('.//estudiante'):
            carnet = est.get('carnet')
            pwd = est.get('contrasenia')
            nombre = est.text
            db_usuarios["estudiantes"][carnet] = {"nombre": nombre, "password": pwd}
            estudiantes_cargados += 1

        # El frontend de Django usará este JSON para crear el XML de salida
        return jsonify({
            "mensaje": "Archivo de configuración procesado correctamente",
            "estadisticas": {
                "tutores_cargados": tutores_cargados,
                "estudiantes_cargados": estudiantes_cargados
            }
        }), 200

    except ET.ParseError:
        return jsonify({"error": "El archivo XML está mal formado"}), 400


@app.route('/api/tutor/horarios/cargar', methods=['POST'])
def cargar_horarios():
    """Recibe XML de horarios y usa la regex con pilas para limpiar la cadena."""
    xml_data = request.data.decode('utf-8')
    try:
        root = ET.fromstring(xml_data)
        horarios_procesados = []
        
        for curso in root.findall('curso'):
            codigo = curso.get('codigo')
            texto_horario = curso.text
            
            # Usamos la función de la Fase 2 (Regex + Pila)
            horario_extraido = extraer_horario_con_pila(texto_horario)
            if horario_extraido:
                horarios_procesados.append({
                    "curso": codigo,
                    "hora_inicio": horario_extraido[0],
                    "hora_fin": horario_extraido[1]
                })
        
        return jsonify({"mensaje": "Horarios extraídos con éxito", "datos": horarios_procesados}), 200
    except ET.ParseError:
        return jsonify({"error": "El archivo XML está mal formado"}), 400


@app.route('/api/tutor/notas/cargar', methods=['POST'])
def cargar_notas():
    """Recibe XML de notas y las inserta en la Matriz Dispersa del curso."""
    xml_data = request.data.decode('utf-8')
    try:
        root = ET.fromstring(xml_data)
        codigo_curso = root.find('curso').get('codigo')
        
        # Si el curso no existe en la BD, creamos su Matriz Dispersa
        if codigo_curso not in db_cursos:
            db_cursos[codigo_curso] = MatrizDispersa(codigo_curso)
        
        matriz = db_cursos[codigo_curso]
        notas_insertadas = 0
        
        # Iterar sobre las actividades y guardarlas en la POO
        for actividad in root.find('notas').findall('actividad'):
            nombre_act = actividad.get('nombre')
            carnet = actividad.get('carnet')
            nota = float(actividad.text)
            
            # Inserción ortogonal usando tu estructura de la Fase 1
            matriz.insertar(nombre_act, carnet, nota)
            notas_insertadas += 1
            
        return jsonify({
            "mensaje": f"Éxito",
            "detalle": f"Se insertaron {notas_insertadas} notas en la matriz del curso {codigo_curso}"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/tutor/notas/promedio/<curso>', methods=['GET'])
def obtener_promedios(curso):
    """Devuelve los promedios de todas las actividades de un curso."""
    if curso not in db_cursos:
        return jsonify({"error": "Curso no encontrado", "actividades": [], "promedios": []}), 404
    
    matriz = db_cursos[curso]
    actividades = matriz.filas()
    promedios = [matriz.promedio_por_actividad(act) for act in actividades]
    
    return jsonify({"actividades": actividades, "promedios": promedios}), 200

@app.route('/api/tutor/top_notas/<curso>/<actividad>', methods=['GET'])
def top_notas(curso, actividad):
    """
    Obtiene el listado ordenado de mejores notas por actividad.
    ---
    tags:
      - Tutor
    parameters:
      - name: curso
        in: path
        type: string
        required: true
      - name: actividad
        in: path
        type: string
        required: true
    responses:
      200:
        description: Listado de notas ordenadas.
    """
    if curso not in db_cursos:
        return jsonify({"error": "Curso no encontrado"}), 404
        
    matriz = db_cursos[curso]
    
    try:
        # Usamos la función que YA sabemos que funciona para tu gráfica
        diccionario_notas = matriz.notas_por_actividad(actividad)
        
        # Ordenar de mayor a menor
        notas_ordenadas = sorted(diccionario_notas.items(), key=lambda x: x[1], reverse=True)
        
        carnets = [str(item[0]) for item in notas_ordenadas]
        notas = [float(item[1]) for item in notas_ordenadas]
        
        return jsonify({"carnets": carnets, "notas": notas}), 200
        
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route('/api/tutor/reporte/graphviz/<curso>', methods=['GET'])
def reporte_graphviz(curso):
    if curso not in db_cursos:
        return jsonify({"error": "Curso no encontrado"}), 404
        
    matriz = db_cursos[curso]
    dot = graphviz.Digraph()
    dot.attr(rankdir='LR') 
    
    dot.node('raiz', 'RESUMEN\nNOTAS', shape='folder', style='filled', fillcolor='lightgoldenrod')
    
    for fila in matriz.filas():
        dot.node(f'F_{fila}', fila, shape='box', style='filled', fillcolor='coral')
        dot.edge('raiz', f'F_{fila}')
        
        actual = matriz._filas.get(fila)
        anterior = f'F_{fila}'
        
        while actual is not None:
            id_nodo = f'N_{actual.fila}_{actual.columna}'
            dot.node(id_nodo, f'{actual.columna}\n{actual.valor}', shape='box')
            dot.edge(anterior, id_nodo) 
            anterior = id_nodo
            actual = actual.siguiente_fila

    # Generamos la URL de la imagen usando QuickChart
    dot_str = dot.source
    dot_encoded = urllib.parse.quote(dot_str)
    url_img = f"https://quickchart.io/graphviz?graph={dot_encoded}"
    
    return jsonify({"imagen_url": url_img}), 200
@app.route('/api/login', methods=['POST'])
def login():
    """
    Autenticación de usuarios por Rol.
    ---
    tags:
      - Seguridad
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            usuario:
              type: string
              example: AdminPPCYL2
            contrasenia:
              type: string
              example: AdminPPCYL2771
    responses:
      200:
        description: Login exitoso con retorno de Rol.
      401:
        description: Credenciales incorrectas.
    """
    datos = request.json
    usuario = datos.get('usuario', '')
    contrasenia = datos.get('contrasenia', '')

    # 1. Verificar si es el Administrador (Credenciales quemadas por el documento)
    if usuario == "AdminPPCYL2" and contrasenia == "AdminPPCYL2771":
        return jsonify({"mensaje": "Bienvenido Admin", "rol": "admin"}), 200

    # 2. Verificar si es Tutor
    if usuario in db_tutores and db_tutores[usuario].get('contrasenia') == contrasenia:
        return jsonify({"mensaje": "Bienvenido Tutor", "rol": "tutor"}), 200

    # 3. Verificar si es Estudiante
    if usuario in db_estudiantes and db_estudiantes[usuario].get('contrasenia') == contrasenia:
        return jsonify({"mensaje": "Bienvenido Estudiante", "rol": "estudiante"}), 200

    # Si no es ninguno, rechazar acceso
    return jsonify({"error": "Credenciales incorrectas"}), 401
@app.route('/api/estudiante/notas/<curso>/<carnet>', methods=['GET'])
def notas_estudiante(curso, carnet):
    if curso not in db_cursos:
        return jsonify({"error": "Curso no encontrado"}), 404
        
    matriz = db_cursos[curso]
    resultados = []
    
    # Recorremos todas las filas (actividades) buscando el carnet (columna)
    for actividad in matriz.filas():
        nota = matriz.obtener(actividad, carnet)
        if nota > 0: # Solo enviamos las actividades donde sí tiene nota
            resultados.append({
                "actividad": actividad,
                "nota": nota
            })
            
    return jsonify({"carnet": carnet, "notas": resultados}), 200 
@app.route('/api/admin/usuarios', methods=['GET'])
def obtener_usuarios():
    lista_usuarios = []
    
    # Extraemos tutores
    for id_usr, datos in db_tutores.items():
        lista_usuarios.append({
            "id": id_usr, 
            "rol": "Tutor", 
            "contrasenia": datos.get("contrasenia", "")
        })
        
    # Extraemos estudiantes
    for id_usr, datos in db_estudiantes.items():
        lista_usuarios.append({
            "id": id_usr, 
            "rol": "Estudiante", 
            "contrasenia": datos.get("contrasenia", "")
        })
        
    return jsonify({"usuarios": lista_usuarios}), 200 
@app.route('/api/cursos', methods=['GET'])
def obtener_cursos():
    # Extraemos todos los códigos de los cursos que están en la matriz
    lista_cursos = [{"codigo": codigo} for codigo in db_cursos.keys()]
    return jsonify({"cursos": lista_cursos}), 200
@app.route('/api/tutor/horarios', methods=['POST'])
def procesar_horarios():
    datos = request.json
    texto = datos.get('texto', '')
    
    # Expresión regular que busca exactamente el formato del PDF: 
    # Busca "HorarioI:", ignora espacios, saca los números "HH:MM", busca "HorarioF:" y saca "HH:MM"
    patron = r'HorarioI:\s*(\d{2}:\d{2})\s*HorarioF:\s*(\d{2}:\d{2})'
    
    # findall busca todas las coincidencias en el texto
    coincidencias = re.findall(patron, texto)
    
    lista_horarios = []
    for inicio, fin in coincidencias:
        lista_horarios.append({
            "inicio": inicio,
            "fin": fin
        })
        
    return jsonify({"horarios": lista_horarios}), 200

if __name__ == '__main__':
    # Levantamos el servidor en el puerto 5001 según tu arquitectura
    print("Iniciando Servicio 2 (Backend API) en http://localhost:5001")
    app.run(port=5001, debug=True)