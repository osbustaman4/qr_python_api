from decouple import config

class Config():
    SECRET_KEY = config('SECRET_KEY')

class DevelopmentConfig(Config):
    DEBUG = True

configure = {
    'development': DevelopmentConfig
}


DATABASES = {
    config('ENVIRONMENTS'): {
        'DB_HOST': config('DB_HOST'),
        'DB_USER': config('DB_USER'),
        'DB_PASSWORD': config('DB_PASSWORD'),
        'DB_PORT': config('DB_PORT'),
        'DB_NAME': config('DB_NAME'),
        'DB_TYPE': config('DB_TYPE'),
    },
    config('ENVIRONMENTS_CC'): {
        'DB_HOST': config('DB_HOST_CC'),
        'DB_USER': config('DB_USER_CC'),
        'DB_PASSWORD': config('DB_PASSWORD_CC'),
        'DB_PORT': config('DB_PORT_CC'),
        'DB_NAME': config('DB_NAME_CC'),
        'DB_TYPE': config('DB_TYPE_CC'),
    },
    config('ENVIRONMENTS_EMPRESAS'): {
        'DB_HOST': config('DB_HOST_EMPRESAS'),
        'DB_USER': config('DB_USER_EMPRESAS'),
        'DB_PASSWORD': config('DB_PASSWORD_EMPRESAS'),
        'DB_PORT': config('DB_PORT_EMPRESAS'),
        'DB_NAME': config('DB_NAME_EMPRESAS'),
        'DB_TYPE': config('DB_TYPE_EMPRESAS'),
    },
}