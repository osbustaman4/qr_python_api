import traceback
import firebase_admin
import os
import json
import socket
import datetime

from decouple import config
from firebase_admin import credentials, messaging



# Obten la ruta del directorio del script actual (donde se encuentra el archivo actual)
ruta_script = os.path.abspath(__file__)

# Obten la ruta base de la aplicación
ruta_base = os.path.dirname(ruta_script)

# Ruta relativa a la carpeta "static"

ruta_static_firebase = str(ruta_base).replace("utils", "static")
file_firebase = config("API_URL_FIREBASE")

ruta_firebase = os.path.join(ruta_static_firebase, file_firebase)

# Inicializar la aplicación de Firebase con tu archivo de credenciales
cred = credentials.Certificate(ruta_firebase)
admin = firebase_admin.initialize_app(cred, {
    'databaseURL': "https://recuperauto-75050.firebaseio.com"
})






def send_push_notification(data):

    respuestas = []
    for index, datos in enumerate(data):
        mensaje = {
            'notification': {
                'title': datos['title'],
                'body': datos['body'],
                'sound': ''
            },
        }

        if 'data' in datos:
            mensaje['data'] = datos['data']

        options = messaging.AndroidConfig(
            priority='high',
            ttl=datetime.timedelta(hours=24)
        )

        try:
            messaging.send_multicast(
                registration_tokens=[datos['fcm']],
                data=mensaje['data'],
                notification=mensaje['notification'],
                android=options
            )
            respuestas.append(f'Enviado: N°_{index + 1}')

        except Exception as error:
            respuestas.append(f'Error: {error}')

    return respuestas
