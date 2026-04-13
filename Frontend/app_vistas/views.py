from django.shortcuts import render, redirect
import requests

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

def tutor_horarios(request):
    if request.session.get('rol') != 'tutor':
        return redirect('login')

    contexto = {'xml_entrada': '', 'horarios': []}

    if request.method == 'POST':
        if 'btn_limpiar' in request.POST:
            return render(request, 'tutor_horarios.html', contexto)

        if 'btn_cargar' in request.POST and 'archivo_xml' in request.FILES:
            archivo = request.FILES['archivo_xml']
            contexto['xml_entrada'] = archivo.read().decode('utf-8')

        if 'btn_procesar' in request.POST:
            xml_contenido = request.POST.get('texto_xml')
            contexto['xml_entrada'] = xml_contenido
            try:
                # Enviamos el XML a la ruta de Flask que usa Regex y Pilas
                respuesta = requests.post(f"{API_URL}/tutor/horarios/cargar", data=xml_contenido.encode('utf-8'), headers={'Content-Type': 'application/xml'})
                if respuesta.status_code == 200:
                    contexto['horarios'] = respuesta.json().get("horarios", [])
            except:
                pass

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