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
    def __init__(self):
        self.os_type = platform.system()
        self.hostname = platform.node()
        self.kernel = platform.release()
        
        self.prev_time = time.time()
        
        if PSUTIL_DISPONIBLE:
            self.prev_net = psutil.net_io_counters()
            disk_io = psutil.disk_io_counters()
            self.prev_disk_read = disk_io.read_bytes
            self.prev_disk_write = disk_io.write_bytes
            
    def obtener_metricas(self):
        if not PSUTIL_DISPONIBLE:
            return None, "La biblioteca 'psutil' no está instalada. Instálala con 'pip install psutil'."
        
        cpu_cores = psutil.cpu_percent(interval=None, percpu=True)

        # RAM
        mem = psutil.virtual_memory()
        mem_info = (mem.total, mem.used, mem.percent)

        # RED (Usando las variables de estado del Monitor)
        net_now = psutil.net_io_counters()
        now = time.time()
        
        # El tiempo entre mediciones debe ser calculado aquí para las tasas de I/O
        dt = now - self.prev_time
        if dt == 0: dt = 1

        tx_speed = (net_now.bytes_sent - self.prev_net.bytes_sent) / dt
        rx_speed = (net_now.bytes_recv - self.prev_net.bytes_recv) / dt

        self.prev_net = net_now
        
        # DISCO I/O (Usando las variables de estado del Monitor)
        disk_io = psutil.disk_io_counters()
        read_s = (disk_io.read_bytes - self.prev_disk_read) / dt
        write_s = (disk_io.write_bytes - self.prev_disk_write) / dt
        
        self.prev_disk_read = disk_io.read_bytes
        self.prev_disk_write = disk_io.write_bytes
        
        # BATERIA
        battery = psutil.sensors_battery()
        battery_info = None
        if battery:
            battery_info = {
                'percent': battery.percent,
                'plugged': battery.power_plugged
            }

        # Procesos (Se obtiene cpu_percent en tiempo real, psutil maneja el cálculo)
        procesos = []
        for p in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent']):
            try:
                # 'status' es el estado del proceso (running, sleeping, etc.)
                p.info['state'] = p.info['status']
                procesos.append(p.info)
            except:
                pass

        # Ordenar y seleccionar los Top 10 procesos
        top_procesos = sorted(procesos, key=lambda p: p['cpu_percent'] or 0, reverse=True)[:10]

        # Actualizar el tiempo para el siguiente ciclo de cálculo de tasas
        self.prev_time = now 

        return {
            'cpu_cores': cpu_cores,
            'mem': mem_info,
            'net': (tx_speed, rx_speed),
            'disk_io': (read_s, write_s),
            'battery': battery_info,
            'procesos': top_procesos
        }, None
        
def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def formatear_bytes(bytes_val):
    """Convierte bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"

def crear_barra(porcentaje, ancho=40):
    """Crea una barra de progreso visual"""
    lleno = int((porcentaje / 100) * ancho)
    vacio = ancho - lleno
    return '█' * lleno + '░' * vacio

def obtener_color_barra(porcentaje):
    """Retorna código de color según porcentaje"""
    if porcentaje < 50:
        return '\033[92m'  # Verde
    elif porcentaje < 80:
        return '\033[93m'  # Amarillo
    else:
        return '\033[91m'  # Rojo

def mostrar_metricas(metricas):
    """Muestra las métricas en formato terminal"""
    limpiar_pantalla()

    CYAN = '\033[96m'
    AMARILLO = '\033[93m'
    VERDE = '\033[92m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    print(f"{BOLD}{VERDE}{'='*80}{RESET}")
    print(f"{BOLD}{CYAN}  MONITOR DEL SISTEMA  - {time.strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{VERDE}{'='*80}{RESET}\n")

    # CPU
    print(f"{BOLD}{CYAN}[CPU USAGE - {len(metricas['cpu_cores'])} cores]{RESET}")
    for idx, uso in enumerate(metricas['cpu_cores']):
        color = obtener_color_barra(uso)
        barra = crear_barra(uso, 30)
        print(f"  Core {idx:2d}: {color}{barra}{RESET} {uso:5.1f}%")

    # Memoria
    print(f"\n{BOLD}{CYAN}[MEMORIA RAM]{RESET}")
    mem_total, mem_usado, mem_perc = metricas['mem']
    color = obtener_color_barra(mem_perc)
    barra = crear_barra(mem_perc, 50)
    print(f"  Usado: {formatear_bytes(mem_usado)} / {formatear_bytes(mem_total)} ({mem_perc:.1f}%)")
    print(f"  {color}{barra}{RESET}")

    # Red
    print(f"\n{BOLD}{CYAN}[RED]{RESET}")
    tx, rx = metricas['net']
    print(f"  {AMARILLO}↑ TX:{RESET} {formatear_bytes(tx)}/s")
    print(f"  {AMARILLO}↓ RX:{RESET} {formatear_bytes(rx)}/s")

    # Disco I/O
    print(f"\n{BOLD}{CYAN}[DISCO I/O]{RESET}")
    read, write = metricas['disk_io']
    print(f"  {AMARILLO}Read: {RESET} {formatear_bytes(read)}/s")
    print(f"  {AMARILLO}Write:{RESET} {formatear_bytes(write)}/s")

    # Batería
    if metricas['battery']:
        print(f"\n{BOLD}{CYAN}[BATERÍA]{RESET}")
        bat = metricas['battery']
        estado = "Conectado" if bat['plugged'] else "Desconectado"
        color = obtener_color_barra(100 - bat['percent'])
        barra = crear_barra(bat['percent'], 50)
        print(f"  Nivel: {bat['percent']:.0f}% ({estado})")
        print(f"  {color}{barra}{RESET}")

    # Procesos
    print(f"\n{BOLD}{CYAN}[TOP 10 PROCESOS]{RESET}")
    print(f"  {AMARILLO}{'PID':<10} {'NOMBRE':<20} {'ESTADO':<10} {'CPU %':<10}{RESET}")
    print(f"  {'-'*60}")
    for proc in metricas['procesos']:
        cpu = proc.get('cpu_percent', 0)
        print(f"  {str(proc['pid']):<10} {proc['name'][:20]:<20} {proc['state']:<10} {cpu:>6.1f}%")

    print(f"\n{VERDE}{'='*80}{RESET}")
    print(f"Actualización cada {ACTUALIZACION_MS}ms | Presiona Ctrl+C para salir")


def main():
    monitor = Monitor()

    print("Iniciando monitor del sistema...")
    print(f"Sistema operativo: {monitor.os_type}")
    print(f"Hostname: {monitor.hostname}")
    print(f"Kernel: {monitor.kernel}\n")

    if not PSUTIL_DISPONIBLE:
        print("ERROR: psutil no está instalado.")
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