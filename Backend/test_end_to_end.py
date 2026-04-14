import requests

xml_admin = """<configuracion>
    <cursos>
        <curso codigo="770"/>
    </cursos>
    <estudiantes>
        <estudiante carnet="1234" contrasenia="1234">Test Est</estudiante>
    </estudiantes>
    <asignaciones>
        <estudiante_curso codigo="770">1234</estudiante_curso>
    </asignaciones>
</configuracion>"""

resp1 = requests.post('http://127.0.0.1:5001/api/admin/cargar_xml', data=xml_admin.encode('utf-8'))
print("Admin Load:", resp1.text)

resp_rep = requests.get('http://127.0.0.1:5001/api/admin/generar-reporte')
print("Reporte:\n", resp_rep.text)
