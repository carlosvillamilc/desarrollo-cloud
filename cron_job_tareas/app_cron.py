import os
from pydub import AudioSegment
import yagmail
import psycopg2
from datetime import datetime
from google.cloud import storage


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
DATABASE_HOST = '34.27.234.145'
DATABASE_PORT = '5432'
DATABASE_NAME = 'conversiontool'

#gcp credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '../desarrollo-cloud-368422.json'
BUCKET_NAME = 'archivos_audio'

def convert_audio_file(fileName,newFormat):
    
    files_path = "../archivos_audio/"
    original = files_path + fileName    
    completeFileName, file_extension = os.path.splitext(original)    
    converted_file = completeFileName+ "." + newFormat.lower()    
    download_process = download_from_bucket(fileName,original,BUCKET_NAME)    
    if download_process == True:
        sound = AudioSegment.from_file(original, file_extension[1:4])    
        sound.export(converted_file, format=newFormat.lower())
        converted_bucket = converted_file.split(files_path)
        upload_to_bucket(converted_bucket[1],converted_file,BUCKET_NAME)
        os.remove(os.path.join(files_path, original))
        os.remove(os.path.join(files_path, converted_file))
    else:
        print("Error descargando de cloud storage")

    

def query_pending_tasks():
    try:
        connection = psycopg2.connect(user=DATABASE_USER,
                                    password=DATABASE_PASSWORD,
                                    host=DATABASE_HOST,
                                    port=DATABASE_PORT,
                                    database=DATABASE_NAME)
        cursor = connection.cursor()
        postgreSQL_select_Query = "select * from tarea where estado = 'UPLOADED' "

        cursor.execute(postgreSQL_select_Query)        
        tareas = cursor.fetchall()

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            #print("PostgreSQL connection is closed")
        return tareas


def report_executed_task(task):    
    task_id = task[0]
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
        print("Error while fetching data from PostgreSQL", error)

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            #print("PostgreSQL connection is closed")
        return
    
    

def sendEmail(task):
    idUser = task[1]
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
        nombre_archivo = task[2]
        formato_destino = task[4]
        message = "El proceso de conversion del archivo " + str(nombre_archivo) + " a formato " + str(formato_destino) + " ha sido finalizado"
        print(message)
        sender = 'testcloudteam7@gmail.com'
        sender_pwd = 'fqaqckznkqgnqdmp'
        
        receivers = [email[0][0]]
        subject = 'Tarea de conversion finalizada'
        
        try:
            yag = yagmail.SMTP(sender,sender_pwd)
            yag.send(receivers,subject,message)
        except:
            print("Error: unable to send email")
        
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            #print("PostgreSQL connection is closed")
        return

    
    
    
def execute_tasks(tasks):
    print("Inicio Ejecucion Tareas Pendientes ", datetime.now())
    for task in tasks:
        nombre_archivo = str(task[2])
        formato_destino = str(task[4])
        convert_audio_file(nombre_archivo,formato_destino)
        report_executed_task(task)
        #sendEmail(task)
    

def process_pending_tasks():
    add_usr_local_bin()   
    tasks = query_pending_tasks()    
    execute_tasks(tasks)

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


process_pending_tasks()

