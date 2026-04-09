# 1. CLASE NODO (El que guarda la nota)
class Nodo:
    def __init__(self, fila: str, columna: str, valor: float):
        self.fila = fila          
        self.columna = columna    
        self.valor = valor        
        
        # Apuntadores para la lista ortogonal
        self.siguiente_fila = None
        self.siguiente_columna = None

    def __repr__(self) -> str:
        return f"[{self.fila}, {self.columna}: {self.valor}]"


# 2. CLASE MATRIZ DISPERSA (La estructura principal)
class MatrizDispersa:
    def __init__(self, nombre_curso: str):
        self.nombre_curso = nombre_curso
        self._filas = {}      
        self._columnas = {}   
        self._orden_filas = []
        self._orden_columnas = []

    def insertar(self, fila: str, columna: str, valor: float) -> None:
        if valor < 0 or valor > 100:
            return

        nuevo_nodo = Nodo(fila, columna, valor) # ¡Aquí es donde fallaba!

        if fila not in self._orden_filas:
            self._orden_filas.append(fila)
        if columna not in self._orden_columnas:
            self._orden_columnas.append(columna)

        # Inserción HORIZONTAL
        if fila not in self._filas:
            self._filas[fila] = nuevo_nodo
        else:
            actual = self._filas[fila]
            anterior = None
            while actual is not None and actual.columna < columna:
                anterior = actual
                actual = actual.siguiente_fila
            if anterior is None: 
                nuevo_nodo.siguiente_fila = self._filas[fila]
                self._filas[fila] = nuevo_nodo
            else:                
                nuevo_nodo.siguiente_fila = actual
                anterior.siguiente_fila = nuevo_nodo

        # Inserción VERTICAL
        if columna not in self._columnas:
            self._columnas[columna] = nuevo_nodo
        else:
            actual = self._columnas[columna]
            anterior = None
            while actual is not None and actual.fila < fila:
                anterior = actual
                actual = actual.siguiente_columna
            if anterior is None: 
                nuevo_nodo.siguiente_columna = self._columnas[columna]
                self._columnas[columna] = nuevo_nodo
            else:                
                nuevo_nodo.siguiente_columna = actual
                anterior.siguiente_columna = nuevo_nodo

    def obtener(self, fila: str, columna: str) -> float:
        if fila not in self._filas: return 0.0
        actual = self._filas[fila]
        while actual is not None:
            if actual.columna == columna: return actual.valor
            actual = actual.siguiente_fila
        return 0.0

    def promedio_por_actividad(self, act: str) -> float:
        if act not in self._filas: return 0.0
        suma = 0.0
        contador = 0
        actual = self._filas[act]
        while actual is not None:
            suma += actual.valor
            contador += 1
            actual = actual.siguiente_fila
        return suma / contador if contador > 0 else 0.0

    def notas_por_actividad(self, act: str) -> dict:
        resultados = {}
        if act in self._filas:
            actual = self._filas[act]
            while actual is not None:
                resultados[actual.columna] = actual.valor
                actual = actual.siguiente_fila
        return resultados

    def filas(self) -> list:
        return self._orden_filas

    def columnas(self) -> list:
        return self._orden_columnas