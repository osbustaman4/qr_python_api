from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint

from decouple import config as config_environment

from src import api as api
from flask_cors import CORS

app = Flask(__name__)
# CORS(app)
CORS(app, resources={r"/*": {"origins": "*"}})

try:
    if config_environment('ENVIRONMENTS') == "desarrollo":
        # swagger configs
        SWAGGER_URL = '/swagger'
        API_URL = '/static/swagger.json'
    else:
        SWAGGER_URL = '/'
        API_URL = ''
except Exception as e:
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

    
    app.register_blueprint(api.main_read_image_code, url_prefix='/read-img-qr')
    
    return app