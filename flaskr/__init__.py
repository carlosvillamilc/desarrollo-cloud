from flask import Flask

def create_app(config_name):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cloud_conversion_tool.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY']='secretisimo'
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['UPLOAD_FOLDER'] = "/archivos_audio"
    return app