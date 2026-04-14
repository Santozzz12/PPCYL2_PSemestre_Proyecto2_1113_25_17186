import urllib.parse
import graphviz
import base64
import re
import xml.etree.ElementTree as ET
from flask import Flask, request, jsonify, redirect
from flasgger import Swagger
import xml.etree.ElementTree as ET
import re
from flask import request, jsonify
import xml.etree.ElementTree as ET
from xml.dom import minidom

from xml_processor import extraer_horario_con_pila
from matriz_dispersa import MatrizDispersa

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'AcadNet API Documentation',
    'uiversion': 3
}
swagger = Swagger(app)

db_usuarios = {"estudiantes": {}, "tutores": {}}
db_cursos = {}

db_tutores = {
    "1111": {"contrasenia": "1234", "nombre": "tutor 1"}
}
db_estudiantes = {
    "1234": {"contrasenia": "1234", "nombre": "estudiante 1"}
}
db_asignaciones_estudiantes = {} 
db_asignaciones_tutores = {}

stats = {
    'asig_e_total': 0,
    'asig_e_ok': 0,
    'asig_e_fail': 0,
    'asig_t_total': 0,
    'asig_t_ok': 0,
    'asig_t_fail': 0
}

@app.route('/')
def index():
    return redirect('/apidocs/')

@app.route('/api/tutor/horarios/cargar', methods=['POST'])
def cargar_horarios_tutor():
    try:
        xml_data = request.data.decode('utf-8')
        id_tutor = request.headers.get('Tutor-ID')
        
        root = ET.fromstring(xml_data)
        
        horarios_procesados = [] # Aquí guardaremos los datos para Django

        for curso_element in root.findall('.//curso'):
            curso_codigo = curso_element.get('codigo')
            texto_sucio = curso_element.text
            
            horario_limpio = procesar_horario_con_pila(texto_sucio)
            
            if horario_limpio:
                # 1. VERIFICAMOS LA MEMORIA: ¿Existe el curso?
                if curso_codigo in db_cursos:
                     if not hasattr(db_cursos[curso_codigo], 'horarios'):
                          db_cursos[curso_codigo].horarios = []
                     
                     db_cursos[curso_codigo].horarios.append(horario_limpio)
                     
                     # 2. EL ARREGLO: Guardamos el diccionario completo para que Django lo lea
                     horarios_procesados.append({
                         "curso": curso_codigo,
                         "horario": horario_limpio
                     })
                     print(f"✅ ÉXITO: Horario guardado para curso {curso_codigo}")
                else:
                     print(f"❌ ERROR: El curso {curso_codigo} no existe en la RAM de Flask. ¿Cargaste el XML 1 de Admin?")
            else:
                 print(f"❌ ERROR: Regex falló o formato inválido en curso {curso_codigo}")

        # 3. EL ARREGLO: Le mandamos la llave 'exitosos' que Django está esperando
        return jsonify({
            "mensaje": "Procesamiento finalizado", 
            "exitosos": horarios_procesados
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def procesar_horario_con_pila(texto_sucio):
    # 1. EXPRESIONES REGULARES: Extraemos los grupos de horas
    # Buscamos el patrón HorarioI: HH:mm y HorarioF: HH:mm
    patron = r"HorarioI:\s*(\d{2}:\d{2})\s*HorarioF:\s*(\d{2}:\d{2})"
    match = re.search(patron, texto_sucio)
    
    if not match:
        return None

    hora_inicio = match.group(1)
    hora_final = match.group(2)

    # 2. USO DE PILA: Validamos que las horas tengan el formato HH:mm correctamente
    pila_validacion = []
    for char in hora_inicio + hora_final:
        if char == ":":
            pila_validacion.append(char)
    
    # Si la pila tiene exactamente 2 símbolos ':', la validación es exitosa
    if len(pila_validacion) == 2:
        return {
            "inicio": hora_inicio,
            "fin": hora_final
        }
    return None

@app.route('/api/tutor/horario', methods=['POST'])
def cargar_horario():
    data = request.get_json()
    # Aquí recibirías el código del curso y el texto del horario desde el XML
    texto = data.get('texto_horario')
    resultado = procesar_horario_con_pila(texto)
    
    if resultado:
        # Guardamos en tu diccionario de base de datos
        return jsonify({"mensaje": "Horario procesado exitosamente", "datos": resultado}), 200
    return jsonify({"error": "Formato de horario inválido"}), 400


@app.route('/api/admin/cargar_xml', methods=['POST'])
def cargar_configuracion():
    xml_data = request.data.decode('utf-8')
    try:
        root = ET.fromstring(xml_data)
        
        # 1. Cargar Cursos
        for curso in root.iter('curso'):
            codigo = curso.get('codigo')
            if codigo and codigo not in db_cursos:
                db_cursos[codigo] = MatrizDispersa(codigo)

        # 2. Cargar Tutores
        for tutor in root.iter('tutor'):
            reg = tutor.get('registro_personal')
            pwd = tutor.get('contrasenia')
            nom = tutor.text.strip() if tutor.text else "Sin nombre"
            if reg and pwd:
                db_tutores[reg] = {"nombre": nom, "contrasenia": pwd}
            
        # 3. Cargar Estudiantes
        estudiantes_cargados = 0
        for est in root.iter('estudiante'):
            carnet = est.get('carnet')
            pwd = est.get('contrasenia')
            nom = est.text.strip() if est.text else "Sin nombre"
            if carnet and pwd:
                db_estudiantes[carnet] = {"nombre": nom, "contrasenia": pwd}
                estudiantes_cargados += 1

        global stats
        for key in stats:
            stats[key] = 0

        # Bloque de asignaciones de ESTUDIANTES (Formato Original)
        asignaciones_e_cargadas = 0
        for asig in root.iter('estudiante_curso'):
            stats['asig_e_total'] += 1
            codigo_curso = asig.get('codigo')
            carnet = asig.text.strip() if asig.text else ""
            
            if carnet and codigo_curso:
                if carnet in db_estudiantes and codigo_curso in db_cursos:
                    stats['asig_e_ok'] += 1
                    if carnet not in db_asignaciones_estudiantes:
                        db_asignaciones_estudiantes[carnet] = []
                    if codigo_curso not in db_asignaciones_estudiantes[carnet]:
                        db_asignaciones_estudiantes[carnet].append(codigo_curso)
                        asignaciones_e_cargadas += 1
                else:
                    stats['asig_e_fail'] += 1
            else:
                stats['asig_e_fail'] += 1

        # Bloque de asignaciones de TUTORES (Formato Original)
        asignaciones_t_cargadas = 0
        for asig in root.iter('tutor_curso'):
            stats['asig_t_total'] += 1
            codigo_curso = asig.get('codigo')
            rp = asig.text.strip() if asig.text else ""
            
            if rp and codigo_curso:
                if rp in db_tutores and codigo_curso in db_cursos:
                    stats['asig_t_ok'] += 1
                    if rp not in db_asignaciones_tutores:
                        db_asignaciones_tutores[rp] = []
                    if codigo_curso not in db_asignaciones_tutores[rp]:
                        db_asignaciones_tutores[rp].append(codigo_curso)
                        asignaciones_t_cargadas += 1
                else:
                    stats['asig_t_fail'] += 1
            else:
                stats['asig_t_fail'] += 1
        
        # Bloque de NUEVO FORMATO REQUERIDO DE ASIGNACIONES:
        asignaciones = root.find('asignaciones')
        if asignaciones is not None:
            for asig in asignaciones.findall('asignacion'):
                stats['asig_e_total'] += 1
                carnet = asig.get('carnet')
                codigo_curso = asig.get('codigo_curso')
                
                if carnet and codigo_curso:
                    if carnet in db_estudiantes and codigo_curso in db_cursos:
                        stats['asig_e_ok'] += 1
                        if carnet not in db_asignaciones_estudiantes:
                            db_asignaciones_estudiantes[carnet] = []
                        if codigo_curso not in db_asignaciones_estudiantes[carnet]:
                            db_asignaciones_estudiantes[carnet].append(codigo_curso)
                            asignaciones_e_cargadas += 1
                    else:
                        stats['asig_e_fail'] += 1
                else:
                    stats['asig_e_fail'] += 1
        
        print(f"DEBUG: Asignaciones guardadas: {db_asignaciones_estudiantes}")

        return jsonify({
            "mensaje": "Configuración cargada exitosamente",
            "estadisticas": {
                "tutores": len(db_tutores),
                "estudiantes": estudiantes_cargados,
                "asignaciones": asignaciones_e_cargadas + asignaciones_t_cargadas,
                "cursos": len(db_cursos)
            }
        }), 200

    except Exception as e:
        print(f"ERROR EN CARGA: {str(e)}")
        return jsonify({"error": str(e)}), 400

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
@app.route('/api/login/', methods=['POST'])
def login():
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibió JSON"}), 400

        usuario = str(datos.get('usuario', '')).strip()
        contrasenia = str(datos.get('contrasenia', '')).strip()

        print(f"--- INTENTO DE LOGIN ---")
        print(f"Usuario recibido: [{usuario}]")
        print(f"Clave recibida: [{contrasenia}]")

        # 1. Admin
        if usuario == "AdminPPCYL2" and contrasenia == "AdminPPCYL2771":
            return jsonify({"mensaje": "Bienvenido Admin", "rol": "admin"}), 200

        # 2. Tutor
        if usuario in db_tutores:
            if str(db_tutores[usuario].get('contrasenia')) == contrasenia:
                return jsonify({"mensaje": "Bienvenido Tutor", "rol": "tutor"}), 200

        # 3. Estudiante
        if usuario in db_estudiantes:
            if str(db_estudiantes[usuario].get('contrasenia')) == contrasenia:
                return jsonify({"mensaje": "Bienvenido Estudiante", "rol": "estudiante"}), 200

        return jsonify({"error": "Credenciales incorrectas"}), 401
    except Exception as e:
        print(f"ERROR CRÍTICO EN LOGIN: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500 
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
    # --- RUTA PARA QUE EL ESTUDIANTE PIDA SUS CURSOS ---
# --- ESTA ES LA RUTA QUE TE FALTA Y POR ESO DA 404 ---
@app.route('/api/estudiante/<carnet>/cursos', methods=['GET'])
def obtener_cursos_del_estudiante(carnet):
    # db_asignaciones_estudiantes es el diccionario que ya vimos que sí tiene datos
    lista_de_cursos = db_asignaciones_estudiantes.get(str(carnet), [])
    return jsonify({"cursos": lista_de_cursos}), 200
@app.route('/api/estudiante/notas/<curso>/<carnet>', methods=['GET'])
def obtener_notas_estudiante(curso, carnet):
    if curso not in db_cursos:
        return jsonify({"notas": []}), 404
    
    matriz = db_cursos[curso]
    notas_encontradas = []
    
    # 1. Obtenemos la lista de nombres de actividades (filas)
    # Como en tu clase 'filas' es un método, lo llamamos con ()
    nombres_actividades = matriz.filas() 
    
    # 2. Recorremos cada actividad buscando el carnet del estudiante
    for actividad in nombres_actividades:
        # Usamos tu método 'obtener' que ya busca por fila y columna
        nota = matriz.obtener(actividad, carnet)
        
        # Si la nota es mayor a 0 (o si quieres mostrar todas, quita el if)
        if nota > 0:
            notas_encontradas.append({
                "actividad": actividad,
                "nota": nota
            })

    print(f"✅ Notas encontradas para {carnet}: {notas_encontradas}")
    return jsonify({"notas": notas_encontradas}), 200
@app.route('/api/reportes/top-notas/<codigo_curso>/<actividad>', methods=['GET'])
def obtener_top_notas(codigo_curso, actividad):
    if codigo_curso in db_cursos:
        matriz = db_cursos[codigo_curso]
        
        # 1. Obtenemos el diccionario { carnet: nota } de esa actividad
        notas_dict = matriz.notas_por_actividad(actividad)
        
        # 2. Convertimos a lista y ordenamos de mayor a menor por el valor de la nota
        # sorted_notas será una lista de tuplas: [('1234', 95), ('5678', 85)...]
        sorted_notas = sorted(notas_dict.items(), key=lambda item: item[1], reverse=True)
        
        # 3. Tomamos los primeros 5 (o los que quieras)
        top_5 = sorted_notas[:5]
        
        return jsonify({
            "carnets": [item[0] for item in top_5],
            "notas": [item[1] for item in top_5]
        }), 200
        
    return jsonify({"error": "No hay datos"}), 404

@app.route('/api/estudiante/consultar/<carnet>', methods=['GET'])
def consultar_notas_estudiante(carnet):
    notas_totales = []
    print(f"🔍 DEBUG: Buscando notas para el carnet: [{carnet}]") # Esto saldrá en tu terminal
    print(f"DEBUG: Cursos cargados actualmente: {list(db_cursos.keys())}")
    for codigo, curso in db_cursos.items():
        matriz = curso
        actividades = matriz.filas() 
        print(f"👉 DEBUG: Curso {codigo} tiene filas (actividades): {actividades}")
        
        for act in actividades:
            if hasattr(matriz, 'obtener'):
                nota = matriz.obtener(act, carnet)
            else:
                nota = matriz.obtener_nota(act, carnet)
            
            print(f"     -> Chequeando actividad: [{act}] para carnet [{carnet}]. Nota obtenida: {nota}")
            if nota > 0:
                print(f"✅ ¡Encontrado! Curso: {codigo}, Actividad: {act}, Nota: {nota}")
                notas_totales.append({
                    'curso': codigo,
                    'actividad': act,
                    'nota': nota,
                    'estado': 'Aprobado' if nota >= 61 else 'Reprobado'
                })
    
    if not notas_totales:
        print(f"❌ No se encontró nada para {carnet}")
        return jsonify({"mensaje": "No se encontraron notas"}), 404
    return jsonify(notas_totales), 200
        
    return jsonify(notas_totales), 200
@app.route('/api/admin/generar-reporte', methods=['GET'])
def generar_xml_salida():
    import xml.etree.ElementTree as ET
    from xml.dom import minidom
    from flask import Response

    root = ET.Element("configuraciones_aplicadas")
    
    ET.SubElement(root, "tutores_cargados").text = str(len(db_tutores))
    ET.SubElement(root, "estudiantes_cargados").text = str(len(db_estudiantes))
    
    asig = ET.SubElement(root, "asignaciones")
    
    t_sec = ET.SubElement(asig, "tutores")
    ET.SubElement(t_sec, "total").text = str(stats['asig_t_total'])
    ET.SubElement(t_sec, "correcto").text = str(stats['asig_t_ok'])
    ET.SubElement(t_sec, "incorrecto").text = str(stats['asig_t_fail'])
    
    e_sec = ET.SubElement(asig, "estudiantes")
    ET.SubElement(e_sec, "total").text = str(stats['asig_e_total'])
    ET.SubElement(e_sec, "correcto").text = str(stats['asig_e_ok'])
    ET.SubElement(e_sec, "incorrecto").text = str(stats['asig_e_fail'])
    
    xml_bytes = ET.tostring(root, encoding='utf-8')
    reparsed = minidom.parseString(xml_bytes)
    pretty_xml = reparsed.toprettyxml(indent="   ").strip() 
    
    return Response(pretty_xml, mimetype='application/xml')

if __name__ == '__main__':
    app.run(port=5001, debug=True)