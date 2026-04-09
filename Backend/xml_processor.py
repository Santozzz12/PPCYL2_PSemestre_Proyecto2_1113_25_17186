import re

# 1. Implementación de la Pila requerida por el proyecto
class Pila:
    def __init__(self):
        self._datos = []

    def push(self, item):
        """Agrega un elemento a la cima de la pila."""
        self._datos.append(item)

    def pop(self):
        """Retira y retorna el elemento en la cima de la pila."""
        if not self.esta_vacia():
            return self._datos.pop()
        return None

    def peek(self):
        """Retorna el elemento en la cima sin retirarlo."""
        if not self.esta_vacia():
            return self._datos[-1]
        return None

    def esta_vacia(self) -> bool:
        """Verifica si la pila no tiene elementos."""
        return len(self._datos) == 0

    def __len__(self):
        return len(self._datos)

# 2. Función de extracción con Regex y Pila
def extraer_horario_con_pila(texto: str) -> tuple:
    """
    Analiza una cadena de texto, extrae el horario usando Regex y lo apila.
    Retorna una tupla (hora_inicio, hora_fin) o None si no hay coincidencias válidas.
    """
    pila_horarios = Pila()
    
    # Expresión regular para buscar exactamente el formato:
    # "HorarioI: HH:mm HorarioF: HH:mm"
    patron = r"Horariol:\s*(\d{2}:\d{2})\s*HorarioF:\s*(\d{2}:\d{2})"
    
    # Encontramos todas las coincidencias en el texto
    coincidencias = re.findall(patron, texto)
    
    # El requerimiento exige utilizar estructuras de pilas
    for coincidencia in coincidencias:
        # coincidencia será una tupla, ej: ('09:40', '10:30')
        pila_horarios.push(coincidencia)
        
    # Extraemos de la pila el último horario válido encontrado en la cadena
    if not pila_horarios.esta_vacia():
        horario_valido = pila_horarios.pop()
        return horario_valido
        
    return None

# ==========================================
# PRUEBA RÁPIDA (Se puede borrar después)
# ==========================================
if __name__ == "__main__":
    cadena_prueba = "Mi horario de curso es Horariol: 09:40 HorarioF: 10:30 y el resto se descarta"
    resultado = extraer_horario_con_pila(cadena_prueba)
    
    if resultado:
        print(f"Horario extraído con éxito -> Inicio: {resultado[0]}, Fin: {resultado[1]}")
    else:
        print("No se encontró un horario válido en la cadena.")