# Importamos las librerías necesarias.

import cv2
import numpy as np
import base64
import os
import tempfile
import traceback

from pyzbar import pyzbar
from PIL import Image  # Pillow para manipulación de imágenes
from argparse import ArgumentParser
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

        # Leemos la imagen de entrada.
        image = cv2.imread(temp_path)

        # Preprocesamos la imagen para mejorar la detección.
        preprocessed_image = preprocess_image(image)

        # Extraemos los códigos de barra de la imagen.
        barcodes = detect_and_decode(preprocessed_image)

        # Dibujamos los códigos de barra/QR en la imagen original.
        qr_result = draw_barcodes(image, barcodes)

        # Cuando hayas terminado de usar el archivo temporal, puedes eliminarlo así:
        os.remove(temp_path)
        
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
    

def preprocess_image(image):
    """
    Apply preprocessing to the image to improve barcode/QR code detection.
    Convert the image to grayscale, adjust contrast, and apply rotation correction.
    """
    # Convertimos a escala de grises
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Ajustamos el contraste y brillo (puedes ajustar estos valores)
    alpha = 1.5  # Contraste
    beta = 0.5     # Brillo
    contrast_adjusted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
    
    # Aplicamos un filtro de suavizado para reducir el ruido
    blurred = cv2.GaussianBlur(contrast_adjusted, (5, 5), 0)
    
    # Realizamos la binarización de la imagen
    _, binary = cv2.threshold(blurred, 100, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Detectar y corregir la inclinación
    binary = correct_rotation(binary)
    
    return binary

def correct_rotation(image):
    """
    Detect and correct rotation of the image.
    """
    # Detectar bordes en la imagen
    edges = cv2.Canny(image, 60, 150, apertureSize=3)
    print(edges)
    
    # Detectar líneas en la imagen
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    angle = 0
    
    if lines is not None:
        # Calcular el ángulo promedio de las líneas detectadas
        angles = [np.degrees(np.arctan2(line[0][1], line[0][0])) for line in lines]
        angle = np.mean(angles)
    
    # Rotar la imagen para corregir la inclinación
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return rotated

def detect_and_decode(image):
    """
    Detect and decode barcodes/QR codes in the given image.
    """
    barcodes = pyzbar.decode(image)
    return barcodes

def draw_barcodes(image, barcodes):
    """
    Draw rectangles and add text labels on the detected barcodes/QR codes.
    """
    code_response = []

    for i, barcode in enumerate(barcodes, start=1):
        x, y, width, height = barcode.rect
        cv2.rectangle(image, (x, y), (x + width, y + height), (0, 0, 255), 2)
        
        data = barcode.data.decode('utf-8')
        type_ = barcode.type
        
        text = f'{data} ({type_})'
        code_response.append({
            "data": data,
            "type": type_
        })
        cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 255), 2)

    return code_response

