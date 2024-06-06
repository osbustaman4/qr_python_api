import base64
import tempfile
import traceback

import cv2  # OpenCV para manipulación de imágenes
from pyzbar.pyzbar import decode  # pyzbar para decodificar códigos QR
from PIL import Image  # Pillow para manipulación de imágenes

from datetime import date, datetime, timedelta
from flask import Blueprint, request, jsonify, send_file, Response

from lib.Stech import Validate
from src.utils.Utils import Utils


main_read_image_code = Blueprint('main_read_image_code', __name__)

@main_read_image_code.route('/', methods=['POST'])
def read_image_code():

    try:
        # Obtenemos la imagen en base64
        data = request.json

        data = request.get_json()
        error_validate, is_validate = Validate.validate_json_keys(data)
        if is_validate:
            raise ValueError(error_validate)

        image = data['image64']

        # Decodificamos la imagen
        image_decode = base64.b64decode(image)
        # Guardamos la imagen decodificada en un archivo temporal
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(image_decode)
            temp_path = temp.name

        # Leer el código QR de la imagen temporal
        qr_result = leer_qr(temp_path)
        
        # Crear el JSON de respuesta
        response = {
            "success": True,
            "qr_result": qr_result
        }
        
        return jsonify(response), 200
    except ValueError as ex:
        return Utils.create_response(str(ex), False, 404)

    except Exception as ex:
        message = f"{str(ex)} - {str(traceback.format_exc())}"
        return Utils.create_response(message, False, 500)
    


# Función para ajustar la imagen antes de decodificar el código QR
def procesar_imagen(ruta_imagen):
    # Leer la imagen
    imagen = cv2.imread(ruta_imagen)
    
    # Convertir a escala de grises
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    
    # Aplicar filtro de desenfoque para reducir el ruido
    desenfoque = cv2.GaussianBlur(gris, (5, 5), 0)
    
    # Aplicar umbral para mejorar el contraste
    _, umbralizada = cv2.threshold(desenfoque, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return umbralizada


# Función para decodificar un código QR desde una imagen procesada
def leer_qr(ruta_imagen):
    # Procesar la imagen
    imagen_procesada = procesar_imagen(ruta_imagen)
    
    # Decodificar el código QR en la imagen
    decodificaciones = decode(imagen_procesada)
    
    # Si se encontró al menos un código QR
    if decodificaciones:
        # Retornar el dato decodificado del primer código QR encontrado
        return {
            "success": True,
            "message": decodificaciones[0].data.decode('utf-8')
        }
    else:
        # Si no se encontró ningún código QR
        return {
            "success": False,
            "message": "No se encontró ningún código QR en la imagen"
        }





