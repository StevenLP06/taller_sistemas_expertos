**Descripción**

Sistema experto desarrollado en Python para diagnosticar fallas de red e Internet. 
Utiliza una base de conocimiento con reglas de producción, hechos iniciales y un motor de inferencia
que genera diagnósticos y recomendaciones.El sistema cuenta con una interfaz gráfica que 
permite cargar archivos y observar el proceso de inferencia paso a paso. 

**Tecnologías**

1. Python

2. Tkinter

3. JSON

**Integrantes**

-Juan Sebastián Zapata Zapata 

-Steven López Parra 

-Saray Cerquera Vallejo

**Instalación y ejecución**

git clone https://github.com/StevenLP06/taller_sistemas_expertos.git

cd taller_sistemas_expertos

Ejecutar python main.py

Se requiere Python instalado y Tkinter disponible.

**Verificar que Tkinter esté disponible:**

python -m tkinter

**Si no está disponible, instalarlo según el sistema operativo:**

**Windows:**

modificar la instalación de Python y seleccionar el componente Tcl/Tk.

**Ubuntu o Debian:**

sudo apt update

sudo apt install python3-tk


**Funcionamiento**

Aparece un menú:
1. **Ejecutar un caso** de `casos/casos.txt` (o los 8 a la vez) y ver la inferencia paso a paso en la consola.
2. **Ingresar los hechos a mano**: el sistema pregunta s/n por cada observación.
3. **Abrir la interfaz gráfica** (Tkinter): cargar la base de conocimiento, cargar el archivo de casos,
elegir un caso en el menú desplegable (o marcar los hechos), *Ejecutar* y luego *Siguiente paso* (o *Mostrar todo*).

El sistema permite ingresar hechos iniciales manualmente o desde archivos externos.
A partir de ellos, aplica encadenamiento hacia adelante y utiliza una estrategia de resolución de conflictos 
basada en prioridad, recencia, especificidad y orden de las reglas.
La base de conocimiento contiene 20 reglas conectadas que permiten obtener diagnósticos y 
recomendaciones sobre fallas de conectividad. Así,
El usuario indica qué observa en su red 
(luces del router, resultados de `ping`, señal WiFi, etc.).
El sistema aplica reglas SI–ENTONCES encadenadas (observación → hecho intermedio → diagnóstico →
recomendación) y entrega el diagnóstico con la recomendación y su cadena de razonamiento.


