import random
from sqlalchemy import desc, literal
from sqlalchemy import Integer, String, update, func, and_, or_, case, Date, cast, literal_column, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import aliased
from lib.Stech import Stech
from decouple import config as load_data


session = Stech.get_session(load_data('ENVIRONMENTS'))

marcas_autos = ["Toyota", "Honda", "Ford"]
modelos_autos = ["Corolla", "Civic", "Focus"]
patentes_autos = ["PDJY46", "PRBS97", "LTLC44"]


def obtener_auto_aleatorio(marcas, modelos, patentes):
    marca_aleatoria = random.choice(marcas)
    indice_marca = marcas.index(marca_aleatoria)
    modelo_correspondiente = modelos[indice_marca]
    patente_correspondiente = patentes[indice_marca]
    return marca_aleatoria, modelo_correspondiente, patente_correspondiente

for i in range(0, 3):
    auto_aleatorio = obtener_auto_aleatorio(marcas_autos, modelos_autos, patentes_autos)
    query = f"""
                        INSERT INTO "detalles_vehiculos" (
                                                "detveh_id"
                                                ,"detveh_version"
                                                ,"detveh_anio"
                                                ,"detveh_tipo"
                                                ,"detveh_color"
                                                ,"detveh_vin"
                                                ,"detveh_patente"
                                                ,"detveh_cant_puertas"
                                                ,"detveh_cant_ruedas"
                                                ,"detveh_color_ruedas"
                                                ,"detveh_color_techo"
                                                ,"detveh_color_asiento"
                                                ,"detveh_color_secundario"
                                                ,"detveh_descripcion"
                                                ,"detveh_otro"
                                                ,"detveh_licencia"
                                                ,"detveh_empresa"
                                                ,"detveh_recompensa"
                                                ,"detveh_propietario"
                                                ,"detveh_mailprop"
                                                ,"detveh_licexpiracion"
                                                ,"detveh_actualizado_en"
                                                ,"detveh_creado_en"
                                                ,"detveh_licest"
                                                ,"detveh_nmotor"
                                                ,"detveh_marca"
                                                ,"detveh_modelo"
                                                )
                                            VALUES (
                                                3
                                                ,10
                                                ,'2024'
                                                ,'SEDAN'
                                                ,'NEGRO'
                                                ,'3VWSE49M58M62763{i}'
                                                ,'{auto_aleatorio[2]}'
                                                ,4
                                                ,NULL
                                                ,NULL
                                                ,NULL
                                                ,NULL
                                                ,NULL
                                                ,NULL
                                                ,NULL
                                                ,'EMPSTECH'
                                                ,1
                                                ,'0'
                                                ,'Carlos Tejos'
                                                ,'carlos@stech.guru'
                                                ,NULL
                                                ,'2022-07-12 16:51:55'
                                                ,'2022-07-12 16:50:09'
                                                ,'INACTIVA'
                                                ,'TXA707040'
                                                ,'{auto_aleatorio[0]}'
                                                ,'{auto_aleatorio[1]}'
                                                );
                        """

    print(query)