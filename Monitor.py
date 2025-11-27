import os
import time
import sys
import platform

try:
    import psutil
    PSUTIL_DISPONIBLE = True
except:
    PSUTIL_DISPONIBLE = False
    
ACTUALIZACION_MS = 1000

class Monitor:
    """
    Clase encargada de inicializar el sistema y obtener las métricas
    en tiempo real usando la librería psutil.
    """
    
    def __init__(self):
        """Inicializa los metadatos del sistema y los contadores previos."""
        # Información estática del sistema
        self.os_type = platform.system()  # Ej: 'Windows', 'Linux'
        self.hostname = platform.node()   # Nombre del equipo
        self.kernel = platform.release()  # Versión del kernel/OS
        
        # Variables necesarias para calcular tasas (I/O y Red)
        self.prev_time = time.time() # Tiempo del ciclo anterior
        
        if PSUTIL_DISPONIBLE:
            # Contadores de red para calcular TX/RX (bytes enviados/recibidos)
            self.prev_net = psutil.net_io_counters()
            
            # Contadores de disco para calcular la velocidad de lectura/escritura
            disk_io = psutil.disk_io_counters()
            self.prev_disk_read = disk_io.read_bytes
            self.prev_disk_write = disk_io.write_bytes
            
    def obtener_metricas(self):
        """
        Recopila todas las métricas de rendimiento del sistema en el ciclo actual.
        Retorna un diccionario de métricas o un mensaje de error si falta psutil.
        """
        if not PSUTIL_DISPONIBLE:
            return None, "La biblioteca 'psutil' no está instalada. Instálala con 'pip install psutil'."
        
        # CPU: Uso por núcleo. interval=None para no bloquear, psutil calcula el delta 
        # entre llamadas a cpu_percent.
        cpu_cores = psutil.cpu_percent(interval=None, percpu=True)

        # RAM: Información de memoria virtual (total, usado, porcentaje)
        mem = psutil.virtual_memory()
        mem_info = (mem.total, mem.used, mem.percent)

        # --- Cálculo de tasas de RED y DISCO I/O ---
        
        # Obtener contadores actuales
        net_now = psutil.net_io_counters()
        disk_io = psutil.disk_io_counters()
        now = time.time()
        
        # Calcular el tiempo transcurrido (delta time) para las tasas
        dt = now - self.prev_time
        if dt == 0: dt = 1 # Evitar división por cero
        
        # RED: Calcular velocidad de Transmisión (TX) y Recepción (RX) en bytes/s
        tx_speed = (net_now.bytes_sent - self.prev_net.bytes_sent) / dt
        rx_speed = (net_now.bytes_recv - self.prev_net.bytes_recv) / dt

        # Actualizar contadores de red para el siguiente ciclo
        self.prev_net = net_now
        
        # DISCO I/O: Calcular velocidad de lectura y escritura en bytes/s
        read_s = (disk_io.read_bytes - self.prev_disk_read) / dt
        write_s = (disk_io.write_bytes - self.prev_disk_write) / dt
        
        # Actualizar contadores de disco para el siguiente ciclo
        self.prev_disk_read = disk_io.read_bytes
        self.prev_disk_write = disk_io.write_bytes
        
        # --- Particiones de Disco ---
        particiones = []
        for particion in psutil.disk_partitions():
            try:
                # Obtener uso de disco para el punto de montaje
                uso = psutil.disk_usage(particion.mountpoint)
                particiones.append({
                    'device': particion.device,
                    'mountpoint': particion.mountpoint,
                    'fstype': particion.fstype,
                    'total': uso.total,
                    'used': uso.used,
                    'free': uso.free,
                    'percent': uso.percent
                })
            except PermissionError:
                # Ignorar particiones que no tienen permisos de acceso (común en Linux)
                continue
        
        # --- Batería ---
        battery = psutil.sensors_battery()
        battery_info = None
        if battery:
            battery_info = {
                'percent': battery.percent,
                'plugged': battery.power_plugged # True/False si está conectado a la corriente
            }

        # --- Procesos ---
        procesos = []
        # Iterar sobre todos los procesos y obtener PID, nombre, estado (status) y uso de CPU
        for p in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent']):
            try:
                # Renombrar 'status' a 'state' para consistencia con la terminología general
                p.info['state'] = p.info['status']
                procesos.append(p.info)
            except:
                # Ignorar procesos que terminaron o no tienen permisos durante la iteración
                pass

        # Ordenar los procesos por uso de CPU (descendente) y seleccionar los 10 primeros
        top_procesos = sorted(procesos, key=lambda p: p['cpu_percent'] or 0, reverse=True)[:10]

        # Actualizar el tiempo de referencia para el cálculo de tasas del siguiente ciclo
        self.prev_time = now 

        # Retornar el diccionario con todas las métricas recopiladas
        return {
            'cpu_cores': cpu_cores,
            'mem': mem_info,
            'net': (tx_speed, rx_speed),
            'disk_io': (read_s, write_s),
            'particiones': particiones,
            'battery': battery_info,
            'procesos': top_procesos
        }, None
        
def limpiar_pantalla():
    """Limpia la terminal (cls para Windows, clear para otros SO)."""
    os.system('cls' if os.name == 'nt' else 'clear')

def formatear_bytes(bytes_val):
    """Convierte un valor de bytes a un formato legible (KB, MB, GB, TB)."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"

def crear_barra(porcentaje, ancho=40):
    """Crea una barra de progreso visual usando caracteres Unicode (█ y ░)."""
    lleno = int((porcentaje / 100) * ancho)
    vacio = ancho - lleno
    return '█' * lleno + '░' * vacio

def obtener_color_barra(porcentaje):
    """
    Retorna el código de color ANSI para la terminal basado en el porcentaje:
    Verde (bajo), Amarillo (medio), Rojo (alto).
    """
    if porcentaje < 50:
        return '\033[92m'  # Verde
    elif porcentaje < 80:
        return '\033[93m'  # Amarillo
    else:
        return '\033[91m'  # Rojo

def mostrar_metricas(metricas):
    """
    Muestra las métricas recopiladas en un formato amigable para la terminal,
    utilizando códigos de color ANSI para estructura y legibilidad.
    """
    limpiar_pantalla()

    
    AZUL = '\033[94m'
    AMARILLO = '\033[93m'
    VERDE = '\033[92m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    print(f"{BOLD}{VERDE}{'='*80}{RESET}")
    print(f"{BOLD}{AZUL}  MONITOR DEL SISTEMA  - {time.strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{VERDE}{'='*80}{RESET}")
    
    # CPU
    print(f"\n{BOLD}{AZUL}[CPU USAGE - {len(metricas['cpu_cores'])} cores]{RESET}")
    for idx, uso in enumerate(metricas['cpu_cores']):
        color = obtener_color_barra(uso)
        barra = crear_barra(uso, 30)
        print(f"  Core {idx:2d}: {color}{barra}{RESET} {uso:5.1f}%")

    # Memoria
    print(f"\n{BOLD}{AZUL}[MEMORIA RAM]{RESET}")
    mem_total, mem_usado, mem_perc = metricas['mem']
    color = obtener_color_barra(mem_perc)
    barra = crear_barra(mem_perc, 50)
    print(f"  Usado: {formatear_bytes(mem_usado)} / {formatear_bytes(mem_total)} ({mem_perc:.1f}%)")
    print(f"  {color}{barra}{RESET}")

    # Disco I/O
    print(f"\n{BOLD}{AZUL}[DISCO I/O]{RESET}")
    read, write = metricas['disk_io']
    print(f"  {AMARILLO}Read: {RESET} {formatear_bytes(read)}/s")
    print(f"  {AMARILLO}Write:{RESET} {formatear_bytes(write)}/s")

    # Particiones de Disco
    print(f"\n{BOLD}{AZUL}[PARTICIONES DE DISCO]{RESET}")
    for part in metricas['particiones']:
        color = obtener_color_barra(part['percent'])
        barra = crear_barra(part['percent'], 30)
        print(f"  {AMARILLO}{part['mountpoint']}{RESET} ({part['device']})")
        print(f"    {formatear_bytes(part['used'])} / {formatear_bytes(part['total'])} ({part['percent']:.1f}%)")
        print(f"    {color}{barra}{RESET}")
        print(f"    Libre: {formatear_bytes(part['free'])} | Tipo: {part['fstype']}")

    # Red
    print(f"\n{BOLD}{AZUL}[RED]{RESET}")
    tx, rx = metricas['net']
    print(f"  {AMARILLO}↑ TX:{RESET} {formatear_bytes(tx)}/s")
    print(f"  {AMARILLO}↓ RX:{RESET} {formatear_bytes(rx)}/s")

    # Batería
    if metricas['battery']:
        print(f"\n{BOLD}{AZUL}[BATERÍA]{RESET}")
        bat = metricas['battery']
        estado = "Conectado" if bat['plugged'] else "Desconectado"
        color = obtener_color_barra(100 - bat['percent'])
        barra = crear_barra(bat['percent'], 50)
        print(f"  Nivel: {bat['percent']:.0f}% ({estado})")
        print(f"  {color}{barra}{RESET}")

    # Procesos
    print(f"\n{BOLD}{AZUL}[TOP 10 PROCESOS]{RESET}")
    print(f"  {AMARILLO}{'PID':<10} {'NOMBRE':<20} {'ESTADO':<10} {'CPU %':<10}{RESET}")
    print(f"  {'-'*60}")
    for proc in metricas['procesos']:
        cpu = proc.get('cpu_percent', 0)
        print(f"  {str(proc['pid']):<10} {proc['name'][:20]:<20} {proc['state']:<10} {cpu:>6.1f}%")

    print(f"\n{VERDE}{'='*80}{RESET}")
    print(f"Actualización cada {ACTUALIZACION_MS}ms | Presiona Ctrl+C para salir")


def main():
    """Punto de entrada del script. Inicializa el monitor y entra en el bucle principal."""
    monitor = Monitor()

    print("Iniciando monitor del sistema...")
    print(f"Sistema operativo: {monitor.os_type}")
    print(f"Hostname: {monitor.hostname}")
    print(f"Kernel: {monitor.kernel}\n")

    if not PSUTIL_DISPONIBLE:
        print("PSUTIL no está instalado.")
        print("Instala con: pip install psutil")
        return

    time.sleep(2)

    try:
        while True:
            metricas, error = monitor.obtener_metricas()

            if error:
                print(f"ERROR: {error}")
                break

            mostrar_metricas(metricas)
            time.sleep(ACTUALIZACION_MS / 1000.0)

    except KeyboardInterrupt:
        print("\n\nMonitor detenido por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()