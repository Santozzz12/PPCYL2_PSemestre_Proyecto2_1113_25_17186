from django.shortcuts import render, redirect
import requests

API_URL = "http://127.0.0.1:5001/api"

def login_view(request):
    if request.method == 'POST':
        usu = request.POST.get('usuario')
        contra = request.POST.get('contrasenia')

        try:
            # Preguntarle a Flask si el usuario existe
            respuesta = requests.post(f"{API_URL}/login", json={"usuario": usu, "contrasenia": contra})
            
            if respuesta.status_code == 200:
                datos = respuesta.json()
                rol = datos.get('rol')
                
                # Guardar datos en la "sesión" de Django para no perderlos al cambiar de página
                request.session['usuario'] = usu
                request.session['rol'] = rol
                
                # Redirecciones dinámicas según el rol
                if rol == 'admin':
                    return redirect('ver_usuarios') # Cambia esto por el name de tu url de admin
                elif rol == 'tutor':
                    return redirect('reportes') # Por ahora enviamos al tutor directo a reportes
                elif rol == 'estudiante':
                    return redirect('mis_notas') # Esta url la crearemos en el siguiente paso
            else:
                return render(request, 'login.html', {'error': "Usuario o contraseña incorrectos"})
        except Exception as e:
            return render(request, 'login.html', {'error': "Error de conexión con el servidor Flask"})

    # Si entra normal (GET), solo mostrar la pantalla
    return render(request, 'login.html')

def admin_dashboard(request):
    # Proteger la ruta para que solo entre el Admin
    if request.session.get('rol') != 'Admin':
        return redirect('login')

    contexto = {'xml_entrada': '', 'xml_salida': ''}

    if request.method == 'POST':
        # Acción 1: Limpiar datos
        if 'btn_limpiar' in request.POST:
            return render(request, 'admin.html', contexto)

        # Acción 2: Cargar el archivo de la computadora a la caja de texto
        if 'btn_cargar' in request.POST and 'archivo_xml' in request.FILES:
            archivo = request.FILES['archivo_xml']
            contexto['xml_entrada'] = archivo.read().decode('utf-8')

        # Acción 3: Enviar el texto al Backend (Flask)
        if 'btn_procesar' in request.POST:
            xml_contenido = request.POST.get('texto_xml')
            contexto['xml_entrada'] = xml_contenido

            try:
                # Petición a tu API de Flask
                respuesta = requests.post(
                    f"{API_URL}/admin/cargar_xml", 
                    data=xml_contenido.encode('utf-8'),
                    headers={'Content-Type': 'application/xml'}
                )
                
                if respuesta.status_code == 200:
                    datos = respuesta.json()
                    stats = datos.get('estadisticas', {})
                    
                    xml_out = f"""<?xml version="1.0"?>
<configuraciones_aplicadas>
    <tutores_cargados>{stats.get('tutores_cargados', 0)}</tutores_cargados>
    <estudiantes_cargados>{stats.get('estudiantes_cargados', 0)}</estudiantes_cargados>
    <asignaciones>
        <!-- Detalles irían aquí -->
    </asignaciones>
</configuraciones_aplicadas>"""
                    contexto['xml_salida'] = xml_out
                else:
                    contexto['xml_salida'] = f"Error del servidor: {respuesta.json()}"
            except Exception as e:
                contexto['xml_salida'] = f"No se pudo conectar a Flask: {str(e)}\n¿Está encendido el Servicio 2?"

    return render(request, 'admin.html', contexto)

def reporte_tutor(request):
    # 1. Obtener la lista de cursos disponibles para llenar el menú <select>
    lista_cursos = []
    try:
        resp_cursos = requests.get(f"{API_URL}/cursos")
        if resp_cursos.status_code == 200:
            lista_cursos = resp_cursos.json().get("cursos", [])
    except:
        pass

    # 2. Variables vacías por defecto (por si apenas entró a la página y no ha seleccionado nada)
    curso_seleccionado = None
    actividades = []
    promedios = []
    imagen_graphviz = ""

    # 3. Detectar si el tutor presionó el botón "Seleccionar"
    if request.method == 'POST':
        curso_seleccionado = request.POST.get('curso_select')

    # 4. Si YA seleccionó un curso, entonces sí hacemos las peticiones a Flask
    if curso_seleccionado:
        try:
            # Petición 1: Las gráficas (Chart.js / Plotly)
            respuesta = requests.get(f"{API_URL}/tutor/notas/promedio/{curso_seleccionado}")
            if respuesta.status_code == 200:
                datos = respuesta.json()
                actividades = datos.get("actividades", [])
                promedios = datos.get("promedios", [])

            # Petición 2: La imagen de Graphviz
            resp_grafo = requests.get(f"{API_URL}/tutor/reporte/graphviz/{curso_seleccionado}")
            if resp_grafo.status_code == 200:
                imagen_graphviz = resp_grafo.json().get("imagen_url", "")
        except:
            pass

    # 5. Enviamos todo al HTML
    contexto = {
        'cursos': lista_cursos,              # La lista para armar el menú desplegable
        'curso_actual': curso_seleccionado,  # El curso que eligió (para que la gráfica sepa de quién es)
        'actividades': actividades,
        'promedios': promedios,
        'grafo': imagen_graphviz
    }
    return render(request, 'tutor_reportes.html', contexto)
def mis_notas(request):
    # Sacamos el carnet de la sesión (del login)
    carnet = request.session.get('usuario') 
    curso_prueba = "770" # Mantenemos el curso de prueba por ahora
    notas_estudiante = []
    
    try:
        respuesta = requests.get(f"{API_URL}/estudiante/notas/{curso_prueba}/{carnet}")
        if respuesta.status_code == 200:
            notas_estudiante = respuesta.json().get("notas", [])
    except:
        pass
        
    contexto = {
        'carnet': carnet,
        'curso': curso_prueba,
        'notas': notas_estudiante
    }
    return render(request, 'mis_notas.html', contexto)
def ver_usuarios(request):
    # Pequeña validación de seguridad
    if request.session.get('rol') != 'admin':
        return redirect('login') # Si no es admin, lo pateamos al login

    usuarios_cargados = []
    try:
        respuesta = requests.get(f"{API_URL}/admin/usuarios")
        if respuesta.status_code == 200:
            usuarios_cargados = respuesta.json().get("usuarios", [])
    except:
        pass
        
    return render(request, 'ver_usuarios.html', {'usuarios': usuarios_cargados})

