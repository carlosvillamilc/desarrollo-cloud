import os
from pydub import AudioSegment
import psycopg2
from datetime import datetime
from google.cloud import storage
import requests
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber import exceptions as sub_exceptions
from concurrent.futures import TimeoutError
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

#app = Flask(__name__)

#app_context = app.app_context()
#app_context.push()

MAIL_SERVER='smtp.gmail.com',
MAIL_PORT=587,
MAIL_USERNAME = 'testcloudteam7@gmail.com',
MAIL_PASSWORD = 'fqaqckznkqgnqdmp',
#local
#DATABASE_USER = 'newuser'
#DATABASE_PASSWORD = '1234'
#DATABASE_HOST = '127.0.0.1'
#DATABASE_PORT = '5432'
#DATABASE_NAME = 'cloud_conversion_tool'

#docker
DATABASE_USER = 'conversiontool'
DATABASE_PASSWORD = 'conversiontool'
#DATABASE_HOST = 'db'
DATABASE_HOST = '34.171.156.60'
DATABASE_PORT = '5432'
DATABASE_NAME = 'conversiontool'

#KEY = '633e66532c7a4cdbaaa7bd093e9867ac-2de3d545-152bfa5e'
KEY = 'c536a392c5d964e42323a333fde45738-62916a6c-e2aa5d70'
SANDBOX = 'sandbox85cb5dcfb07a4e6e9ffdc7e24f759e66.mailgun.org'

#gcp credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'desarrollo-cloud.json'
BUCKET_NAME = 'bucket_archivos_audio'

app = Flask(__name__)
app_context = app.app_context()
app_context.push()

def convert_audio_file(fileName,newFormat):
    
    files_path = "."
    #original = files_path + fileName
    original = fileName    
    completeFileName, file_extension = os.path.splitext(original)
    print("completeFileName ",completeFileName)
    print("file_extension ",file_extension)
    converted_file = completeFileName+ "." + newFormat.lower()    
    print("converted_file "+converted_file)
    download_process = download_from_bucket(fileName,original,BUCKET_NAME)
    print("fileName "+fileName)
    if download_process == True:
        sound = AudioSegment.from_file(original, file_extension[1:4])    
        sound.export(converted_file, format=newFormat.lower())
        #converted_bucket = converted_file.split(files_path)
        upload_to_bucket(converted_file,converted_file,BUCKET_NAME)
        os.remove(os.path.join(files_path, original))
        os.remove(os.path.join(files_path, converted_file))
    else:
        print("Error descargando de cloud storage")

    
def query_pending_tasks():
    credentials_path = 'desarrollo-cloud.json'
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = 'projects/desarrollo-cloud-370513/subscriptions/async-webapp-worker-sub'
    

    def callback(message: pubsub_v1.subscriber.message.Message) -> None:
        tarea = {}
        print(f"Received {message}.")
        print(f'data: {message.data}')
        if message.attributes:   
            for key in message.attributes:
                value = message.attributes.get(key)
                tarea[key] = value
            #arrayTareas.append(tarea)
        message.ack()
        execute_task(tarea)

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}..\n")

    # Wrap subscriber in a 'with' block to automatically call close() when done.
    with subscriber:
        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            #timeout = 60.0
            #streaming_pull_future.result(timeout=timeout)
            streaming_pull_future.result()
        except TimeoutError:
            streaming_pull_future.cancel()  # Trigger the shutdown.
            streaming_pull_future.result()  # Block until the shutdown is complete.


def report_executed_task(task):    
    task_id = task["id"]
    print(task["id"])
    try:
        connection = psycopg2.connect(user=DATABASE_USER,
                                    password=DATABASE_PASSWORD,
                                    host=DATABASE_HOST,
                                    port=DATABASE_PORT,
                                    database=DATABASE_NAME)
        cursor = connection.cursor()
        postgreSQL_select_Query = """update tarea set estado = 'PROCESSED' where id = %s"""        
        cursor.execute(postgreSQL_select_Query,(task_id,))
        print("Updating task status", task_id, datetime.now())
        connection.commit()        

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error, " in 'report_executed_task'")

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            #print("PostgreSQL connection is closed")
        return

def send_mail_mailgun(sender, recipient,message):
    request_url = f'https://api.mailgun.net/v3/{SANDBOX}/messages'

    request = requests.post(request_url, auth=('api', KEY), data={
        'from': sender,
        'to': recipient,
        'subject': 'Tarea de conversion finalizada',
        'text': message
    })

    if request.status_code == 200:
        print('Correo electrónico enviado exitosamente.')
        #print(request.json())


    
def sendEmail(task):
    idUser = task["id_usuario"]
    try:
        connection = psycopg2.connect(user=DATABASE_USER,
                                    password=DATABASE_PASSWORD,
                                    host=DATABASE_HOST,
                                    port=DATABASE_PORT,
                                    database=DATABASE_NAME)
        cursor = connection.cursor()
        postgreSQL_select_Query = "select correo from usuario where id = %s "

        cursor.execute(postgreSQL_select_Query,(idUser,))        
        email = cursor.fetchall()                
        nombre_archivo = task["nombre_archivo"]
        formato_destino = task["formato_destino"]
        message = "El proceso de conversion del archivo " + str(nombre_archivo) + " a formato " + str(formato_destino) + " ha sido finalizado"
        print(message)
        sender = 'testcloudteam7@gmail.com'
        sender_pwd = 'fqaqckznkqgnqdmp'
        
        receivers = [email[0][0]]
        #subject = 'Tarea de conversion finalizada'
        
        try:
            send_mail_mailgun(sender,receivers,message)
            #yag = yagmail.SMTP(sender,sender_pwd)
            #yag.send(receivers,subject,message)
        except:
            print("Error: unable to send email")
        
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error, " in send_email")

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            #print("PostgreSQL connection is closed")
        return

def execute_task(tarea):
    print("Inicio Ejecucion Tareas Pendientes ", datetime.now())
    convert_audio_file(tarea["nombre_archivo"],tarea["formato_destino"])
    report_executed_task(tarea)
    sendEmail(tarea)

#def clear_tareas():
#    execute_task(arrayTareas)
#    arrayTareas.clear()
    

def process_pending_tasks():
    add_usr_local_bin()   
    query_pending_tasks()    


def add_usr_local_bin():
    ffmpeg_path = "/usr/local/bin"
    os.environ["PATH"] += os.pathsep + ffmpeg_path


#blob = a binary larg oBject is a collection of a binary data sotres as a single entity
def upload_to_bucket(blob_name,file_path,bucket_name):
    print("upload")
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(file_path)
        return True
    except Exception as e:
        print(e)
        return False

def download_from_bucket(blob_name,file_path,bucket_name):
    print("download", file_path)
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        with open(file_path,'wb') as f:
                storage_client.download_blob_to_file(blob,f)        
        return True
    except Exception as e:
        print(e)
        return False


#arrayTareas = []
process_pending_tasks()

#scheduler = BackgroundScheduler()
#scheduler.add_job(func = process_pending_tasks, trigger = "interval", seconds=60, id = "tasks")
#scheduler.start()