from flask import request, jsonify, send_from_directory
from modelos import db, Tarea, Usuario, UsuarioSchema, TareaSchema, EstadoTarea
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from datetime import datetime
from werkzeug.utils import secure_filename
from .utils import *
from google.cloud import pubsub_v1

import os
import queue

ALLOWED_EXTENSIONS = set(['mp3', 'wav', 'ogg'])
UPLOAD_FOLDER = '.'
#UPLOAD_FOLDER = '../archivos_audio'
BUCKET_NAME = 'archivos_audio'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


tarea_schema = TareaSchema()
usuario_schema = UsuarioSchema()


class VistaSignIn(Resource):
    
    def post(self):
        nuevo_usuario = Usuario(usuario=request.json["usuario"], contrasena=request.json["contrasena"], correo = request.json["correo"])
        token_de_acceso = create_access_token(identity=request.json["usuario"])
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
            return {"mensaje":"Acceso concedido", "usuario": {"usuario": usuario.usuario, "id": usuario.id}, "token": token_de_acceso}
        else:
            return {'mensaje':'Nombre de usuario o contraseña incorrectos'}, 401


class VistaTareas(Resource):

    @jwt_required()
    def get(self):
        usuario = Usuario.query.filter_by(usuario = get_jwt_identity()).first()
        
        if usuario == None:
            resp = jsonify({'message' : 'Usuario no identificado'})
            resp.status_code = 401
            return resp
        
        id_usuario = usuario.id
        return [tarea_schema.dump(tarea) for tarea in Tarea.query.filter(Tarea.id_usuario == id_usuario).all()]
    
    @jwt_required()
    def post(self):
        usuario = Usuario.query.filter_by(usuario = get_jwt_identity()).first()
        
        if usuario == None:
            resp = jsonify({'message' : 'Usuario no identificado'})
            resp.status_code = 401
            return resp
        
        id_usuario = usuario.id
        
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
                #file.save(os.path.join(UPLOAD_FOLDER, filename))                
                success = upload_to_bucket(filename,file,BUCKET_NAME)
                #success = upload_to_bucket(filename,os.path.join(UPLOAD_FOLDER, filename),BUCKET_NAME)
                #os.remove(os.path.join(UPLOAD_FOLDER, filename))
            else:
                errors['message'] = 'File type is not allowed or file not specified'
        print(success,errors)
        
        if request.form['newFormat'].lower() not in ALLOWED_EXTENSIONS:
            errors['message'] = 'Format to convert type is not allowed'
            resp = jsonify(errors)
            resp.status_code = 400
            return resp
        
        if success:            
            nueva_tarea = Tarea(id_usuario = id_usuario, estado="UPLOADED", nombre_archivo= filename, formato_destino=request.form['newFormat'].upper())
            db.session.add(nueva_tarea)

            try:
                db.session.commit()
                publicar_mensaje(nueva_tarea)
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
        usuario = Usuario.query.filter_by(usuario = get_jwt_identity()).first()
        
        if usuario == None:
            resp = jsonify({'message' : 'Usuario no identificado'})
            resp.status_code = 401
            return resp
        
        id_usuario = usuario.id
        tarea =[tarea_schema.dump(tarea) for tarea in Tarea.query.filter(Tarea.id_usuario == id_usuario,Tarea.id == id_tarea).all()]
        print(tarea)
        if tarea == []:
            resp = jsonify({'message' : 'La tarea no fue encontrada'}) 
            resp.status_code = 404
            return resp
        return tarea

    @jwt_required()
    def delete(self, id_tarea):
        usuario = Usuario.query.filter_by(usuario = get_jwt_identity()).first()
        
        if usuario == None:
            resp = jsonify({'message' : 'Usuario no identificado'})
            resp.status_code = 401
            return resp
        
        id_usuario = usuario.id
        tarea = Tarea.query.filter(Tarea.id_usuario == id_usuario,Tarea.id == id_tarea).first()
        
        if tarea != None:
            archivo_original = tarea.nombre_archivo.split(".")
            formato_destino = str(tarea.formato_destino)        
            nombre_archivo_converido = archivo_original[0] + '.' +  formato_destino.split(".")[1].lower()
        else :
            resp = jsonify({'message' : 'Los archivos / tarea no existen'})
            resp.status_code = 404
            return resp

        if tarea.estado == EstadoTarea.PROCESSED:
            if check_blob_exists(tarea.nombre_archivo,BUCKET_NAME) and \
                check_blob_exists(nombre_archivo_converido,BUCKET_NAME):

                delete_blob(tarea.nombre_archivo,BUCKET_NAME)
                delete_blob(nombre_archivo_converido,BUCKET_NAME)
                db.session.delete(tarea)
                db.session.commit()
                
                resp = jsonify({'message' : 'Los archivos fueron eliminados'})
                resp.status_code = 204
                return resp
            else:
                resp = jsonify({'message' : 'Los archivos no existen'})
                resp.status_code = 404
                return resp
        else:
            resp = jsonify({'message' : 'Los archivos todavia se estan procesando'}) 
            resp.status_code = 400
            return resp
        
    @jwt_required()
    def put(self, id_tarea):
        try:
            usuario = Usuario.query.filter_by(usuario = get_jwt_identity()).first()
            
            if usuario == None:
                resp = jsonify({'message' : 'Usuario no identificado'})
                resp.status_code = 401
                return resp
        
            id_usuario = usuario.id
            
            tarea_actualizar = Tarea.query.filter(Tarea.id_usuario == id_usuario, Tarea.id == id_tarea).first()
            errors = {}            
            if tarea_actualizar.estado == EstadoTarea.PROCESSED and check_blob_exists(tarea_actualizar.nombre_archivo,BUCKET_NAME):
                archivo_original = tarea_actualizar.nombre_archivo.split(".")
                formato_destino = str(tarea_actualizar.formato_destino)        
                nombre_archivo_converido = archivo_original[0] + '.' +  formato_destino.split(".")[1].lower()

                #os.remove(os.path.join(UPLOAD_FOLDER, nombre_archivo_converido))                
                delete_blob(nombre_archivo_converido,BUCKET_NAME)
 
                tarea_actualizar.formato_destino = request.json.get("newFormat", tarea_actualizar.formato_destino)
                tarea_actualizar.estado = EstadoTarea.UPLOADED
                try:
                    db.session.commit()
                    publicar_mensaje(tarea_actualizar)
                    return "El formato fue actualizado"
                except IntegrityError:
                    db.session.rollback()
                    return 'El formato no pudo ser actualizado'
            else:
                return 'File type is not allowed or file not specified'
        except:
            return {"Message": "No task found"}

class VistaArchivo(Resource):
    @jwt_required()
    def get(self, filename):
        
        errors = {}        
        found = download_from_bucket(filename,os.path.join(UPLOAD_FOLDER, filename),BUCKET_NAME)
        print(found)
        if found == False:
            errors['message'] = 'File not found'            
            resp = jsonify(errors)
            resp.status_code = 404
            return resp
        else:
            for file in os.listdir(UPLOAD_FOLDER):
                if str(filename) in file:
                    print(file)
                    found = True
                    file_to_send = send_from_directory(UPLOAD_FOLDER, file, mimetype='audio/mpeg', as_attachment=True, attachment_filename=filename)
                    os.remove(os.path.join(UPLOAD_FOLDER, filename))
                    return file_to_send       


def publicar_mensaje(nueva_tarea):
    #credentials_path = '../pubsub-service-key.json'
    credentials_path = 'desarrollo-cloud-368422.json'
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    publisher = pubsub_v1.PublisherClient()
    topic_path = 'projects/desarrollo-cloud-368422/topics/async-webapp-worker'
    attributes = {
        'id' : str(nueva_tarea.id),
        'nombre_archivo': str(nueva_tarea.nombre_archivo),
        'formato_destino': str(nueva_tarea.formato_destino.name),
        'id_usuario': str(nueva_tarea.id_usuario)
        }
    data = str(nueva_tarea.id)
    data = data.encode('utf-8')
    future = publisher.publish(topic_path, data, **attributes)
    print(f"Published message id: {future.result()}")
