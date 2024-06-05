import cv2  # OpenCV para manipulación de imágenes
from pyzbar.pyzbar import decode  # pyzbar para decodificar códigos QR
from PIL import Image  # Pillow para manipulación de imágenes


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
        return decodificaciones[0].data.decode('utf-8')
    else:
        # Si no se encontró ningún código QR
        return None

# Ruta de la imagen que contiene el código QR
ruta_imagen_1 = '/home/osbustaman/PROYECTOS/QR/img/vin_1.png'
ruta_imagen_2 = '/home/osbustaman/PROYECTOS/QR/img/vin_2.png'
ruta_imagen_3 = '/home/osbustaman/PROYECTOS/QR/img/vin_3.png'
ruta_imagen_4 = '/home/osbustaman/PROYECTOS/QR/img/vin_4.png'
ruta_imagen_5 = '/home/osbustaman/PROYECTOS/QR/img/img.png'

# Leer y decodificar el código QR
resultado1 = leer_qr(ruta_imagen_1)
resultado2 = leer_qr(ruta_imagen_2)
resultado3 = leer_qr(ruta_imagen_3)
resultado4 = leer_qr(ruta_imagen_4)
resultado5 = leer_qr(ruta_imagen_5)

print("Resultado 1:", resultado1)
print("Resultado 2:", resultado2)
print("Resultado 3:", resultado3)
print("Resultado 4:", resultado4)
print("Resultado 5:", resultado5)


