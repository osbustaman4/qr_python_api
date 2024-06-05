from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint

from decouple import config as config_environment

from src import api as api
from src import api_carcloud as api_carcloud
from src import api_company as api_company
from flask_cors import CORS

app = Flask(__name__)
# CORS(app)
CORS(app, resources={r"/*": {"origins": "*"}})

if config_environment('ENVIRONMENTS') == "desarrollo":
    # swagger configs
    SWAGGER_URL = '/swagger'
    API_URL = '/static/swagger.json'
else:
    SWAGGER_URL = '/'
    API_URL = ''

SWAGGER_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name' : "Todo Lista Endpoints"
    }
)

app.register_blueprint(SWAGGER_BLUEPRINT, url_prefix = SWAGGER_URL)

def init_app(config):
    app.config.from_object(config)

    # GARAGE
    # app.register_blueprint(api.main_list_garage, url_prefix='/listado-garage')
    
    return app