import time
import atexit
import os
import sqlalchemy
from pydub import AudioSegment
from flaskr import create_app
from .modelos import *
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail

app = create_app('default')
app_context = app.app_context()
app_context.push()

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME = 'testcloudteam7@gmail.com',
    MAIL_PASSWORD = 'fqaqckznkqgnqdmp',
    SQLALCHEMY_DATABASE_URI = 'postgresql://newuser@localhost:5432/cloud_conversion_tool'
)
db.init_app(app)
mail = Mail(app)
    
def convert_audio_file(fileName,newFormat):
    
    files_path = "../archivos_audio/"
    original = files_path + fileName
    
    completeFileName, file_extension = os.path.splitext(original)
    converted = completeFileName+ "." + newFormat.name.lower()
        
    sound = AudioSegment.from_file(original, file_extension[1:4])
    
    sound.export(converted, format=newFormat.name.lower())
    
    
def query_pending_tasks():
    tasks = Tarea.query.filter_by(estado = "UPLOADED").all()
    return tasks


def report_executed_task(task):
    task.estado = "PROCESSED"
    db.session.commit()
    return

def sendEmail(task):
    idUser = task.id_usuario
    message = "El proceso de conversión del archivo " + task.nombre_archivo + " a formato " + task.formato_destino.name + " ha sido finalizado"
    user = Usuario.query.get(idUser)
    email_message = mail.send_message(
        subject = 'Tarea de conversión terminada',
        sender = 'testcloudteam7@gmail.com',
        recipients = [user.correo],
        body = message
    )
    return
    
    
def execute_tasks(tasks):
    print("Inicio Ejecución Tareas Pendientes")
    for task in tasks:
        convert_audio_file(task.nombre_archivo,task.formato_destino)
        report_executed_task(task)
        sendEmail(task)
    
def process_pending_tasks():   
    with app.app_context():   
        tasks = query_pending_tasks()
        execute_tasks(tasks)

scheduler = BackgroundScheduler()
scheduler.add_job(func = process_pending_tasks, trigger = "interval", seconds=60, id = "tasks")
scheduler.start()

# Para dejar de ejecutar el cron al salir de la aplicación:
atexit.register(lambda: scheduler.shutdown())