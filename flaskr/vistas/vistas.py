import queue
from flask import request, Flask, render_template
from ..modelos import db, Tarea, Usuario, UsuarioSchema, TareaSchema
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from datetime import datetime
from celery import Celery
from werkzeug.utils import secure_filename

celery_app = Celery(__name__, broker='redis://localhost:6379/0')

@celery_app.task(name = 'registrar_login')
def registrar_login(*args):
    pass


tarea_schema = TareaSchema()
usuario_schema = UsuarioSchema()


class VistaSignIn(Resource):
    
    def post(self):
        nuevo_usuario = Usuario(usuario=request.json["usuario"], contrasena=request.json["contrasena"], correo = request.json["correo"])
        token_de_acceso = create_access_token(identity = request.json["usuario"])
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
        except:
            return {"mensaje":"no se pudo crear el usuario"}
        return {"mensaje":"usuario creado exitosamente", "token de acceso":token_de_acceso}
    
    
class VistaLogIn(Resource):
    
    def post(self):
        usuario_u = request.json["usuario"]
        usuario_contrasena = request.json["contrasena"]
        usuario = Usuario.query.filter_by(usuario = usuario_u, contrasena = usuario_contrasena).first()
        db.session.commit()
        if usuario:
            token_de_acceso = create_access_token(identity = usuario.usuario)
            args = (usuario_u, datetime.utcnow())
            registrar_login.apply_async(args = args, queue = 'login')#la cola se llama login
            return {"mensaje":"Acceso concedido", "usuario": {"usuario": usuario.usuario, "id": usuario.id}, "token": token_de_acceso}
        else:
            return {'mensaje':'Nombre de usuario o contraseña incorrectos'}, 401
            

class VistaTarea(Resource):
    
    @jwt_required()
    def post(self):
        id_usuario = Usuario.query.filter_by(usuario = get_jwt_identity()).first().id
        nombre_archivo = request.json["fileName"]
        
        # try:
        #     f = request.files['file']
        #     filename = secure_filename(f.filename)
        #     f.save(filename)
        # except Exception as e: 
        #     print(e)
        #     return 'Error al intentar subir el archivo',409
        
        nueva_tarea = Tarea(id_usuario = id_usuario, estado="UPLOADED", nombre_archivo= nombre_archivo, formato_destino=request.json["newFormat"])
        db.session.add(nueva_tarea)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return 'La tarea no pudo ser creada',409

        return tarea_schema.dump(nueva_tarea)