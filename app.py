from flask import Flask, render_template, jsonify, send_file
import psutil
import sqlite3
import matplotlib.pyplot as plt
import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)

# Función para guardar recursos en base de datos (historial)
def save_resource_data(cpu_percent, memory_percent, disk_percent):
    conn = sqlite3.connect('resources.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS resource_data (cpu REAL, memory REAL, disk REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute("INSERT INTO resource_data (cpu, memory, disk) VALUES (?, ?, ?)", (cpu_percent, memory_percent, disk_percent))
    conn.commit()
    conn.close()

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# API para obtener recursos del sistema
@app.route('/api/resources')
def get_resources():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent

    # Guardar los recursos en la base de datos
    save_resource_data(cpu_percent, memory_percent, disk_percent)

    alert_message = ""
    if cpu_percent > 90:
        alert_message = "¡Advertencia! El uso de CPU está muy alto."
    elif memory_percent > 90:
        alert_message = "¡Advertencia! El uso de memoria está muy alto."
    
    return jsonify(cpu=cpu_percent, memory=memory_percent, disk=disk_percent, alert=alert_message)

# API para obtener gráfico de uso de recursos
@app.route('/api/resource_graph')
def resource_graph():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent

    # Crear gráfica
    fig, ax = plt.subplots()
    ax.bar(['CPU', 'Memoria'], [cpu_percent, memory_percent], color=['blue', 'green'])
    ax.set_title("Uso de Recursos del Sistema")

    # Guardar la gráfica en un objeto de tipo imagen
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)

    # Convertir la imagen a base64 para renderizarla en la web
    img_base64 = base64.b64encode(img.getvalue()).decode('utf8')
    
    return jsonify(image=img_base64)

# Ruta para descargar el gráfico como PNG
@app.route('/download_graph')
def download_graph():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent

    # Crear gráfica
    fig, ax = plt.subplots()
    ax.bar(['CPU', 'Memoria'], [cpu_percent, memory_percent], color=['blue', 'green'])
    ax.set_title("Uso de Recursos del Sistema")

    # Guardar la gráfica en el buffer
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)

    return send_file(img, as_attachment=True, download_name="graph.png", mimetype='image/png')

# Ruta para generar el PDF con los recursos
@app.route('/generate_pdf')
def generate_pdf():
    # Obtener el uso de recursos
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent

    # Crear un archivo PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Escribir la información en el PDF
    c.drawString(100, 750, f'Uso de CPU: {cpu_percent}%')
    c.drawString(100, 730, f'Uso de Memoria: {memory_percent}%')

    # Crear una gráfica en el PDF
    fig, ax = plt.subplots()
    ax.bar(['CPU', 'Memoria'], [cpu_percent, memory_percent], color=['blue', 'green'])
    ax.set_title("Uso de Recursos del Sistema")
    
    # Guardar la gráfica en el buffer
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    
    # Guardar la imagen en un archivo temporal
    with open('temp_image.png', 'wb') as f:
        f.write(img.getvalue())

    # Insertar la imagen en el PDF desde el archivo temporal
    c.drawImage('temp_image.png', 100, 400, width=400, height=200)
    
    c.showPage()
    c.save()
    
    # Volver a la posición inicial del buffer
    buffer.seek(0)

    # Eliminar archivo temporal después de generar el PDF
    os.remove('temp_image.png')

    return send_file(buffer, as_attachment=True, download_name="reporte_recursos.pdf", mimetype='application/pdf')

# Ruta para obtener procesos y paginarlos
@app.route('/api/processes/<int:page>')
def get_processes(page):
    processes_per_page = 10
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        processes.append(proc.info)

    processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)
    start = (page - 1) * processes_per_page
    end = start + processes_per_page

    return jsonify(processes=processes[start:end])

# Ruta para matar un proceso
@app.route('/api/kill_process/<int:pid>', methods=['DELETE'])
def kill_process(pid):
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        return jsonify(message="Proceso terminado con éxito"), 200
    except Exception as e:
        return jsonify(message=str(e)), 400

if __name__ == '__main__':
    app.run(debug=True)


#------------------------------------------------------------------------------------------

