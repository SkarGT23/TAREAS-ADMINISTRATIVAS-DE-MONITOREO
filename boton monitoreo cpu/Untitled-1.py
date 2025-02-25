import tkinter as tk
import psutil
import time
import threading
import mysql.connector

# Conectar a la base de datos MySQL
def connect_db():
    return mysql.connector.connect(
        host="localhost",  # Cambia si tu servidor está en otra ubicación
        user="tu_usuario",  # Tu usuario de MySQL
        password="tu_contraseña",  # Tu contraseña de MySQL
        database="system_monitor"  # Nombre de la base de datos
    )

# Función para monitorear el sistema operativo
def monitor_system():
    while running:
        # Obtener información de uso del CPU y la memoria
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        
        # Actualizar el texto en la interfaz gráfica
        status_label.config(text=f"CPU: {cpu_usage}% | RAM: {memory_info.percent}%")
        
        # Guardar el historial cada 5 segundos si el botón ha sido activado
        if save_history:
            save_to_database(cpu_usage, memory_info.percent)
        
        time.sleep(5)

# Función para guardar los registros en la base de datos
def save_to_database(cpu, memory):
    try:
        db_connection = connect_db()
        cursor = db_connection.cursor()
        
        # Insertar un nuevo registro en la base de datos
        cursor.execute("INSERT INTO system_logs (cpu_usage, ram_usage) VALUES (%s, %s)", (cpu, memory))
        
        # Confirmar la transacción
        db_connection.commit()
        
        cursor.close()
        db_connection.close()
    except mysql.connector.Error as err:
        print(f"Error al guardar en la base de datos: {err}")

# Función para iniciar el monitoreo en un hilo separado
def start_monitoring():
    global running, save_history
    running = True
    save_history = True
    monitor_thread = threading.Thread(target=monitor_system)
    monitor_thread.daemon = True
    monitor_thread.start()

# Función para detener el monitoreo
def stop_monitoring():
    global running
    running = False

# Función para activar el guardado de historial
def start_saving_history():
    global save_history
    save_history = True
    save_button.config(state=tk.DISABLED)  # Desactivar el botón de guardar después de ser presionado

# Crear la ventana principal
root = tk.Tk()
root.title("Monitoreo del Sistema")

# Etiqueta para mostrar el estado del sistema
status_label = tk.Label(root, text="CPU: 0% | RAM: 0%", font=("Helvetica", 16))
status_label.pack(pady=20)

# Botón para iniciar el monitoreo
start_button = tk.Button(root, text="Iniciar Monitoreo", command=start_monitoring, font=("Helvetica", 14))
start_button.pack(pady=10)

# Botón para detener el monitoreo
stop_button = tk.Button(root, text="Detener Monitoreo", command=stop_monitoring, font=("Helvetica", 14))
stop_button.pack(pady=10)

# Botón para activar el guardado del historial
save_button = tk.Button(root, text="Guardar Historial", command=start_saving_history, font=("Helvetica", 14))
save_button.pack(pady=10)

# Iniciar la interfaz gráfica
root.mainloop()

