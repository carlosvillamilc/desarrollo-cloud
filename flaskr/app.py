#from flaskr import create_app
from flask import Flask
from flask_restful import Api
from modelos import db
from vistas import VistaSignIn, VistaLogIn, VistaTareas, VistaTarea, VistaArchivo
from flask_jwt_extended import JWTManager
from flask_cors import CORS

#from modelos import *
#from vistas import *
#app = create_app('default')

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://newuser:1234@localhost:5432/cloud_conversion_tool'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://conversiontool:conversiontool@db:5432/conversiontool'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY']='secretisimo'
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['UPLOAD_FOLDER'] = "/"

app_context = app.app_context()
app_context.push()


db.init_app(app)
db.create_all()

cors = CORS(app)

api = Api(app)
api.add_resource(VistaSignIn, '/api/auth/signup')
api.add_resource(VistaLogIn, '/api/auth/login')
api.add_resource(VistaTareas, '/api/tasks')
api.add_resource(VistaTarea, '/api/tasks/<int:id_tarea>')
api.add_resource(VistaArchivo, '/api/files/<filename>')

jwt = JWTManager(app)