import base64
import hashlib
import json
import logging
import os
import platform
import re
import traceback
import secrets
import string
import subprocess
# import boto3
import pexpect
import paramiko
import locale

from app_config import DATABASES
from decouple import config as config_environment

from sqlalchemy import create_engine, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

from lib.ConnectionGoogle import GoogleSFTPConnection

class HTTP404Error(Exception):
    def __init__(self, message="HTTP 404 - Not Found"):
        self.message = message
        super().__init__(self.message)


class HTTP500Error(Exception):
    def __init__(self, message="HTTP 500 - Internal Server Error"):
        self.message = message
        super().__init__(self.message)

class Logger():

    def __set_logger(self, client):
        log_directory = config_environment('LOG_DIRECTORY')
        log_filename = f'{client}.log'

        # Obtener el nombre del sistema operativo
        operating_system = platform.system()
        if operating_system == "Linux":
            # Comando para cambiar los permisos
            chmod_command = f"sudo chmod -R u+rwx {log_directory}"

            # Ejecutar el comando en la terminal
            subprocess.run(chmod_command, shell=True)

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        log_path = os.path.join(log_directory, log_filename)
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', "%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)

        if (logger.hasHandlers()):
            logger.handlers.clear()

        logger.addHandler(file_handler)

        return logger

    @classmethod
    def add_to_log(self, level, message, client='log'):
        try:
            logger = self.__set_logger(self, client)

            if (level == "critical"):
                logger.critical(message)
            elif (level == "debug"):
                logger.debug(message)
            elif (level == "error"):
                logger.error(message)
            elif (level == "info"):
                logger.info(message)
            elif (level == "warn"):
                logger.warn(message)
            elif (level == "success"):
                logger.info(message)
        except Exception as ex:
            print(traceback.format_exc())
            print(ex)

class Validate():

    @classmethod
    def validate_json_keys(self, json_data, array_no_required=[]):
        """
        Valida un JSON asegurándose de que todos los campos tengan un valor.

        Parameters:
        - json_data: El JSON a validar.
        - array_no_required: Arreglo de key que no son requeridos.

        Raises:
        - ValueError: Si se encuentra algún campo sin valor.

        Returns:
        - Tuple: Una tupla que contiene el mensaje de error y un indicador de éxito.
        """
        for key, value in json_data.items():
            if key not in array_no_required:
                if value is None or (isinstance(value, str) and value.strip() == ''):
                    return f'El campo "{key}" no tiene un valor válido.', True
        return None, False

class Stech():

    Base = declarative_base()

    MEDIA_TYPE_STATIC_FORMAT = [
        "gif"
        , "jpg"
        , "jpeg"
        , "png"
        , "mp4"
    ]


    @classmethod
    def format_to_set_locale_peso(number, set_locale='es_CL.UTF-8'):
        """
        Format a number as Chilean peso.

        - es_CL.UTF-8'

        Args:
            number (float): The number to be formatted.
            set_locale (str, optional): The locale to be used for formatting. Defaults to 'es_CL.UTF-8'.

        Returns:
            str: The formatted number as Chilean peso.

        """
        # Set the locale for Chile
        locale.setlocale(locale.LC_ALL, set_locale)

        # Format the number as Chilean peso
        formatted_number = locale.currency(number, grouping=True)

        return formatted_number


    @classmethod
    def validate_rut(self, rut):
            """
            Validates a Chilean RUT (Rol Único Tributario) number.

            Args:
                rut (str): The RUT number to be validated.

            Returns:
                bool: True if the RUT is valid, False otherwise.
            """
            rut = rut.replace(".", "").replace("-", "")
            if not re.match(r'^\d{1,8}[0-9K]$', rut):
                return False
            rut_not_dv = rut[:-1]
            dv = rut[-1].upper()
            multiplier = 2
            _sum = 0
            for r in reversed(rut_not_dv):
                _sum += int(r) * multiplier
                multiplier += 1
                if multiplier == 8:
                    multiplier = 2
            _rest = _sum % 11
            dv_calculated = 11 - _rest
            if dv_calculated == 11:
                dv_calculated = '0'
            elif dv_calculated == 10:
                dv_calculated = 'K'
            else:
                dv_calculated = str(dv_calculated)
            return dv == dv_calculated


    def validate_mail(self, email):
            """
            Valida si una dirección de correo electrónico es válida.

            Args:
                correo (str): La dirección de correo electrónico a validar.

            Returns:
                bool: True si la dirección de correo electrónico es válida, False en caso contrario.
            """
            compiled_model = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

            compiled_model = re.compile(compiled_model)

            if compiled_model.match(email):
                return True
            else:
                return False


    @classmethod
    def get_session(self, connection_name):
        """
        Returns a session object for the specified database connection.

        Args:
            connection_name (str): The name of the database connection.

        Returns:
            Session: A session object for the specified database connection.
        """

        # Recuperar la conexión según el nombre dado
        data = DATABASES[connection_name]

        DB_HOST = data['DB_HOST']
        DB_USER = data['DB_USER']
        DB_PASSWORD = data['DB_PASSWORD']
        DB_PORT = data['DB_PORT']
        DB_NAME = data['DB_NAME']
        DB_TYPE = data['DB_TYPE']

        encoded_password = quote_plus(DB_PASSWORD)
        connection_string = f"{DB_TYPE}://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(connection_string, pool_pre_ping=True, poolclass=pool.NullPool)
        Session = sessionmaker(bind=engine)
        
        # Retorna la sesión
        return Session()


    @classmethod
    #def object_to_json(self, headers_list, tuplas_list, query_list):
    def object_to_json(self, query_object, type_object="list"):
        """
        Converts a query object to a JSON list.

        Args:
            query_object (list): The query object to be converted.

        Returns:
            list: A list of JSON objects representing the query object.
        """

        if not query_object:
            return []
        
        list_to_json = []
        headers_list = query_object[0]._fields
        tuplas_list = query_object

        for tupla in tuplas_list:
            object_json = {}
            for i in range(len(headers_list)):
                object_json[headers_list[i]] = tupla[i]
            list_to_json.append(object_json)

        return list_to_json
    

    @classmethod
    def make_password(self, password):
        
        # Generar una sal aleatoria
        characters = string.ascii_letters + string.digits + string.punctuation
        salt = ''.join(secrets.choice(characters) for i in range(12))  # Sal de 12 caracteres

        # Combinar la contraseña y la sal
        password_with_salt = password + salt

        # Aplicar el algoritmo de hash (en este caso, SHA-256)
        hashed_password = hashlib.sha256(password_with_salt.encode()).hexdigest()

        # Retornar la contraseña encriptada junto con la sal
        return f"{hashed_password}${salt}"
    
    
    @classmethod
    def validate_email_format(self, email):
        # Expresión regular para validar un formato básico de correo electrónico
        email_regex = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'

        # Verificar si el correo electrónico coincide con la expresión regular
        return bool(re.match(email_regex, email))
    
    @classmethod
    def go_up_to_root_directory(self, image, file_name):
        """
        Guarda una imagen en el directorio raíz del proyecto
        @param current_file_path: Directorio actual
        @param file_name: Nombre del archivo
        @param image: Imagen en base64
        """
        try:
            print(file_name)
            route_static = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','src', 'static'))
            if not os.path.exists(route_static):
                os.makedirs(route_static)

            # Guardar la imagen decodificada en el directorio especificado
            with open(os.path.join(route_static, file_name), 'wb') as archivo_salida:
                archivo_salida.write(image)

            return True

        except Exception as ex:
            Logger.add_to_log("error", f"go_up_to_root_directory_base64: {str(ex)}")
            Logger.add_to_log("error", traceback.format_exc())
            
            return False
        
    # @classmethod
    # def go_up_to_root_directory_S3(self, image, name_file, directorio_destino):

    #     try:
    #         content_type = self.get_content_type(name_file)
    #         _name_file = name_file

    #         s3_client = boto3.resource(
    #             's3', 
    #             aws_access_key_id=config_environment('ENV_AWS_ACCESS_KEY_IS'), 
    #             aws_secret_access_key=config_environment('ENV_AWS_SECRET_ACCESS_KEY'), 
    #             region_name=config_environment('ENV_AWS_REGION_NAME')
    #         )

    #         name_file = os.path.join(directorio_destino, name_file)
    #         s3_client.Bucket(config_environment('ENV_AWS_S3_BUCKET_NAME')).put_object(
    #             Key=name_file
    #             , Body=image
    #             , ContentType=content_type
    #             , ContentDisposition=f'inline; filename="{_name_file}"'
    #         )

    #         url_s3 = f"https://s3.amazonaws.com/{config_environment('ENV_AWS_S3_BUCKET_NAME')}/{name_file}"

    #         return url_s3
        
    #     except Exception as ex:
    #         Logger.add_to_log("error", f"go_up_to_root_directory_base64: {str(ex)}")
    #         Logger.add_to_log("error", traceback.format_exc())
            
    #         return False
        

    @classmethod
    def update_image_google_sftp(self, file_name, position_image, extra=None, extra_twoo=None):
        
        
        # Obtén la ruta del archivo .pem

        route_file_key = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','src', 'static', config_environment("ENV_GOOGLE_SFTP_ROUTE_PPK_PEM")))
        route_static = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','src', 'static', file_name))

        try:

            if extra_twoo == 'reportesApp':
                google_sftp = config_environment('ENV_GOOGLE_SFTP_REMOTE_PATH') + "/" + extra.upper()
                file_name = file_name.split("/")[len(file_name.split("/")) - 1]
            else:
                google_sftp = config_environment('ENV_GOOGLE_SFTP_REMOTE_PATH_DINAMIC') + extra_twoo + "/" + extra.upper()
                file_name = "img" + str(position_image) + ".jpg"

            if_upload = self.connect_sftp(route_file_key, route_static, google_sftp, file_name)

            if if_upload:
                return True
            else:
                return False

        except Exception as ex:
            print(f"Error en la conexión SFTP: {str(ex)}")
            return False

        

    @classmethod
    def connect_sftp(self, route_file_key, route_static, google_sftp, file_name):

        ip = config_environment("ENV_GOOGLE_SFTP_IP")
        user = config_environment("ENV_GOOGLE_SFTP_USER")

        try:
            # Crear una instancia de SSHClient
            cliente_ssh = paramiko.SSHClient()

            connection = GoogleSFTPConnection(ip, user, route_file_key)
            connection.connect()
            connection.upload_file(route_static, f"{google_sftp}", file_name)
            connection.disconnect()
                        # Cerrar la conexión SSH
            cliente_ssh.close()
            return True
        except Exception as ex:
            print(f"Error en la conexión SFTP: {str(ex)}")
            return False
        
        finally:
            # Cerrar la conexión SSH
            cliente_ssh.close()

    def get_content_type(file_name):
        """
        Obtiene el tipo de contenido (Content-Type) basado en la extensión del archivo.

        Parameters:
        - file_name: El nombre del archivo.

        Returns:
        - El tipo de contenido correspondiente a la extensión del archivo.
        """
        
        _, file_extension = os.path.splitext(file_name.lower())
        content_type_mapping = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.mp4': 'video/mp4'
        }
        return content_type_mapping.get(file_extension, 'application/octet-stream')

    
