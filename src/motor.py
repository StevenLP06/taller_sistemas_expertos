# -*- coding: utf-8 -*-

"""
motor.py
--------
Motor de inferencia con ENCADENAMIENTO HACIA ADELANTE (forward chaining).
Es la evolución de motor_inferencia_avanzado() del código original.

Idea general: partimos de los hechos que da el usuario y vamos aplicando reglas
SI-ENTONCES; cada regla puede crear hechos nuevos que a su vez activan otras reglas,
hasta que ya no se pueda aplicar ninguna.

Cada vuelta del ciclo tiene tres pasos:
  1. RECONOCER : buscar las reglas aplicables (conjunto de conflicto).
  2. RESOLVER  : elegir UNA con la estrategia de resolución de conflictos.
  3. ACTUAR    : disparar la regla y agregar sus consecuentes a la memoria de trabajo.

MEMORIA DE TRABAJO: diccionario con esta forma
      { "nombre_del_hecho": {"ciclo": numero, "regla": "id_de_la_regla" o None} }
  - "ciclo": en qué vuelta del ciclo entró el hecho (0 = lo dio el usuario).
  - "regla": qué regla lo infirió (None si lo dio el usuario).

ESTRATEGIA DE RESOLUCIÓN DE CONFLICTOS (en este orden):
  1. Mayor PRIORIDAD de la regla.
  2. Mayor RECENCIA (el antecedente más recién agregado).
  3. Mayor ESPECIFICIDAD (más antecedentes).
  4. Orden en la base de conocimiento (desempate sin azar).
"""



def buscar_reglas_aplicables(reglas, memoria, disparadas):
    """Devuelve la lista de reglas que se pueden disparar en este momento."""
    aplicables = []                       
    for regla in reglas:                  
        if regla["id"] in disparadas:     
            continue                      
        antecedentes = set(regla["antecedentes"])   
        if antecedentes.issubset(memoria):
            aplicables.append(regla)      
    return aplicables



def recencia(regla, memoria):
    """La recencia de una regla es el ciclo del antecedente MÁS NUEVO."""
    mayor = 0                                         
    for antecedente in regla["antecedentes"]:         
        ciclo = memoria[antecedente]["ciclo"]         
        if ciclo > mayor:                             
            mayor = ciclo                             
    return mayor


def resolver_conflicto(aplicables, memoria):
    """
    Elige UNA regla de la lista 'aplicables'. Devuelve (regla_elegida, motivo).
    Filtra las candidatas criterio por criterio, hasta que quede una sola.
    """
    candidatas = aplicables                           
    motivo = "es la única regla aplicable"            
    if len(candidatas) == 1:                         
        return candidatas[0], motivo

    
    mayor = max(r["prioridad"] for r in candidatas)
    candidatas = [r for r in candidatas if r["prioridad"] == mayor]
    motivo = "mayor prioridad (" + str(mayor) + ")"

    
    if len(candidatas) > 1:
        mayor = max(recencia(r, memoria) for r in candidatas)
        candidatas = [r for r in candidatas if recencia(r, memoria) == mayor]
        motivo = "mayor recencia (antecedente del ciclo " + str(mayor) + ")"

    
    if len(candidatas) > 1:
        mayor = max(len(r["antecedentes"]) for r in candidatas)
        candidatas = [r for r in candidatas if len(r["antecedentes"]) == mayor]
        motivo = "mayor especificidad (" + str(mayor) + " antecedentes)"

    
    if len(candidatas) > 1:
        motivo = "empate en todos los criterios: primera en el orden de la base"

   
    return candidatas[0], motivo



def rastrear(hecho, memoria, reglas_por_id, camino):
    """
    Función RECURSIVA (se llama a sí misma). Recorre hacia atrás la memoria de trabajo
    y llena la lista 'camino' con los ids de las reglas que llevaron a 'hecho',
    en orden lógico: de la primera regla a la última.
    """
    regla_id = memoria[hecho]["regla"]      
    if regla_id is None:                      
        return
    regla = reglas_por_id[regla_id]           
    for antecedente in regla["antecedentes"]: 
        rastrear(antecedente, memoria, reglas_por_id, camino)
    if regla_id not in camino:                
        camino.append(regla_id)



def ejecutar_inferencia(base, hechos_iniciales):
    """
    Recibe la base de conocimiento y la lista de hechos iniciales.
    Devuelve un diccionario con: hechos_iniciales, memoria, pasos,
    diagnosticos, recomendaciones y advertencias.
    """
    reglas = base["reglas"]          
    catalogo = base["hechos"]        

    
    reglas_por_id = {}
    for regla in reglas:
        reglas_por_id[regla["id"]] = regla

   
    memoria = {}                     
    validos = []                     
    advertencias = []                
    for hecho in hechos_iniciales:
        if hecho not in catalogo:                              
            advertencias.append("Hecho desconocido ignorado: '" + hecho + "'")
        elif catalogo[hecho]["tipo"] != "observacion":         
            advertencias.append("'" + hecho + "' no es una observación (se infiere con reglas); se ignora.")
        elif hecho not in memoria:                           
            memoria[hecho] = {"ciclo": 0, "regla": None}       
            validos.append(hecho)

    
    disparadas = []                  
    pasos = []                      
    ciclo = 0                        
    while True:                      
        aplicables = buscar_reglas_aplicables(reglas, memoria, disparadas)
        if not aplicables:           
            break                    

        ciclo = ciclo + 1            

        
        conflicto = []
        for r in aplicables:
            conflicto.append(r["id"] + " " + r["nombre"] +
                             "  [prioridad=" + str(r["prioridad"]) +
                             ", recencia=" + str(recencia(r, memoria)) +
                             ", especificidad=" + str(len(r["antecedentes"])) + "]")

        
        elegida, motivo = resolver_conflicto(aplicables, memoria)

        
        nuevos = []                                   
        for consecuente in elegida["consecuentes"]:
            if consecuente not in memoria:            
                memoria[consecuente] = {"ciclo": ciclo, "regla": elegida["id"]}
                nuevos.append(consecuente)
        disparadas.append(elegida["id"])              

        
        pasos.append({"ciclo": ciclo, "conflicto": conflicto, "regla": elegida,
                      "motivo": motivo, "nuevos": nuevos})

    
    diagnosticos = []
    recomendaciones = []
    for hecho in memoria:                             
        tipo = catalogo[hecho]["tipo"]
        if tipo == "diagnostico":
            diagnosticos.append(hecho)
        if tipo == "recomendacion":
            regla = reglas_por_id[memoria[hecho]["regla"]]   
            camino = []                                      
            rastrear(hecho, memoria, reglas_por_id, camino)
            recomendaciones.append({"hecho": hecho,
                                    "texto": catalogo[hecho]["descripcion"],
                                    "prioridad": regla["prioridad"],
                                    "ciclo": memoria[hecho]["ciclo"],
                                    "camino": camino})

    
   
    
    recomendaciones.sort(key=lambda rec: (-rec["prioridad"], rec["ciclo"]))

    return {"hechos_iniciales": validos, "memoria": memoria, "pasos": pasos,
            "diagnosticos": diagnosticos, "recomendaciones": recomendaciones,
            "advertencias": advertencias}



def formatear_inicio(resultado, base):
    """Texto con los hechos iniciales y las advertencias."""
    texto = "=== HECHOS INICIALES (Memoria de Trabajo al comenzar) ===\n"   
    if resultado["hechos_iniciales"]:
        for hecho in resultado["hechos_iniciales"]:
            texto += "  - " + hecho + ": " + base["hechos"][hecho]["descripcion"] + "\n"
    else:
        texto += "  (ninguno)\n"
    for aviso in resultado["advertencias"]:
        texto += "  ! " + aviso + "\n"
    return texto


def formatear_paso(paso):
    """Texto de UN paso: conjunto de conflicto, regla elegida, motivo y hechos nuevos."""
    regla = paso["regla"]
    texto = "\n--- PASO " + str(paso["ciclo"]) + " ---\n"      
    texto += "Conjunto de conflicto (reglas aplicables):\n"
    for linea in paso["conflicto"]:
        texto += "   * " + linea + "\n"
    texto += "Regla seleccionada: " + regla["id"] + " - " + regla["nombre"] + "\n"
    texto += "Motivo: " + paso["motivo"] + "\n"
    texto += "Si " + " Y ".join(regla["antecedentes"]) + "\n"      
    texto += "Entonces " + ", ".join(regla["consecuentes"]) + "\n"
    if regla["explicacion"] != "":
        texto += "Porque: " + regla["explicacion"] + "\n"
    if paso["nuevos"]:
        texto += "Hechos nuevos en la memoria: " + ", ".join(paso["nuevos"]) + "\n"
    else:
        texto += "No se agregaron hechos nuevos.\n"
    return texto


def formatear_resultado(resultado, base):
    """Texto final: diagnósticos y recomendación principal con su cadena de razonamiento."""
    texto = "\n=========== RESULTADO FINAL ===========\n"
    texto += "Reglas disparadas: " + str(len(resultado["pasos"])) + "\n"

    texto += "\nDIAGNÓSTICO(S):\n"
    if resultado["diagnosticos"]:
        for dx in resultado["diagnosticos"]:
            texto += "  - " + base["hechos"][dx]["descripcion"] + "\n"
    else:
        texto += "  (ninguno)\n"

    
    if not resultado["recomendaciones"]:
        texto += "\nRECOMENDACIÓN:\n"
        texto += "  El sistema no pudo concluir un diagnóstico con los datos dados.\n"
        texto += "  Agregue más observaciones (por ejemplo, pruebe ping al router,\n"
        texto += "  ping a 8.8.8.8 y ping a google.com) y ejecute de nuevo.\n"
        return texto

   
    principal = resultado["recomendaciones"][0]
    texto += "\nRECOMENDACIÓN PRINCIPAL (prioridad " + str(principal["prioridad"]) + "):\n"
    texto += "  " + principal["texto"] + "\n"
    texto += "  Cadena de razonamiento: " + " -> ".join(principal["camino"]) + "\n"

    
    if len(resultado["recomendaciones"]) > 1:
        texto += "\nOTRAS RECOMENDACIONES (por orden de prioridad):\n"
        for rec in resultado["recomendaciones"][1:]:
            texto += "  - [prioridad " + str(rec["prioridad"]) + "] " + rec["texto"] + "\n"
            texto += "    Cadena: " + " -> ".join(rec["camino"]) + "\n"
    return texto