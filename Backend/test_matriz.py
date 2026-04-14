import sys
sys.path.append('C:\\Users\\PC\\.gemini\\antigravity\\scratch\\Backend')
from matriz_dispersa import MatrizDispersa

m = MatrizDispersa('770')
m.insertar('Tarea 1', '1234', 100.0)
m.insertar('Parcial 1', '1234', 85.0)

print("Filas:", m.filas())
nota1 = m.obtener_nota('Tarea 1', '1234')
print("Nota1:", nota1)

if hasattr(m, 'obtener'):
    print("Has obtener")

