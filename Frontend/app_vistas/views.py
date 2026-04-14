from django.shortcuts import render, redirect
import requests
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
import requests
from django.contrib import messages
import requests # Asegúrate de tener esto arriba
from django.shortcuts import render, redirect

import requests
from django.shortcuts import render

import requests
from django.shortcuts import render
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def descargar_reporte_horarios(request):
    # 1. Configuramos la respuesta HTTP para que el navegador sepa que es un PDF descargable
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Reporte_Horarios_Tutor.pdf"'

    # 2. Creamos el "lienzo" del PDF
    p = canvas.Canvas(response, pagesize=letter)
    
    # 3. Dibujamos el título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 750, "REPORTE DE HORARIOS - ACADNET")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, 720, "Tutor ID: 1111")
    p.drawString(50, 700, "-" * 100)

    # 4. Aquí simulamos los datos que ya tienes en tu contexto
    # (En la vida real, sacarías esto de tu variable contexto['horarios'])
    y = 660
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Curso")
    p.drawString(200, y, "Hora de Inicio")
    p.drawString(350, y, "Hora de Fin")
    
    p.setFont("Helvetica", 12)
    y -= 30
    
    # Ejemplo de cómo pintarías la tabla de horarios
    horarios_ejemplo = [
        {"curso": "770", "inicio": "09:40", "fin": "10:30"},
        {"curso": "771", "inicio": "11:00", "fin": "12:30"}
    ]
    
    for h in horarios_ejemplo:
        p.drawString(50, y, h['curso'])
        p.drawString(200, y, h['inicio'])
        p.drawString(350, y, h['fin'])
        y -= 25 # Bajamos el "lápiz" para la siguiente línea

    # 5. Guardamos y cerramos el documento
    p.showPage()
    p.save()

    return response

def vista_cargar_horarios(request):
    horarios_extraidos = []
    mensaje_error = None
    xml_content = ""

    if request.method == 'POST':
        xml_content = request.POST.get('contenido_xml')

        if xml_content:
            url_flask = "http://localhost:5001/api/tutor/horarios/cargar"
            headers = {
                'Content-Type': 'application/xml',
                'Tutor-ID': '1111' 
            }

            try:
                respuesta = requests.post(url_flask, data=xml_content.encode('utf-8'), headers=headers)
                
                if respuesta.status_code == 200:
                    data = respuesta.json()
                    # Extraemos los datos si todo salió bien
                    for item in data.get('exitosos', []):
                        horarios_extraidos.append(item['horario'])
                    
                    if not horarios_extraidos:
                        mensaje_error = "Flask procesó el XML, pero los cursos no están asignados al tutor o el formato es incorrecto."
                else:
                    # ¡AQUÍ CAPTURAMOS EL ERROR SECRETO DE FLASK!
                    mensaje_error = f"Error en Flask (Código {respuesta.status_code}): {respuesta.text}"
                    
            except Exception as e:
                mensaje_error = f"No se pudo conectar al puerto 5001: {e}"

    contexto = {
        'horarios': horarios_extraidos,
        'error': mensaje_error,
        'xml_ingresado': xml_content # Para que no se borre tu texto
    }
    return render(request, 'tutor_horarios.html', contexto)
def cargar_horarios_view(request):
    # Asumiendo que el tutor ya inició sesión y tienes su ID en la sesión
    id_tutor = request.session.get('usuario_id') 

    if request.method == 'POST' and request.FILES.get('archivo_horarios'):
        archivo = request.FILES['archivo_horarios']
        xml_content = archivo.read().decode('utf-8')

        url_flask = "http://localhost:5001/api/tutor/horarios/cargar"
        headers = {
            'Content-Type': 'application/xml',
            'Tutor-ID': str(id_tutor) # Enviamos el ID del tutor en los headers
        }

        try:
            # Enviamos el XML tal cual a Flask
            respuesta = requests.post(url_flask, data=xml_content.encode('utf-8'), headers=headers)
            
            if respuesta.status_code == 200:
                data = respuesta.json()
                messages.success(request, f"Horarios procesados: {len(data['exitosos'])} éxitos, {len(data['errores'])} errores.")
            else:
                messages.error(request, f"Error en Flask: {respuesta.json().get('error', 'Desconocido')}")
                
        except requests.exceptions.RequestException as e:
            messages.error(request, f"Error conectando a Flask: {e}")

        return redirect('tutor_horarios') # Redirige a tu vista de la tabla

    return render(request, 'tutor_horarios.html')

API_URL = "http://127.0.0.1:5001/api"

# --- VISTA DE LOGIN ---
def login_view(request):
    if request.method == 'POST':
        usu = request.POST.get('usuario')
        contra = request.POST.get('contrasenia')

        try:
            respuesta = requests.post(f"{API_URL}/login/", json={"usuario": usu, "contrasenia": contra})
            
            if respuesta.status_code == 200:
                datos = respuesta.json()
                rol = datos.get('rol')
                
                request.session['usuario'] = usu
                request.session['rol'] = rol
                
                if rol == 'admin':
                    return redirect('admin_dashboard')
                elif rol == 'tutor':
                    # ¡AQUÍ ESTÁ LA CORRECCIÓN! Ahora usa 'reportes' que es el nombre en urls.py
                    return redirect('reportes') 
                elif rol == 'estudiante':
                    return redirect('mis_notas')
            else:
                return render(request, 'login.html', {'error': "Usuario o contraseña incorrectos"})
        except Exception as e:
            # ESTO IMPRIMIRÁ EL ERROR REAL EN LA TERMINAL DE DJANGO
            print(f"!!! ERROR REAL EN DJANGO: {str(e)}") 
            return render(request, 'login.html', {'error': f"Error interno: {str(e)}"})

    return render(request, 'login.html')

# --- VISTAS DEL ADMINISTRADOR ---
def admin_dashboard(request):
    if request.session.get('rol') != 'admin':
        return redirect('login')

    contexto = {'xml_entrada': '', 'xml_salida': ''}

    if request.method == 'POST':
        if 'btn_limpiar' in request.POST:
            return render(request, 'admin.html', contexto)

        if 'btn_cargar' in request.POST and 'archivo_xml' in request.FILES:
            archivo = request.FILES['archivo_xml']
            contexto['xml_entrada'] = archivo.read().decode('utf-8')

        if 'btn_procesar' in request.POST:
            xml_contenido = request.POST.get('texto_xml')
            contexto['xml_entrada'] = xml_contenido
            try:
                respuesta = requests.post(f"{API_URL}/admin/cargar_xml", data=xml_contenido.encode('utf-8'), headers={'Content-Type': 'application/xml'})
                if respuesta.status_code == 200:
                    contexto['xml_salida'] = respuesta.text
            except:
                contexto['xml_salida'] = "Error de conexión con el Backend"

    return render(request, 'admin.html', contexto)

def ver_usuarios(request):
    if request.session.get('rol') != 'admin':
        return redirect('login')

    usuarios_cargados = []
    try:
        respuesta = requests.get(f"{API_URL}/admin/usuarios")
        if respuesta.status_code == 200:
            usuarios_cargados = respuesta.json().get("usuarios", [])
    except:
        pass
        
    return render(request, 'ver_usuarios.html', {'usuarios': usuarios_cargados})

# --- VISTAS DEL TUTOR ---

import requests
from django.shortcuts import render, redirect

def tutor_horarios(request):
    if request.session.get('rol') != 'tutor':
        return redirect('login')

    # Diccionario de contexto inicial
    contexto = {'xml_entrada': '', 'horarios': [], 'error': None}

    if request.method == 'POST':
        if 'btn_limpiar' in request.POST:
            return render(request, 'tutor_horarios.html', contexto)

        if 'btn_cargar' in request.POST and 'archivo_xml' in request.FILES:
            archivo = request.FILES['archivo_xml']
            contexto['xml_entrada'] = archivo.read().decode('utf-8')

        # 👇 AQUÍ ESTÁ EL BLOQUE INTEGRADO 👇
        if 'btn_procesar' in request.POST:
            xml_contenido = request.POST.get('contenido_xml') 
            contexto['xml_entrada'] = xml_contenido
            
            try:
                # 🚨 CREAMOS LOS HEADERS COMPLETOS AQUÍ 🚨
                mis_headers = {
                    'Content-Type': 'application/xml',
                    'Tutor-ID': '1111'  # <-- ¡ESTE ES EL PASE VIP QUE FLASK ESTABA PIDIENDO!
                }

                # Enviamos el XML con los headers correctos
                # (Asegúrate de que API_URL esté definida arriba en tu archivo, o usa "http://localhost:5001/api")
                respuesta = requests.post(f"{API_URL}/tutor/horarios/cargar", data=xml_contenido.encode('utf-8'), headers=mis_headers)
                
                # Manejamos la respuesta de Flask
                if respuesta.status_code == 200:
                    datos = respuesta.json()
                    
                    # Extraemos los horarios (ajusta la llave 'exitosos' o 'procesados' según lo que devuelva tu Flask)
                    lista_horarios = []
                    for item in datos.get('exitosos', []):
                        lista_horarios.append(item['horario'])
                        
                    contexto['horarios'] = lista_horarios
                    
                    if not contexto['horarios']:
                         contexto['error'] = "El XML se procesó, pero no se encontraron horarios válidos o el curso no está asignado."
                else:
                    contexto['error'] = f"Error en Flask ({respuesta.status_code}): {respuesta.text}"
                    
            except Exception as e:
                contexto['error'] = f"No se pudo conectar con Flask: {str(e)}"
        # 👆 FIN DEL BLOQUE INTEGRADO 👆

    return render(request, 'tutor_horarios.html', contexto)

def tutor_notas(request):
    if request.session.get('rol') != 'tutor':
        return redirect('login')

    contexto = {'xml_entrada': '', 'mensaje': ''}

    if request.method == 'POST':
        if 'btn_limpiar' in request.POST:
            return render(request, 'tutor_notas.html', contexto)

        if 'btn_cargar' in request.POST and 'archivo_xml' in request.FILES:
            archivo = request.FILES['archivo_xml']
            contexto['xml_entrada'] = archivo.read().decode('utf-8')

        if 'btn_procesar' in request.POST:
            xml_contenido = request.POST.get('texto_xml')
            contexto['xml_entrada'] = xml_contenido
            try:
                # Enviamos el XML a la ruta de Flask que llena la Matriz Dispersa
                respuesta = requests.post(f"{API_URL}/tutor/notas/cargar", data=xml_contenido.encode('utf-8'), headers={'Content-Type': 'application/xml'})
                if respuesta.status_code == 200:
                    contexto['mensaje'] = "¡Éxito! Notas integradas en la Matriz Dispersa."
                else:
                    contexto['mensaje'] = f"Error: {respuesta.text}"
            except:
                contexto['mensaje'] = "Error de conexión con el Backend"

    return render(request, 'tutor_notas.html', contexto)

def reporte_tutor(request):
    if request.session.get('rol') != 'tutor':
        return redirect('login')

    lista_cursos = []
    try:
        resp_cursos = requests.get(f"{API_URL}/cursos")
        if resp_cursos.status_code == 200:
            lista_cursos = resp_cursos.json().get("cursos", [])
    except:
        pass

    curso_seleccionado = None
    actividades = []
    promedios = []
    imagen_graphviz = ""

    if request.method == 'POST':
        curso_seleccionado = request.POST.get('curso_select')

    if curso_seleccionado:
        try:
            respuesta = requests.get(f"{API_URL}/tutor/notas/promedio/{curso_seleccionado}")
            if respuesta.status_code == 200:
                datos = respuesta.json()
                actividades = datos.get("actividades", [])
                promedios = datos.get("promedios", [])

            resp_grafo = requests.get(f"{API_URL}/tutor/reporte/graphviz/{curso_seleccionado}")
            if resp_grafo.status_code == 200:
                imagen_graphviz = resp_grafo.json().get("imagen_url", "")
        except:
            pass

    contexto = {
        'cursos': lista_cursos,
        'curso_actual': curso_seleccionado,
        'actividades': actividades,
        'promedios': promedios,
        'grafo': imagen_graphviz
    }
    return render(request, 'tutor_reportes.html', contexto)

def top_notas_tutor(request):
    if request.session.get('rol') != 'tutor':
        return redirect('login')

    lista_cursos = []
    try:
        resp = requests.get(f"{API_URL}/cursos")
        if resp.status_code == 200:
            lista_cursos = resp.json().get("cursos", [])
    except:
        pass

    curso_seleccionado = None
    actividad_seleccionada = None
    carnets = []
    notas = []

    if request.method == 'POST':
        curso_seleccionado = request.POST.get('curso_select')
        actividad_seleccionada = request.POST.get('actividad_txt')

        if curso_seleccionado and actividad_seleccionada:
            try:
                url = f"{API_URL}/tutor/top_notas/{curso_seleccionado}/{actividad_seleccionada}"
                resp_top = requests.get(url)
                if resp_top.status_code == 200:
                    datos = resp_top.json()
                    carnets = datos.get("carnets", [])
                    notas = datos.get("notas", [])
            except:
                pass

    contexto = {
        'cursos': lista_cursos,
        'curso_actual': curso_seleccionado,
        'actividad_actual': actividad_seleccionada,
        'carnets': carnets,
        'notas': notas
    }
    return render(request, 'tutor_top.html', contexto)

def mis_notas(request):
    if request.session.get('rol') != 'estudiante':
        return redirect('login')

    carnet = request.session.get('usuario') 
    cursos_asignados = []
    curso_seleccionado = None
    notas_estudiante = []
    
    # 1. Pedir cursos a Flask
    try:
        # IMPORTANTE: Asegúrate que API_URL sea http://127.0.0.1:5001/api
        url_cursos = f"{API_URL}/estudiante/{carnet}/cursos"
        resp_cursos = requests.get(url_cursos)
        
        if resp_cursos.status_code == 200:
            # Flask manda {"cursos": ["770"]}, así que extraemos esa lista
            cursos_asignados = resp_cursos.json().get("cursos", [])
            print(f"DEBUG DJANGO: Cursos recibidos para {carnet} -> {cursos_asignados}")
    except Exception as e:
        print(f"ERROR DJANGO AL PEDIR CURSOS: {str(e)}")

    # 2. Si el estudiante elige un curso del menú
    if request.method == 'POST':
        curso_seleccionado = request.POST.get('curso_select')
        if curso_seleccionado:
            try:
                url_notas = f"{API_URL}/estudiante/notas/{curso_seleccionado}/{carnet}"
                respuesta = requests.get(url_notas)
                if respuesta.status_code == 200:
                    notas_estudiante = respuesta.json().get("notas", [])
            except:
                pass
        
    contexto = {
        'carnet': carnet,
        'cursos': cursos_asignados, # Esta es la lista que llena el menú
        'curso_actual': curso_seleccionado,
        'notas': notas_estudiante
    }
    return render(request, 'mis_notas.html', contexto)
def tutor_reportes(request):
    # Textos literales para que JavaScript los entienda rápido
    contexto = {
        'labels_str': "['Parcial 1', 'Proyecto 1', 'Examen Final']",
        'data_str': "[75, 90, 85]"
    }
    return render(request, 'tutor_reportes.html', contexto) 
    import json # Asegúrate de tener esto hasta arriba en tu views.py
from django.shortcuts import render

def reportes_tutor(request):
    # 1. Simulamos los cursos que el tutor tiene asignados (para el <select>)
    cursos_disponibles = [
        {'codigo': '770'},
        {'codigo': '771'},
        {'codigo': '999'}
    ]

    # Contexto base que siempre se envía al HTML
    contexto = {
        'cursos': cursos_disponibles,
        'curso_actual': None,
    }

    # 2. Si el tutor presionó el botón "Seleccionar"
    if request.method == 'POST':
        curso_seleccionado = request.POST.get('curso_select')
        contexto['curso_actual'] = curso_seleccionado

        # ---------------------------------------------------------
        # 🚨 ZONA DE PRUEBA: Datos quemados (Aquí irá el requests a Flask después)
        # ---------------------------------------------------------
        if curso_seleccionado == '770':
            actividades = ['Parcial 1', 'Parcial 2', 'Proyecto 1', 'Examen Final']
            promedios = [75.5, 62.0, 95.0, 80.5]
        elif curso_seleccionado == '771':
            actividades = ['Hoja de Trabajo 1', 'Corto 1', 'Examen Final']
            promedios = [100.0, 45.0, 78.0]
        else:
            actividades = ['Evaluación Única']
            promedios = [60.0]

        # 3. Empacamos los datos en formato JSON para que JavaScript (Chart.js) los entienda
        contexto['actividades'] = json.dumps(actividades)
        contexto['promedios'] = json.dumps(promedios)
        
        # Simulamos que Graphviz aún no nos manda la imagen
        contexto['grafo'] = None 
        if request.POST.get('actividad_txt'):
             actividad_sel = request.POST.get('actividad_txt')
             res_top = requests.get(f"{API_URL}/reportes/top-notas/{curso_seleccionado}/{actividad_sel}")
             if res_top.status_code == 200:
                 datos = res_top.json()
                 contexto['top_carnets'] = json.dumps(datos.get('carnets', []))
                 contexto['top_notas'] = json.dumps(datos.get('notas', []))
                 contexto['actividad_nombre'] = actividad_sel
        

    return render(request, 'tutor_reportes.html', contexto)

def vista_estudiante(request):
    if request.session.get('rol') != 'estudiante':
        return redirect('login')
        
    carnet = request.session.get('usuario')
    notas_totales = []
    error = None
    
    try:
        respuesta = requests.get(f"{API_URL}/estudiante/consultar/{carnet}")
        if respuesta.status_code == 200:
            notas_totales = respuesta.json()
        elif respuesta.status_code == 404:
            error = respuesta.json().get("mensaje", "No hay notas.")
        else:
            error = "Error al consultar las notas."
    except Exception as e:
        error = "Error de conexión con la API."
        
    contexto = {
        'notas': notas_totales,
        'error': error
    }
    return render(request, 'estudiante_consulta.html', contexto)
def descargar_reporte_admin(request):
    # Pedimos el XML al Backend
    response = requests.get(f"{API_URL}/admin/generar-reporte")

    # Reenviamos el archivo al navegador del Admin
    res = HttpResponse(response.content, content_type='application/xml')
    res['Content-Disposition'] = 'attachment; filename="reporte_final.xml"'
    return res