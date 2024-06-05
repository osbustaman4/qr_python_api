import firebase_admin
import os

from decouple import config
from firebase_admin import credentials, auth, messaging


class FirebaseNotification:

    def __init__(self):
        self.ruta_script = os.path.abspath(__file__)
        self.ruta_base = os.path.dirname(self.ruta_script)
        self.ruta_static_firebase = str(self.ruta_base).replace("utils", "static")
        self.file_firebase = config("API_URL_FIREBASE")
        self.ruta_firebase = os.path.join(self.ruta_static_firebase, self.file_firebase)
        self.cred = credentials.Certificate(self.ruta_firebase)
        self.firebase_admin = firebase_admin.initialize_app(self.cred, {
                                    'databaseURL': "https://recuperauto-75050.firebaseio.com"
                                })

    @staticmethod
    def send_push_notification(self, data):
        
        list_tokens = data["list_tokens"]
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=data["title"],
                body=data["body"]
            ),
            tokens=list_tokens
        )

        try:
            response = messaging.send_multicast(message)
            print('Successfully sent message:', response)
            return response
        except Exception as e:
            print('Error sending message:', e)
            return str(e)