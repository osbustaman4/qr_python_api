import bcrypt
import jwt

from jwt import decode

class JWT_Tokens:

    @classmethod
    def encrypt(self, pass_user):
        salt_rounds = 10
        # Generar una salt aleatoria y encriptar la contraseña
        salt = bcrypt.gensalt(rounds=salt_rounds)
        hashed_password = bcrypt.hashpw(pass_user.encode('utf-8'), salt)
        return hashed_password
    

    @classmethod
    def encode_token_jwt(self, token):
        
        try:
            token = token.split(' ')[1]
            # Decodifica el token y obtén el payload
            payload = jwt.decode(token, options={"verify_signature": False})  # El parámetro "verify_signature" se establece en False para omitir la verificación de la firma. Puedes configurarlo según tus necesidades.
            return payload
        except jwt.ExpiredSignatureError:
            print("El token ha expirado.")
            return None
        except jwt.InvalidTokenError:
            print("Token no válido.")
            return None