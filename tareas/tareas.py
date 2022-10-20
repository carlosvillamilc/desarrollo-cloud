from celery import Celery

celery_app = Celery(__name__, broker='redis://localhost:6379/0')

@celery_app.task(name="registrar_login") # con este decorador indicamos que esta función debe pasar a través de la cola
def registrar_login(usuario,fecha):
    with open('registro_logins.txt', 'a+') as file:
        file.write('{} - Inicio de sesión {}\n'.format(usuario, fecha))
      