from flask import request, jsonify
from ..modelos import db, Tarea, Usuario, UsuarioSchema, TareaSchema
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from datetime import datetime
from celery import Celery
from werkzeug.utils import secure_filename

import os
import queue

# celery_app = Celery(__name__, broker='redis://localhost:6379/0')

# @celery_app.task(name = 'registrar_login')
# def registrar_login(*args):
#     pass
 
ALLOWED_EXTENSIONS = set(['mp3', 'wav', 'ogg'])
UPLOAD_FOLDER = '../archivos_audio'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



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
            #registrar_login.apply_async(args = args, queue = 'login')#la cola se llama login
            return {"mensaje":"Acceso concedido", "usuario": {"usuario": usuario.usuario, "id": usuario.id}, "token": token_de_acceso}
        else:
            return {'mensaje':'Nombre de usuario o contraseña incorrectos'}, 401

class VistaTareas(Resource):

    @jwt_required()
    def get(self):
        id_usuario = Usuario.query.filter_by(usuario = get_jwt_identity()).first().id
        return [tarea_schema.dump(tarea) for tarea in Tarea.query.filter(Tarea.id_usuario == id_usuario).all()]
    
    @jwt_required()
    def post(self):
        id_usuario = Usuario.query.filter_by(usuario = get_jwt_identity()).first().id
        
        # check if the post request has the file part
        print(request.files)
        if 'file' not in request.files:
            resp = jsonify({'message' : 'No file part in the request'})
            resp.status_code = 400
            return resp
        
            
        files = request.files.getlist('file')
        errors = {}
        success = False
        
        for file in files:
            print(file)
            print(allowed_file(file.filename))
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                print(filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                success = True                
            else:
                errors['message'] = 'File type is not allowed or file not specified'
        print(success,errors)
        
        if request.form['newFormat'].lower() not in ALLOWED_EXTENSIONS:
            errors['message'] = 'Format to convert type is not allowed'
            resp = jsonify(errors)
            resp.status_code = 400
            return resp
        
        if success:            
            nueva_tarea = Tarea(id_usuario = id_usuario, estado="UPLOADED", nombre_archivo= filename, formato_destino=request.form['new_format'].upper())
            db.session.add(nueva_tarea)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return 'La tarea no pudo ser creada',409
            
            resp = jsonify({'message' : tarea_schema.dump(nueva_tarea)})
            resp.status_code = 201
            return resp            
            
        else:
            print("else")
            resp = jsonify(errors)
            resp.status_code = 500
            return resp

class VistaTarea(Resource):    
    @jwt_required()
    def get(self, id_tarea):
        id_usuario = Usuario.query.filter_by(usuario = get_jwt_identity()).first().id
        return [tarea_schema.dump(tarea) for tarea in Tarea.query.filter(Tarea.id_usuario == id_usuario,Tarea.id == id_tarea).all()]

    @jwt_required()
    def delete(self, id_tarea):
        id_usuario = Usuario.query.filter_by(usuario = get_jwt_identity()).first().id
        tarea = Tarea.query.filter(Tarea.id_usuario == id_usuario,Tarea.id == id_tarea).first()
        print(tarea.nombre_archivo)
        if os.path.exists(os.path.join(UPLOAD_FOLDER, tarea.nombre_archivo)):
            os.remove(os.path.join(UPLOAD_FOLDER, tarea.nombre_archivo))
            resp = jsonify({'message' : 'Los archivos fueron eliminados'})
            resp.status_code = 204
            return resp
        else:
            resp = jsonify({'message' : 'Los archivos no existen'})
            resp.status_code = 400
            return resp
        
        