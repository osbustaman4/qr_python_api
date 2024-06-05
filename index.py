from app_config import configure
from src import init_app
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

configuration = configure['development']
app = init_app(configuration)

# Agregar esta línea para definir la variable 'application'
application = app

if __name__ == '__main__':
    #load_dotenv()
    app.run(host='0.0.0.0', port=5000)
    # app.run(host='192.168.100.16', port=5000)