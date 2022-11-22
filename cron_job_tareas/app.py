import time
import atexit
import os
import sqlalchemy
from pydub import AudioSegment
#from flaskr import create_app
#from .modelos import *
from modelos import *
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail
from flask import Flask
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber import exceptions as sub_exceptions
from concurrent.futures import TimeoutError


#app = create_app('default')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://newuser@localhost:5432/cloud_conversion_tool'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY']='secretisimo'
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['UPLOAD_FOLDER'] = "/"
app.config['MAIL_SERVER='] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'testcloudteam7@gmail.com'
app.config['MAIL_PASSWORD'] = 'fqaqckznkqgnqdmp'

app_context = app.app_context()
app_context.push()

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME = 'testcloudteam7@gmail.com',
    MAIL_PASSWORD = 'fqaqckznkqgnqdmp',
    #SQLALCHEMY_DATABASE_URI = 'postgresql://newuser@localhost:5432/cloud_conversion_tool'
    SQLALCHEMY_DATABASE_URI = 'postgresql://conversiontool:conversiontool@db:5432/conversiontool'
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
    #tasks = Tarea.query.filter_by(estado = "UPLOADED").all()
    credentials_path = '../pubsub-service-key.json'
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = 'projects/desarrollo-cloud-368422/subscriptions/async-webapp-worker-sub'

    def callback(message: pubsub_v1.subscriber.message.Message) -> None:
        print(f"Received {message}.")
        id_tarea = int(message.data)
        message.ack()
        execute_task(id_tarea)

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}..\n")

    # Wrap subscriber in a 'with' block to automatically call close() when done.
    with subscriber:
        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            timeout = 10.0
            streaming_pull_future.result(timeout=timeout)
        except TimeoutError:
            streaming_pull_future.cancel()  # Trigger the shutdown.
            streaming_pull_future.result()  # Block until the shutdown is complete.

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
    
    
def execute_task(id_task):
    print("Inicio Ejecución de Tarea Pendiente")
    task = Tarea.query.filter_by(id = id_task).first()
    convert_audio_file(task.nombre_archivo,task.formato_destino)
    report_executed_task(task)
    sendEmail(task)
    
def process_pending_tasks():   
    with app.app_context():   
        query_pending_tasks()
        #execute_tasks(tasks)

scheduler = BackgroundScheduler()
scheduler.add_job(func = process_pending_tasks, trigger = "interval", seconds=60, id = "tasks")
scheduler.start()

# Para dejar de ejecutar el cron al salir de la aplicación:
#atexit.register(lambda: scheduler.shutdown())