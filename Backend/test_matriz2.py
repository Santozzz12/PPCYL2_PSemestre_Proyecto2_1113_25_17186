import sys
sys.path.append('C:\\Users\\PC\\.gemini\\antigravity\\scratch\\Backend')
from matriz_dispersa import MatrizDispersa

m = MatrizDispersa('770')
m.insertar('Tarea 1', '1234', 100.0)

print(m._filas['Tarea 1'].columna)
print(type(m._filas['Tarea 1'].columna))

# Simulated obtener_nota:
carnet_buscado = "1234"
print(m.obtener_nota('Tarea 1', carnet_buscado))
