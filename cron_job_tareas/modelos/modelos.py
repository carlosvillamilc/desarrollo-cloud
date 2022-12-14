import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
import enum

db = SQLAlchemy()

@enum.unique            
class EstadoTarea(int, enum.Enum):
    UPLOADED: int = 1                                      
    PROCESSED: int = 2
    
@enum.unique            
class Formato(int, enum.Enum):
    MP3: int = 1                                      
    WAV: int = 2
    OGG: int = 3
    
    def toCadena(self):
        return self.name[8:]

class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    nombre_archivo = db.Column(db.String)
    estado = db.Column(db.Enum(EstadoTarea))
    formato_destino = db.Column(db.Enum(Formato))
    fecha_hora = db.Column(DateTime, default=datetime.datetime.utcnow)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(30))
    contrasena = db.Column(db.String(50))
    correo = db.Column(db.String())
    tareas = db.relationship('Tarea', cascade='all, delete, delete-orphan')# para que si un usuario que tiene una tarea es eliminado, las tareas de ese usuario también sean eliminados