# -*- coding: utf-8 -*-
"""
interfaz.py
-----------
Interfaz gráfica simple hecha con Tkinter (viene incluido con Python).

Qué permite:
  - Cargar la Base de Conocimiento desde un archivo .json
  - Ingresar hechos iniciales: marcando casillas O cargando un archivo de casos (.txt)
  - Ejecutar la inferencia y verla PASO A PASO (botón "Siguiente paso")
  - Ver el diagnóstico y la recomendación final

Está hecha solo con funciones (sin clases). Las variables que cambian mientras
se usa el programa se guardan en el diccionario 'estado'.
"""

# 'tkinter' es la librería de ventanas. Se le pone el apodo 'tk' para escribir menos.
import tkinter as tk

# 'ttk' trae widgets más modernos; aquí lo usamos para el menú desplegable (Combobox).
from tkinter import ttk

# filedialog = ventanas para elegir archivos; messagebox = ventanas de aviso;
# scrolledtext = cuadro de texto con barra de desplazamiento.
from tkinter import filedialog, messagebox, scrolledtext

# Importamos nuestros módulos de la carpeta src/
# Esto permite ejecutar el archivo directamente o desde la carpeta del proyecto.
import os
import sys

CARPETA_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if CARPETA_PROYECTO not in sys.path:
    sys.path.insert(0, CARPETA_PROYECTO)

from src import cargador, motor


def iniciar_interfaz(ruta_kb_inicial=None):
    """Crea la ventana, sus botones y la deja funcionando hasta que el usuario la cierre."""

    # Ventana principal
    ventana = tk.Tk()
    ventana.title("Sistema Experto - Diagnóstico de fallas de red / Internet")
    ventana.geometry("1150x680")

    # Diccionario con los datos que cambian mientras se usa el programa
    estado = {
        "base": None,              # base de conocimiento cargada (None = todavía no hay)
        "ids_observaciones": [],    # nombres de los hechos que se muestran en la lista (mismo orden)
        "casos": {},                # casos leídos del archivo de casos: {nombre: [hechos]}
        "resultado": None,          # resultado de la última inferencia
        "paso_actual": 0,            # cuántos pasos se han mostrado ya
    }

    # Construcción de los elementos visuales (widgets)
    # Frame = un contenedor (caja) para agrupar elementos. Este agrupa los botones.
    marco_botones = tk.Frame(ventana)
    marco_botones.pack(fill="x", padx=10, pady=8)

    # Label = texto fijo. Aquí muestra qué base de conocimiento está cargada.
    etiqueta_kb = tk.Label(ventana, text="Base de conocimiento: (ninguna cargada)", anchor="w")
    etiqueta_kb.pack(fill="x", padx=10)

    # Contenedor central: a la izquierda la lista de hechos, a la derecha los resultados.
    marco_central = tk.Frame(ventana)
    marco_central.pack(fill="both", expand=True, padx=10, pady=8)

    # ----- Panel izquierdo: lista de observaciones -----
    # LabelFrame = contenedor con título.
    marco_izq = tk.LabelFrame(marco_central, text="Hechos iniciales (seleccione lo que observa)")
    marco_izq.pack(side="left", fill="y")

    # Listbox = lista de opciones. selectmode=MULTIPLE permite marcar varias a la vez.
    # exportselection=False evita que la selección se pierda al hacer clic en otros elementos.
    lista = tk.Listbox(marco_izq, selectmode=tk.MULTIPLE, width=62, height=28, exportselection=False)

    # Scrollbar = barra de desplazamiento vertical, conectada a la lista con command=lista.yview.
    barra = tk.Scrollbar(marco_izq, command=lista.yview)
    lista.config(yscrollcommand=barra.set)  # la lista le avisa a la barra cuando se mueve
    barra.pack(side="right", fill="y")
    lista.pack(side="left", fill="y")

    # ----- Panel derecho: cuadro de texto con los resultados -----
    marco_der = tk.LabelFrame(marco_central, text="Resultados de la inferencia")
    marco_der.pack(side="right", fill="both", expand=True, padx=(10, 0))

    # ScrolledText = cuadro de texto con barra. wrap="word" parte las líneas en espacios, no a mitad de palabra.
    texto = scrolledtext.ScrolledText(marco_der, wrap="word", font=("Courier", 10))
    texto.pack(fill="both", expand=True)

    # Funciones que se ejecutan al presionar los botones
    def escribir(mensaje):
        """Agrega una línea de texto al final del cuadro de resultados."""
        texto.insert(tk.END, mensaje + "\n")  # tk.END = al final del texto
        texto.see(tk.END)  # baja el scroll para ver lo último escrito

    def poner_base(ruta):
        """Carga la base de conocimiento y llena la lista con las observaciones."""
        try:
            base = cargador.cargar_base_conocimiento(ruta)
        except (ValueError, OSError) as error:
            # Si el archivo no existe (OSError) o está mal armado (ValueError) mostramos un aviso.
            messagebox.showerror("Error al cargar la base", str(error))
            return

        estado["base"] = base  # guardamos la base en el estado
        estado["resultado"] = None  # se borra cualquier resultado anterior
        estado["ids_observaciones"] = []
        lista.delete(0, tk.END)  # vaciamos la lista visual

        for nombre, datos in base["hechos"].items():
            if datos["tipo"] == "observacion":  # solo las observaciones se ofrecen al usuario
                lista.insert(tk.END, datos["descripcion"])  # se muestra la descripción en la lista
                estado["ids_observaciones"].append(nombre)  # y se recuerda el nombre del hecho

        # .config(text=...) cambia el texto de la etiqueta.
        nombre_base = base.get("nombre", ruta)
        etiqueta_kb.config(
            text=f"Base de conocimiento: {nombre_base}  |  {len(base['reglas'])} reglas  |  {ruta}"
        )
        texto.delete("1.0", tk.END)  # "1.0" = inicio del texto (línea 1, carácter 0)
        escribir(f"Base de conocimiento cargada: {len(base['reglas'])} reglas.")
        escribir("Seleccione los hechos observados (o cargue el archivo de casos) y presione 'Ejecutar'.")

    def cargar_kb():
        """Botón 1: abre un explorador de archivos para elegir otra base .json."""
        ruta = filedialog.askopenfilename(
            title="Seleccione la base de conocimiento",
            filetypes=[("Base de conocimiento JSON", "*.json")]
        )
        if ruta:  # si el usuario canceló, ruta viene vacía
            poner_base(ruta)

    def marcar_hechos(hechos):
        """Marca en la lista los hechos recibidos (y avisa de los que no existan)."""
        lista.selection_clear(0, tk.END)  # primero desmarca todo
        desconocidos = []

        for hecho in hechos:
            if hecho in estado["ids_observaciones"]:
                posicion = estado["ids_observaciones"].index(hecho)  # posición del hecho en la lista
                lista.selection_set(posicion)  # lo marca
            else:
                desconocidos.append(hecho)

        if desconocidos:
            escribir("  ! Hechos no reconocidos (ignorados): " + ", ".join(desconocidos))

    def cargar_casos_archivo():
        """Botón 2: carga el archivo de casos y llena el menú desplegable."""
        if estado["base"] is None:
            messagebox.showwarning("Falta la base", "Primero cargue la base de conocimiento.")
            return

        ruta = filedialog.askopenfilename(
            title="Seleccione el archivo de casos",
            filetypes=[("Casos", "*.txt")]
        )
        if not ruta:
            return

        try:
            casos = cargador.cargar_casos(ruta)
        except OSError as error:
            messagebox.showerror("Error al cargar los casos", str(error))
            return

        estado["casos"] = casos
        menu_casos["values"] = list(casos.keys())  # llena el menú con los nombres de los casos
        menu_casos.set("")  # deja el menú sin selección
        escribir(f"\nArchivo de casos cargado: {ruta} ({len(casos)} casos).")
        escribir("Elija un caso en el menú desplegable.")

    def elegir_caso(evento=None):
        """Se ejecuta cuando el usuario elige un caso del menú desplegable."""
        nombre = menu_casos.get()  # nombre del caso elegido
        if nombre in estado["casos"]:
            marcar_hechos(estado["casos"][nombre])  # marca sus hechos en la lista
            escribir(f"\nCaso '{nombre}' cargado. Presione 'Ejecutar'.")

    def ejecutar():
        """Botón 3: corre el motor de inferencia con los hechos marcados."""
        if estado["base"] is None:
            messagebox.showwarning("Falta la base", "Primero cargue la base de conocimiento.")
            return

        # curselection() = posiciones marcadas
        hechos = [estado["ids_observaciones"][i] for i in lista.curselection()]
        if not hechos:
            messagebox.showwarning("Sin hechos", "Seleccione al menos un hecho observado.")
            return

        resultado = motor.ejecutar_inferencia(estado["base"], hechos)  # ¡aquí corre el motor!
        estado["resultado"] = resultado
        estado["paso_actual"] = 0  # aún no se ha mostrado ningún paso

        texto.delete("1.0", tk.END)  # limpiamos el cuadro de resultados
        escribir(motor.formatear_inicio(resultado, estado["base"]))

        if not resultado["pasos"]:
            # No se disparó ninguna regla: mostramos de una vez el resultado final.
            escribir(motor.formatear_resultado(resultado, estado["base"]))
        else:
            escribir(
                f"Inferencia lista ({len(resultado['pasos'])} reglas se dispararán). "
                "Presione 'Siguiente paso'."
            )

    def siguiente_paso():
        """Botón 'Siguiente paso': muestra un paso más de la inferencia."""
        resultado = estado["resultado"]
        if resultado is None:
            messagebox.showinfo("Sin ejecución", "Primero presione 'Ejecutar'.")
            return
        if estado["paso_actual"] >= len(resultado["pasos"]):
            messagebox.showinfo("Fin", "Ya se mostraron todos los pasos.")
            return

        # Mostramos el paso número 'paso_actual' (las listas empiezan en la posición 0).
        escribir(motor.formatear_paso(resultado["pasos"][estado["paso_actual"]]))
        estado["paso_actual"] += 1

        # Si ya se mostraron todos los pasos, se muestra el resultado final.
        if estado["paso_actual"] == len(resultado["pasos"]):
            escribir(motor.formatear_resultado(resultado, estado["base"]))

    def mostrar_todo():
        """Botón 'Mostrar todo': muestra de una vez los pasos que faltan."""
        if estado["resultado"] is None:
            messagebox.showinfo("Sin ejecución", "Primero presione 'Ejecutar'.")
            return

        while estado["paso_actual"] < len(estado["resultado"]["pasos"]):
            siguiente_paso()

    def limpiar():
        """Botón 'Limpiar': desmarca la lista y borra los resultados."""
        lista.selection_clear(0, tk.END)
        estado["resultado"] = None
        estado["paso_actual"] = 0
        texto.delete("1.0", tk.END)

    # Botones y menú desplegable (command = función que se ejecuta al hacer clic)
    def crear_boton(nombre, funcion):
        tk.Button(marco_botones, text=nombre, command=funcion).pack(side="left", padx=3)

    crear_boton("1. Cargar base de conocimiento", cargar_kb)
    crear_boton("2. Cargar archivo de casos", cargar_casos_archivo)

    # Combobox = menú desplegable. state="readonly" = solo se puede elegir, no escribir.
    menu_casos = ttk.Combobox(marco_botones, state="readonly", width=34)
    menu_casos.pack(side="left", padx=3)

    # bind() conecta un evento con una función: al elegir una opción se llama a elegir_caso.
    menu_casos.bind("<<ComboboxSelected>>", elegir_caso)

    crear_boton("3. Ejecutar", ejecutar)
    crear_boton("Siguiente paso", siguiente_paso)
    crear_boton("Mostrar todo", mostrar_todo)
    crear_boton("Limpiar", limpiar)

    # Si main.py nos pasó una base por defecto, la cargamos al abrir la ventana.
    if ruta_kb_inicial:
        poner_base(ruta_kb_inicial)

    # mainloop() mantiene la ventana abierta y atenta a los clics hasta que se cierre.
    ventana.mainloop()



# Si se ejecuta este archivo directamente, carga la base de conocimiento inicial.
if __name__ == "__main__":
    ruta_base = os.path.join(CARPETA_PROYECTO, "conocimiento", "red_fallas.json")
    iniciar_interfaz(ruta_base)
