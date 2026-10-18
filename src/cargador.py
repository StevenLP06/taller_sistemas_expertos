# -*- coding: utf-8 -*-
# La línea de arriba le dice a Python que este archivo usa codificación UTF-8,
# para que se puedan escribir tildes y la letra ñ sin problemas.

"""
cargador.py
-----------
Este módulo se encarga de LEER los archivos externos:
  1) La Base de Conocimiento (archivo .json con el catálogo de hechos y las reglas).
  2) Los casos de prueba (archivo .txt con los hechos iniciales de uno o varios casos).

También VALIDA la base de conocimiento, es decir, revisa que no tenga errores
(por ejemplo, una regla que usa un hecho que nunca fue declarado).
"""

# 'import json' trae el módulo estándar de Python que sabe leer archivos .json
# y convertirlos en diccionarios y listas de Python.
import json

# Lista con los cuatro tipos de hecho permitidos. La usamos para validar la base.
TIPOS_VALIDOS = ["observacion", "intermedio", "diagnostico", "recomendacion"]


def cargar_base_conocimiento(ruta):
    """Lee el archivo JSON de la base de conocimiento y devuelve un diccionario."""
    # 'open(...)' abre el archivo. "r" = solo lectura. encoding="utf-8" = para leer tildes.
    # 'with ... as archivo' cierra el archivo automáticamente cuando termina el bloque.
    with open(ruta, "r", encoding="utf-8") as archivo:
        # json.load convierte el texto JSON en un diccionario de Python.
        # Si el JSON está mal escrito, Python lanza un ValueError (error de valor).
        base = json.load(archivo)
    # Revisamos que la base tenga la estructura correcta (si hay error, se lanza ValueError).
    validar_base(base)
    # 'return' entrega el diccionario a quien llamó la función.
    return base


def validar_base(base):
    """Revisa la estructura de la base. Si encuentra un error lanza ValueError con un mensaje."""
    # La base debe tener las dos claves principales: "hechos" y "reglas".
    if "hechos" not in base or "reglas" not in base:
        # 'raise' lanza un error; el programa que nos llamó lo captura y muestra el mensaje.
        raise ValueError("El archivo debe tener las claves 'hechos' y 'reglas'.")

    # ---- 1) Validar el catálogo de hechos ----
    # .items() recorre el diccionario entregando pares (nombre, datos).
    for nombre, datos in base["hechos"].items():
        # .get("tipo") devuelve el tipo, o None si no existe. 'not in' pregunta si NO está en la lista.
        if datos.get("tipo") not in TIPOS_VALIDOS:
            raise ValueError("El hecho '" + nombre + "' tiene un tipo inválido. "
                             "Debe ser uno de: " + ", ".join(TIPOS_VALIDOS))
        # Cada hecho debe traer su descripción (el texto que se muestra al usuario).
        if "descripcion" not in datos:
            raise ValueError("El hecho '" + nombre + "' no tiene descripción.")

    # ---- 2) Validar cada regla ----
    ids_usados = []   # aquí guardamos los ids que ya vimos para detectar repetidos
    for regla in base["reglas"]:
        # Toda regla debe tener estos cuatro campos obligatorios.
        for campo in ["id", "nombre", "antecedentes", "consecuentes"]:
            if campo not in regla:
                raise ValueError("Una regla no tiene el campo '" + campo + "'.")

        # No pueden existir dos reglas con el mismo id.
        if regla["id"] in ids_usados:
            raise ValueError("El id de regla '" + regla["id"] + "' está repetido.")
        ids_usados.append(regla["id"])   # .append agrega el id al final de la lista

        # Una regla sin antecedentes se dispararía siempre; sin consecuentes no haría nada.
        if len(regla["antecedentes"]) == 0 or len(regla["consecuentes"]) == 0:
            raise ValueError("La regla " + regla["id"] + " no puede tener listas vacías.")

        # Valores por defecto: si la regla no trae prioridad usamos 5; si no trae explicación, texto vacío.
        if "prioridad" not in regla:
            regla["prioridad"] = 5
        if "explicacion" not in regla:
            regla["explicacion"] = ""

        # Todo hecho que aparezca en una regla debe estar declarado en el catálogo "hechos".
        # La suma de listas (+) junta antecedentes y consecuentes en una sola lista.
        for hecho in regla["antecedentes"] + regla["consecuentes"]:
            if hecho not in base["hechos"]:
                raise ValueError("La regla " + regla["id"] + " usa el hecho '" + hecho +
                                 "' que no está declarado en 'hechos'.")


def cargar_casos(ruta):
    """
    Lee un archivo .txt con uno o varios casos de prueba.
    Formato del archivo:
        [nombre_del_caso]    -> inicia un caso nuevo
        hecho                -> un hecho por línea
        # comentario         -> se ignora
    Devuelve un diccionario:  {"nombre_del_caso": ["hecho1", "hecho2", ...], ...}
    Si el archivo no tiene encabezados [..], todo se guarda en un caso llamado "caso_unico".
    """
    casos = {}                      # diccionario vacío donde iremos guardando los casos
    caso_actual = "caso_unico"      # nombre del caso al que pertenecen las líneas que se van leyendo

    with open(ruta, "r", encoding="utf-8") as archivo:
        # Recorremos el archivo línea por línea.
        for linea in archivo:
            linea = linea.strip()   # .strip() quita espacios y saltos de línea al inicio y al final

            # Línea vacía o comentario (empieza con #): se salta con 'continue'.
            if linea == "" or linea.startswith("#"):
                continue

            # Encabezado de caso: empieza con [ y termina con ]
            if linea.startswith("[") and linea.endswith("]"):
                caso_actual = linea[1:-1].strip()   # [1:-1] quita el primer y el último carácter
                if caso_actual not in casos:
                    casos[caso_actual] = []         # crea el caso con lista de hechos vacía
                continue

            # Si llegamos aquí, la línea es un hecho. Lo agregamos al caso actual.
            if caso_actual not in casos:
                casos[caso_actual] = []
            casos[caso_actual].append(linea)

    return casos
