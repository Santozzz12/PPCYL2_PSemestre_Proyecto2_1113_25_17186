# Backend/matriz_dispersa.py

class Nodo:
    def __init__(self, fila: str, columna: str, valor: float):
        self.fila = fila          
        self.columna = columna    
        self.valor = valor        
        self.siguiente_fila = None    # Nodo a la derecha
        self.siguiente_columna = None # Nodo abajo

class MatrizDispersa:
    def __init__(self, nombre_curso: str):
        self.nombre_curso = nombre_curso
        self._filas = {}      # Diccionario de cabeceras de filas
        self._columnas = {}   # Diccionario de cabeceras de columnas
        self._orden_filas = []
        self._orden_columnas = []

    def insertar(self, fila: str, columna: str, valor: float) -> None:
        if valor < 0 or valor > 100:
            return

        nuevo_nodo = Nodo(fila, columna, valor)
        print(f"DEBUG: Insertando en Matriz -> {fila}, {columna}: {valor}")

        if fila not in self._orden_filas:
            self._orden_filas.append(fila)
        if columna not in self._orden_columnas:
            self._orden_columnas.append(columna)

        # Inserción HORIZONTAL (Fila)
        if fila not in self._filas:
            self._filas[fila] = nuevo_nodo
        else:
            actual = self._filas[fila]
            anterior = None
            while actual is not None and str(actual.columna) < str(columna):
                anterior = actual
                actual = actual.siguiente_fila
            
            if anterior is None: 
                nuevo_nodo.siguiente_fila = self._filas[fila]
                self._filas[fila] = nuevo_nodo
            else:                
                nuevo_nodo.siguiente_fila = actual
                anterior.siguiente_fila = nuevo_nodo

        # Inserción VERTICAL (Columna)
        if columna not in self._columnas:
            self._columnas[columna] = nuevo_nodo
        else:
            actual = self._columnas[columna]
            anterior = None
            while actual is not None and str(actual.fila) < str(fila):
                anterior = actual
                actual = actual.siguiente_columna
            
            if anterior is None: 
                nuevo_nodo.siguiente_columna = self._columnas[columna]
                self._columnas[columna] = nuevo_nodo
            else:                
                nuevo_nodo.siguiente_columna = actual
                anterior.siguiente_columna = nuevo_nodo

    # 🎯 ESTA ES LA FUNCIÓN QUE CORREGIMOS PARA EL ESTUDIANTE
    def obtener_nota(self, actividad_nombre, carnet_buscado):
        act_target = str(actividad_nombre).strip().lower()
        carnet_target = str(carnet_buscado).strip()

        # Buscamos la fila en el diccionario _filas
        target_key = None
        for key in self._filas.keys():
            if str(key).strip().lower() == act_target:
                target_key = key
                break
        
        if target_key:
            # Recorremos la fila horizontalmente usando siguiente_fila
            actual = self._filas[target_key]
            while actual is not None:
                if str(actual.columna).strip() == carnet_target:
                    return actual.valor
                actual = actual.siguiente_fila
        return 0

    def filas(self) -> list:
        return self._orden_filas