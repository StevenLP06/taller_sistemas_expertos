# -*- coding: utf-8 -*-

"""
main.py - Sistema Experto: Diagnóstico de fallas de red / Internet
-------------------------------------------------------------------
Está escrito igual que el código de ejemplo del curso (motor_inferencia_avanzado):
una función con un ciclo while, hechos guardados en un set, reglas con
"antecedentes" y "consecuentes", y mensajes con print.

Lo que cambió respecto al ejemplo:
  1. Las reglas YA NO están escritas aquí: se leen del archivo conocimiento/red_fallas.json
  2. Los hechos iniciales vienen de un archivo (casos/casos.txt) o se preguntan por teclado
  3. La resolución de conflictos usa: prioridad -> recencia -> especificidad -> orden en la base
  4. Al final se entrega el diagnóstico y la recomendación del sistema experto

Para ejecutarlo:   python main.py
"""

import os                      # para armar las rutas de los archivos
from src import cargador       # nuestro módulo que lee el JSON y el archivo de casos

# Carpeta donde está este archivo main.py
CARPETA = os.path.dirname(os.path.abspath(__file__))
# Rutas de los dos archivos externos
RUTA_KB = os.path.join(CARPETA, "conocimiento", "red_fallas.json")
RUTA_CASOS = os.path.join(CARPETA, "casos", "casos.txt")


# ======================================================================
# FUNCIÓN AUXILIAR: recencia de una regla
# ======================================================================
def calcular_recencia(regla, ciclo_de_hecho):
    # La recencia de una regla es el ciclo del antecedente MÁS NUEVO.
    # (ciclo 0 = hecho dado por el usuario; ciclo 1, 2, 3... = hecho inferido en ese paso)
    mayor = 0
    for antecedente in regla["antecedentes"]:
        if ciclo_de_hecho[antecedente] > mayor:
            mayor = ciclo_de_hecho[antecedente]
    return mayor


# ======================================================================
# MOTOR DE INFERENCIA (igual que motor_inferencia_avanzado del ejemplo)
# ======================================================================
def motor_inferencia_avanzado(datos_iniciales, reglas, catalogo):
    # Convertir los datos iniciales a hechos (set = conjunto sin repetidos).
    # Solo se aceptan hechos que existan en el catálogo de la base de conocimiento.
    hechos = set()
    ciclo_de_hecho = {}      # en qué paso entró cada hecho (0 = dato inicial)
    regla_de_hecho = {}      # qué regla (posición en la lista) infirió cada hecho
    for dato in datos_iniciales:
        if dato in catalogo and catalogo[dato]["tipo"] == "observacion":
            hechos.add(dato)
            ciclo_de_hecho[dato] = 0
        else:
            print(f"Aviso: '{dato}' no es una observación válida y se ignora.")

    reglas_disparadas = set()    # posiciones de las reglas que ya se dispararon
    ciclo = 0                    # número de paso (cuenta cuántas reglas se han disparado)

    while True:
        # ---------- 1) Buscar las reglas aplicables (conjunto de conflicto) ----------
        reglas_aplicables = []
        for i, regla in enumerate(reglas):
            # a) No repetir reglas ya disparadas
            if i not in reglas_disparadas:
                # Verificar si la regla se aplica (todos los antecedentes son hechos)
                antecedentes = set(regla["antecedentes"])
                if antecedentes.issubset(hechos):
                    reglas_aplicables.append((i, regla))

        # Mostrar el conjunto de conflictos (reglas aplicables)
        print("\nConjunto de conflictos (Reglas aplicables):")
        if reglas_aplicables:
            for _, regla in reglas_aplicables:
                print(f"- {regla['id']} {regla['nombre']} "
                      f"[prioridad={regla['prioridad']}, "
                      f"recencia={calcular_recencia(regla, ciclo_de_hecho)}, "
                      f"especificidad={len(regla['antecedentes'])}]")
        else:
            print("- Ninguna")

        if not reglas_aplicables:
            break  # No hay reglas aplicables, detener la inferencia

        ciclo = ciclo + 1

        # ---------- 2) *****  Resolver conflicto  ***** ----------
        # Se ordena de mayor a menor usando tres valores, en este orden:
        #   b) mayor PRIORIDAD de la regla (las más importantes o más fáciles de verificar primero)
        #   c) mayor RECENCIA (la que usa el hecho recién agregado)
        #   d) mayor ESPECIFICIDAD (la que tiene más antecedentes)
        # Si hay empate en los tres, sort() deja primero a la que viene primero en la base
        # (así NO se usa el azar y el resultado siempre es el mismo).
        reglas_aplicables.sort(
            key=lambda item: (item[1]["prioridad"],
                              calcular_recencia(item[1], ciclo_de_hecho),
                              len(item[1]["antecedentes"])),
            reverse=True)

        # Seleccionar la primera regla aplicable después de la resolución de conflictos
        indice_regla_seleccionada, regla_seleccionada = reglas_aplicables[0]

        # Mostrar la regla seleccionada
        print(f"\nPaso {ciclo} - Regla seleccionada: {regla_seleccionada['id']} {regla_seleccionada['nombre']}")
        print(f"   Si {' Y '.join(regla_seleccionada['antecedentes'])}")
        print(f"   Entonces {', '.join(regla_seleccionada['consecuentes'])}")
        print(f"   Porque: {regla_seleccionada['explicacion']}")

        # ---------- 3) Disparar la regla y agregar nuevos hechos (consecuentes) ----------
        reglas_disparadas.add(indice_regla_seleccionada)

        nuevos_hechos_inferidos_por_regla = []
        for consecuente in regla_seleccionada["consecuentes"]:
            if consecuente not in hechos:
                hechos.add(consecuente)
                ciclo_de_hecho[consecuente] = ciclo                  # anotamos en qué paso nació
                regla_de_hecho[consecuente] = indice_regla_seleccionada   # y qué regla lo produjo
                nuevos_hechos_inferidos_por_regla.append(consecuente)

        if nuevos_hechos_inferidos_por_regla:
            print(f"Regla disparada: {regla_seleccionada['nombre']}. Nuevos hechos agregados: {', '.join(nuevos_hechos_inferidos_por_regla)}")
        else:
            print(f"Regla disparada: {regla_seleccionada['nombre']}. No se agregaron nuevos hechos (ya existían o la regla no infiere nuevos).")

    # Devolvemos los hechos finales y los dos diccionarios que sirven para explicar el resultado
    return hechos, ciclo_de_hecho, regla_de_hecho


# ======================================================================
# RESULTADO: diagnóstico y recomendación del sistema experto
# ======================================================================
def mostrar_resultado(hechos, ciclo_de_hecho, regla_de_hecho, reglas, catalogo):
    print("\n=========== RESULTADO FINAL ===========")

    # Diagnósticos: los hechos de tipo "diagnostico" que se infirieron
    print("\nDIAGNÓSTICO(S):")
    hay_diagnostico = False
    for hecho in hechos:
        if catalogo[hecho]["tipo"] == "diagnostico":
            print(f"- {catalogo[hecho]['descripcion']}")
            hay_diagnostico = True
    if not hay_diagnostico:
        print("- (ninguno)")

    # Recomendaciones: los hechos de tipo "recomendacion".
    # Se guardan como (-prioridad, ciclo, hecho, id_regla) para ordenar: primero la de mayor prioridad
    # (el signo menos invierte el orden) y, si empatan, la que se obtuvo antes.
    recomendaciones = []
    for hecho in hechos:
        if catalogo[hecho]["tipo"] == "recomendacion":
            regla = reglas[regla_de_hecho[hecho]]
            recomendaciones.append((-regla["prioridad"], ciclo_de_hecho[hecho], hecho, regla["id"]))
    recomendaciones.sort()

    if not recomendaciones:
        print("\nRECOMENDACIÓN:")
        print("El sistema no pudo concluir un diagnóstico con los datos dados.")
        print("Agregue más observaciones (ping al router, ping a 8.8.8.8, ping a google.com) y ejecute de nuevo.")
        return

    prioridad, ciclo, hecho, id_regla = recomendaciones[0]
    print(f"\nRECOMENDACIÓN PRINCIPAL (prioridad {-prioridad}, regla {id_regla}):")
    print(catalogo[hecho]["descripcion"])

    if len(recomendaciones) > 1:
        print("\nOTRAS RECOMENDACIONES (por orden de prioridad):")
        for prioridad, ciclo, hecho, id_regla in recomendaciones[1:]:
            print(f"- [prioridad {-prioridad}] {catalogo[hecho]['descripcion']}")


# ======================================================================
# Ejecutar un caso completo (motor + resultado)
# ======================================================================
def ejecutar_caso(nombre, datos_iniciales, base):
    print("\n" + "=" * 70)
    print(f"--- Ejecutando motor de inferencia para: {nombre} ---")
    print("=" * 70)
    print("Hechos iniciales:", datos_iniciales)
    hechos, ciclo_de_hecho, regla_de_hecho = motor_inferencia_avanzado(
        datos_iniciales, base["reglas"], base["hechos"])
    mostrar_resultado(hechos, ciclo_de_hecho, regla_de_hecho, base["reglas"], base["hechos"])


# ======================================================================
# Preguntar los hechos al usuario por teclado
# ======================================================================
def preguntar_hechos(base):
    print("Responda s (sí) o n (no):\n")
    datos = []
    for nombre, info in base["hechos"].items():
        if info["tipo"] == "observacion":
            respuesta = input(f"  ¿{info['descripcion']}? (s/n): ").strip().lower()
            if respuesta == "s":
                datos.append(nombre)
    return datos


# ======================================================================
# PROGRAMA PRINCIPAL
# ======================================================================
def main():
    # Cargar la base de conocimiento desde el archivo externo
    base = cargador.cargar_base_conocimiento(RUTA_KB)
    print(f"Base de conocimiento cargada: {base['nombre']} ({len(base['reglas'])} reglas)")

    print("\n¿Qué desea hacer?")
    print("  1) Ejecutar un caso del archivo casos/casos.txt")
    print("  2) Ingresar los hechos a mano (preguntas s/n)")
    print("  3) Abrir la interfaz gráfica")
    opcion = input("Opción: ").strip()

    if opcion == "1":
        casos = cargador.cargar_casos(RUTA_CASOS)       # diccionario {nombre_caso: [hechos]}
        nombres = list(casos.keys())
        print("\nCasos disponibles:")
        for numero, nombre in enumerate(nombres, start=1):
            print(f"  {numero}) {nombre}")
        print("  0) Ejecutar TODOS los casos")
        eleccion = input("Caso: ").strip()
        if eleccion == "0":
            for nombre in nombres:
                ejecutar_caso(nombre, casos[nombre], base)
        elif eleccion.isdigit() and 1 <= int(eleccion) <= len(nombres):
            nombre = nombres[int(eleccion) - 1]
            ejecutar_caso(nombre, casos[nombre], base)
        else:
            print("Opción no válida.")

    elif opcion == "2":
        datos = preguntar_hechos(base)
        ejecutar_caso("Caso ingresado por el usuario", datos, base)

    elif opcion == "3":
        from src import interfaz          # se importa aquí para no exigir tkinter en las otras opciones
        interfaz.iniciar_interfaz(RUTA_KB)

    else:
        print("Opción no válida.")


# Solo se ejecuta main() cuando corremos "python main.py"
if __name__ == "__main__":
    main()
