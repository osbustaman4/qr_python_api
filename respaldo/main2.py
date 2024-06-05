import cv2
import numpy as np
from pyzbar.pyzbar import decode

def ajustar_perspectiva(imagen, contorno):
    puntos = contorno.reshape(4, 2)
    puntos_ordenados = np.zeros((4, 2), dtype="float32")
    
    s = np.sum(puntos, axis=1)
    puntos_ordenados[0] = puntos[np.argmin(s)]
    puntos_ordenados[2] = puntos[np.argmax(s)]
    
    diff = np.diff(puntos, axis=1)
    puntos_ordenados[1] = puntos[np.argmin(diff)]
    puntos_ordenados[3] = puntos[np.argmax(diff)]
    
    (tl, tr, br, bl) = puntos_ordenados
    ancho = max(
        np.linalg.norm(br - bl),
        np.linalg.norm(tr - tl)
    )
    alto = max(
        np.linalg.norm(tr - br),
        np.linalg.norm(tl - bl)
    )
    
    destino = np.array([
        [0, 0],
        [ancho - 1, 0],
        [ancho - 1, alto - 1],
        [0, alto - 1]], dtype="float32")
    
    matriz_transformacion = cv2.getPerspectiveTransform(puntos_ordenados, destino)
    imagen_transformada = cv2.warpPerspective(imagen, matriz_transformacion, (int(ancho), int(alto)))
    
    return imagen_transformada

def corregir_perspectiva(imagen):
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    _, umbralizada = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    contornos, _ = cv2.findContours(umbralizada, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    max_area = 0
    mejor_contorno = None
    for contorno in contornos:
        epsilon = 0.02 * cv2.arcLength(contorno, True)
        aproximacion = cv2.approxPolyDP(contorno, epsilon, True)
        if len(aproximacion) == 4:
            area = cv2.contourArea(aproximacion)
            if area > max_area:
                mejor_contorno = aproximacion
                max_area = area

    if mejor_contorno is not None:
        return ajustar_perspectiva(imagen, mejor_contorno)
    else:
        return imagen

def procesar_imagen(ruta_imagen):
    imagen = cv2.imread(ruta_imagen)
    
    imagen_corregida = corregir_perspectiva(imagen)
    
    gris = cv2.cvtColor(imagen_corregida, cv2.COLOR_BGR2GRAY)
    desenfoque = cv2.GaussianBlur(gris, (5, 5), 0)
    _, umbralizada = cv2.threshold(desenfoque, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    kernel = np.ones((3, 3), np.uint8)
    apertura = cv2.morphologyEx(umbralizada, cv2.MORPH_OPEN, kernel)
    cierre = cv2.morphologyEx(apertura, cv2.MORPH_CLOSE, kernel)
    
    return cierre

def leer_qr(ruta_imagen):
    imagen_procesada = procesar_imagen(ruta_imagen)
    decodificaciones = decode(imagen_procesada)
    
    if decodificaciones:
        return decodificaciones[0].data.decode('utf-8')
    else:
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
