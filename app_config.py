from decouple import config

class Config():
    SECRET_KEY = config('SECRET_KEY')

class DevelopmentConfig(Config):
    DEBUG = True

configure = {
    'development': DevelopmentConfig
}


DATABASES = {
    
}