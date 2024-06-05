import base64
import json
import random
import tempfile
import traceback
import os
import requests
import hashlib
import hmac

from datetime import date, datetime, timedelta
from decouple import config as load_data
from flask import request, jsonify, Blueprint
from lib.Email import EmailSender
from lib.ExceptionsHTTP import HTTP404Error
from lib.Stech import Logger, Stech, Validate
from lib.ExceptionsJson import ExceptionsJson

from src.decorators import verify_user_fcm
from sqlalchemy import desc, literal
from sqlalchemy import Integer, String, update, func, and_, or_, case, Date, cast, literal_column, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import aliased

from datetime import datetime

from src.utils.FCM import send_push_notification
from src.utils.Utils import Utils, Utils_Mails

# main_funcion_ejemplo = Blueprint('funcion_ejemplo', __name__)



@main_funcion_ejemplo.route('/', methods=['POST'])
@verify_user_fcm
def funcion_ejemplo():
    try:

		session = Stech.get_session(load_data('ENVIRONMENTS'))
		
        data = request.get_json()
        error_validate, is_validate = Validate.validate_json_keys(data)
        if is_validate:
            raise ValueError(error_validate)


        response = {
            "success": True
        }
        return jsonify(response), 200

    except ValueError as ex:
        return Utils.create_response(str(ex), False, 404)

    except SQLAlchemyError as ex:
        return Utils.create_response(str(ex), False, 500)

    except Exception as ex:
        message = f"{str(ex)} - {str(traceback.format_exc())}"
        return Utils.create_response(message, False, 500)
    