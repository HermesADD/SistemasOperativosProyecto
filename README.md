# Proyecto

> Sistemas Operativos
> Semestre 2026 - 01.
> Javier León Cotonieto

## Autor
- Hermes Alberto Delgado Díaz

## Descripción
> Desarrollo de un monitor básico que implementa una herramienta sencilla que muestre información relevante del Sistema Operativo (SO) en la terminal. El script muestra métricas actualizadas en tiempo real sobre:
- Uso de CPU (por núcleo)
- Uso de Memoria RAM
- Particiones de Disco y uso de espacio.
- Tasas de I/O (lectura/escritura de disco).
- Tasas de Red (envío/recepción).
- Top 10 Procesos con mayor uso de CPU.
- Estado de la Batería (si aplica).

## Guía de instalación, herramientas necesarias

> Para ejecutar el monitor correctamente, necesitarás los siguientes componentes:
1. Requisistos del SO. El script es compatible con la mayoría de sistemas operativos que soporten Python, incluyendo:
    - Windows 10 u 11.
    - Linux (ej. Ubuntu, Debian, Kali)
    - macOS

2. Lenguaje de Programación:
    - Python 3.x: El script requiere una versión moderna de Python (se recomienda 3.6 o superior). Para instalar Python en tu SO clickea la imagen: [![Tutorial para instalar Python en tu SO](https://www.python.org/static/img/python-logo.png)](https://youtu.be/JZ_pHQo5Nxk?si=EnRs5815woHEhaWB)

3. Librerías de Python (Dependencias)

| Librería   | Tipo           | Propósito   |
|:-----------|:---------------|:------------|
| psutil     | Externa            | Obtener métricas de CPU, RAM, Disco, Red, Procesos, etc.       |
| os, time, sys, platform   | Estándar          | Funciones básicas del sistema, manejo de tiempo y metadatos. Incluidas en Python.|

### Instrucciones de Instalación y Ejecución

Sigue estos pasos para poner en marcha el monitor:

**Paso 1: Clonar o Descargar el Repositorio**

Clona el repositorio usando Git:
```shell
git clone https://github.com/HermesADD/SistemasOperativosProyecto.git
```

O descarga directamente desde [este enlace](https://github.com/HermesADD/SistemasOperativosProyecto/archive/refs/heads/main.zip)

**Paso 2: Instalar la Dependencia**

Abre tu terminal o símbolo del sistema y ejecuta el siguiente comando para instalar *psutil* 
```shell
pip install psutil
```

**Paso 3: Ejecutar el Monitor**

Navega hasta el directorio donde se encuentra el script y ejecútalo con Python:
```shell
python Monitor.py
```
- El monitor se actualizará automáticamente cada **segundo**.
- Para detener la ejecución en cualquier momento, presiona __*Ctrl + C*__


