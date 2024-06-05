import bcrypt
import hashlib
import hmac
import json
from flask import jsonify
import jwt
import random
import math
import requests
import string
import traceback


from datetime import date, datetime, timedelta
from decouple import config
from jwt import decode
from lib.Email import EmailSender

from lib.Stech import Logger, Stech, Validate

from sqlalchemy import Integer, update, func, and_, or_, case, Date, cast, literal_column, text, desc, literal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased

from src.models.recuperautos.CodLicencias import CodLicencias
from src.models.recuperautos.GaragePatente import GaragePatente
from src.models.recuperautos.GaragePatenteCompartido import GaragePatenteCompartido
from src.models.recuperautos.Licencias import Licencias
from src.models.recuperautos.ListaBlancaCodEmp import ListaBlancaCodEmp
from src.models.recuperautos.MailTemplate import MailTemplate
from src.models.recuperautos.TraspasoVehiculos import TraspasoVehiculos
from src.models.recuperautos.UsuariosApp import UsuariosApp

class Utils:

    @classmethod
    def create_response(self, message, success, status_code):
        response = jsonify({
            'message': message,
            'success': success
        })
        return response, status_code


    @classmethod
    def add_charge_card(self, data_config):

        session = Stech.get_session(config('ENVIRONMENTS'))

        url_api_flow = config('URL_API_FLOW')

        dt = datetime.now()
        dt_consulta = dt.strftime('%d%m%Y%H%M')

        # Variables de flujo
        api_key = config('FLOW_API_KEY')
        secret_key = config('FLOW_SECRET_KEY')
        flow_id = data_config['id_costumer_flow'] # idCostumerFlow
        value_reward = data_config['value_reward'] # valorRecompensa
        plate_number = data_config['plate_number'] # patente

        random_str = f"{plate_number}{dt_consulta}{random.randint(-10000, -1000)}"
        state = data_config['state'] if 'estado' in data_config else 0 # estado

        url = url_api_flow + data_config["url_api"]

        alltexg = f'amount{value_reward}apiKey{api_key}byEmail0commerceOrder{random_str}currencyCLPcustomerId{flow_id}subjectcargo automaticourlConfirmationurlReturn'

        sign = hmac.new(bytes(secret_key , 'latin-1'), msg = bytes(alltexg , 'latin-1'), digestmod = hashlib.sha256).hexdigest()

        payload = json.dumps({
            "apiKey": api_key,
            "customerId": flow_id,
            "commerceOrder": random_str,
            "subject": 'cargo automatico',
            "amount": value_reward,
            "urlConfirmation": '',
            "urlReturn": '',
            "currency": 'CLP',
            "byEmail": '0',
            "s": sign,
        })

        headers = {
            "apiKey": api_key,
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": "AWSALB=bkjtA7hjgfSDdYDjR1gA1nTV405mj/mRlXDYBQMz2ZAbMoQcY9LLgD1KsHd7BTZLMk3bcqBQ6JUIGoXKb6QSivStsWUyHeyiQ6oDmZ7hu6VtUR5ztVYeMjqjGblh; AWSALBCORS=bkjtA7hjgfSDdYDjR1gA1nTV405mj/mRlXDYBQMz2ZAbMoQcY9LLgD1KsHd7BTZLMk3bcqBQ6JUIGoXKb6QSivStsWUyHeyiQ6oDmZ7hu6VtUR5ztVYeMjqjGblh"
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        json_response = response.json()

        if response.status_code == 200:
            data_response = response.json()
            data_response['state'] = state
            return data_response

        print(response.text)


        print(" ***** ")


    @classmethod
    def decision_transfer_vehicle(self, data_config):
        try:
            session = Stech.get_session(config('ENVIRONMENTS'))

            transfer_id = data_config["traspaso_id"] # idtrv
            transfer_response = data_config["respuesta_traspaso"] # resptrv
            email = data_config["email"]

            tp = aliased(TraspasoVehiculos)
            up = aliased(UsuariosApp)
            ups = aliased(UsuariosApp)

            query_traspaso_vehiculos = (
                session.query(
                    tp,
                    func.concat(up.nombre, ' ', up.apellido).label('nprop'),
                    up.email_userapp.label('mprop'),
                    up.fcm_userapp.label('fcmprop'),
                    ups.id_userapp.label('idsoli'),
                    func.concat(ups.nombre, ' ', ups.apellido).label('nsoli'),
                    ups.email_userapp.label('msoli'),
                    ups.fcm_userapp.label('fcmsoli')
                )
                .select_from(tp)
                .join(up, up.id_userapp == tp.idprop_trv)
                .join(ups, ups.id_userapp == tp.idprop_trv)
                .filter(tp.estado_trv == True)
                .filter(tp.resp_trv == "PENDIENTE")
                .filter(tp.id_trv == transfer_id)
                .filter(up.email_userapp == email)

            ).all()

            if not query_traspaso_vehiculos:
                raise ValueError("traspaso de vehiculo no existe")

            response = Stech.object_to_json(query_traspaso_vehiculos)[0]

            plate_number = query_traspaso_vehiculos[0][0].ppu_trv
            applicant_id = query_traspaso_vehiculos[0][0].idsoli_trv

            pushsoli = { 
                "fcm" : query_traspaso_vehiculos[0].fcmsoli,
                "body" :"",
                "title" : "Traspaso Vehículo "+transfer_response,
            }

            pushprop = {
                "fcm" : query_traspaso_vehiculos[0].fcmprop,
                "body" : "",
                "title" : "Traspaso Vehículo "+transfer_response,
            }

            emailprop = {
                "asunto": "Solicitud Traspaso Vehículo "+transfer_response,
                "to": query_traspaso_vehiculos[0].mprop,
                "bcc": "",
                "mensaje": "",
                "nombre": query_traspaso_vehiculos[0].nprop
            }

            emailsoli={
                "asunto": "Solicitud Traspaso Vehículo "+transfer_response,
                "to": query_traspaso_vehiculos[0].msoli,
                "bcc": "",
                "mensaje": "",
                "nombre": query_traspaso_vehiculos[0].nsoli
            }

            query_traspaso_vehiculos = text(f"""UPDATE traspaso_vehiculos 
                                            SET resp_trv = :transfer_response
                                                , dtresp_trv = now()
                                                , notificado_trv = true
                                                , actualizado_en = now() 
                                        WHERE id_trv = :transfer_id 
                                            AND ppu_trv = :plate_number 
                                            AND estado_trv = true;""")
            
            if transfer_response == "ACEPTADO":
                pushsoli["body"] = f"El traspaso del Vehículo PPU: {plate_number} fue Aceptado por su nuevo propietario."
                pushsoli["data"] = { "uid": "garage", "ppu": plate_number}
                emailsoli["mensaje"] = f"La solicitud para traspaso del Vehículo PPU: {plate_number} fue Aceptado por su nuevo propietario, en poco tiempo podras verlo en la sección mi Garaje dentro de la App"

                pushprop["body"]=f"Aceptaste el traspaso del Vehículo PPU: {plate_number}."
                emailprop["mensaje"]=f"Aceptaste la solicitud para traspaso del Vehículo PPU: {plate_number}, en poco tiempo el vehiculo sera desvinculado de tu cuenta y vinculado al nuevo propietario."

                query_update_garaje_vehiculo = text(f"""UPDATE garage_patente 
                                                    SET id_usuario_app = {applicant_id}
                                                    , actualizado_en = now()
                                                    WHERE patente = '{plate_number}' 
                                                        AND estado_patente = true 
                                                        AND reportado_robado = false;""")
                
                query_updgaragevehiculo = session.execute(query_update_garaje_vehiculo, {'applicant_id': applicant_id, 'plate_number': plate_number})
                session.commit()

                if query_updgaragevehiculo.rowcount > 0:
            
                    query_updgaragevehiculo = session.execute(query_traspaso_vehiculos, {'transfer_response': transfer_response, 'transfer_id': transfer_id, 'plate_number': plate_number})
                    session.commit()

                    if query_updgaragevehiculo.rowcount > 0:
                        response = {
                            "datos": response,
                            "pushfmc":[pushsoli, pushprop],
                            "emails":[emailprop, emailsoli],
                            "msj": "Solicitud Aceptada Correctamente"
                        }

                        return response, 200
                    
                    else:
                        response = {
                            "error": "Error al realizar la solicitud"
                        }

                        return response, 400
                    
            elif transfer_response == "RECHAZADO":

                pushsoli["body"] = f"El traspaso del Vehículo PPU: {plate_number} fue rechazado."
                emailsoli["mensaje"] = f"La solicitud para traspaso del Vehículo PPU: {plate_number} fue Rechazada por su actual propietario. Puedes generar una nueva solicitud de traspaso o comunicarte con nuestro soporte, para revisar tu caso."

                pushprop["body"]=f"Rechazaste el traspaso del Vehículo PPU: {plate_number}."
                emailprop["mensaje"]=f"Rechazaste la solicitud para traspaso del Vehículo PPU: {plate_number}, recuerda que puedes recibir nuevas solicitudes de traspaso o ser contactado por nuestro soporte si el caso debe ser revisado."

                query_updgaragevehiculo = session.execute(query_traspaso_vehiculos, {'transfer_response': transfer_response, 'transfer_id': transfer_id, 'plate_number': plate_number})
                session.commit()

                response = {
                    "datos": response,
                    "pushfmc":[pushsoli, pushprop],
                    "emails":[emailprop, emailsoli],
                    "msj": "Solicitud Aceptada Correctamente"
                }

                return response, 200
            
            else:
                raise ValueError("respuesta no valida")

        except ValueError as ex:
            session.rollback()
            return {
                "error": str(ex)
            }, 400
        
        except SQLAlchemyError as ex:
            session.rollback()
            return {
                "error": "Error al realizar la solicitud"
            }, 500


    @classmethod
    def vehicle_transfer_request(self, data_config):

        try:
            session = Stech.get_session(config('ENVIRONMENTS'))

            plate_number = data_config["patente"]
            email = data_config["email"]

            caracteres = "ABCDEFGHJKMNPQRTUVWXYZ12346789"
            scod = 'TRV' + plate_number
            for i in range(6):
                scod += random.choice(caracteres)

            query_traspaso_vehiculos = (
                session.query(TraspasoVehiculos)
                .filter(TraspasoVehiculos.ppu_trv == plate_number)
                .filter(TraspasoVehiculos.idprop_trv == (session.query(GaragePatente.id_usuario_app).filter(GaragePatente.patente == plate_number)).scalar())
                .filter(TraspasoVehiculos.idsoli_trv == (session.query(UsuariosApp.id_userapp).filter(UsuariosApp.email_userapp == email)).scalar())
                .filter(TraspasoVehiculos.resp_trv == "PENDIENTE")
            ).first()

            if not query_traspaso_vehiculos:

                usuarios_app = aliased(UsuariosApp)

                subquery_id_userapp = (
                    session.query(UsuariosApp.id_userapp)
                    .filter(UsuariosApp.email_userapp == email)
                ).scalar()

                subquery_email_user = (
                    session.query(UsuariosApp.email_userapp)
                    .filter(UsuariosApp.email_userapp == email)
                ).scalar()

                subquery_fcm_user = (
                    session.query(UsuariosApp.fcm_userapp)
                    .filter(UsuariosApp.email_userapp == email)
                ).scalar()

                subquery_name_user  = (
                    session.query(
                        func.concat(UsuariosApp.nombre, ' ', UsuariosApp.apellido)
                    )
                    .filter(UsuariosApp.email_userapp == email)
                ).scalar()

                query_garage_patente = (
                    session.query(
                        GaragePatente.id_garage,
                        GaragePatente.reportado_robado,
                        GaragePatente.patente,
                        GaragePatente.marca,
                        GaragePatente.modelo,
                        GaragePatente.color,
                        usuarios_app.id_userapp.label('idprop'),
                        func.concat(usuarios_app.nombre, ' ', usuarios_app.apellido).label('nprop'),
                        usuarios_app.email_userapp.label('mprop'),
                        usuarios_app.fcm_userapp.label('fcmprop'),
                        literal(subquery_id_userapp).label('idsoli'),
                        literal(subquery_name_user).label('nsoli'),
                        literal(subquery_email_user).label('msoli'),
                        literal(subquery_fcm_user).label('fcmsoli')
                    )
                    .select_from(GaragePatente)
                    .join(usuarios_app, usuarios_app.id_userapp == GaragePatente.id_usuario_app)
                    .filter(GaragePatente.patente == plate_number)
                ).all()

                if not query_garage_patente:
                    return {
                        "error": "No se encontró el garage"
                    }, 400
                
                else:
                    json_query_garage_patente = Stech.object_to_json(query_garage_patente)[0]

                    if json_query_garage_patente["reportado_robado"]:
                        return {
                            "error": "El vehiculo se encuentra reportado como robado"
                        }, 400
                    
                    push_requestor = {
                        "fcm": json_query_garage_patente["fcmsoli"],
                        "body": f"Has Solicitado el traspaso del vehículo PPU: {plate_number}.",
                        "title": "Solicitud Traspaso Vehículo",
                    }

                    pushprop = {
                        "fcm": json_query_garage_patente["fcmprop"],
                        "body": f"El usuario {json_query_garage_patente['nsoli']} ha solicitado el traspaso del vehículo PPU: {plate_number}. Puedes Aceptar o Rechazar esta solicitud desde la sección mi Garaje.",
                        "title": "Solicitud Traspaso Vehículo",
                        "data": {
                            "uid": "garage-traspaso",
                            "ppu": plate_number
                        }
                    }

                    emailprop = {
                        "asunto": "Solicitud Traspaso Vehículo",
                        "to": json_query_garage_patente['mprop'],
                        "bcc": "",
                        "mensaje": f"El usuario {json_query_garage_patente['nsoli']} ha solicitado el traspaso del vehículo PPU: {plate_number}. Puedes Aceptar o Rechazar esta solicitud desde la sección mi Garaje. Si no respondes esta solicitud en 72 horas se marcara como Rechazada.",
                        "nombre": json_query_garage_patente["nprop"]
                    }

                    emailsoli = {
                        "asunto": "Solicitud Traspaso Vehículo",
                        "to": json_query_garage_patente["msoli"],
                        "bcc": "",
                        "mensaje": f"Has Solicitado el traspaso del vehículo PPU: {plate_number}. Te mantendremos informado sobre el estado de tu solicitud.",
                        "nombre": json_query_garage_patente["nsoli"]
                    }

                    response = {
                        "datos": json_query_garage_patente,
                        "pushfmc":[push_requestor, pushprop],
                        "emails":[emailprop, emailsoli],
                        "msj": "Solicitud Ingresada Correctamente"
                    }

                    traspaso_vehicle = TraspasoVehiculos(
                        idvehi_trv = json_query_garage_patente["id_garage"],
                        idprop_trv = json_query_garage_patente["idprop"],
                        idsoli_trv = json_query_garage_patente["idsoli"],
                        resp_trv = "PENDIENTE",
                        dtsoli_trv = datetime.now(),
                        codigo_trv = scod,
                        ppu_trv = plate_number
                    )
                    
                    session.add(traspaso_vehicle)
                    session.commit()

                    return response, 200

            else:
                return {
                    "error": "Solicitud ya existe"
                }, 400
        
        except ValueError as ex:
            session.rollback()
            return {
                "error": str(ex)
            }, 400
        except SQLAlchemyError as ex:
            session.rollback()
            return {
                ",error": "Error al realizar la solicitud"
            }, 500


    @classmethod
    def create_user(self, email_userapp):
        
        session = Stech.get_session(config('ENVIRONMENTS'))

        try:
            create_user = UsuariosApp(
                email_userapp = email_userapp,
                
            )
            session.add(create_user)
            # Realiza la confirmación para efectuar la inserción en la base de datos y obtener el ID devuelto
            session.commit()
            data_user_app = {}
            data_user_app['id_userapp'] = create_user.id_userapp
            return data_user_app
        
        except SQLAlchemyError as e:
            session.rollback()
            print(e)
            return {
                "message": "Error al crear usuario"
            }, 500
        

    @classmethod
    def create_code_license(self, master_code):
        
        license = master_code.upper()
        activation_date = datetime.now()
        activation_date = activation_date.strftime("%Y-%m-%d %H:%M:%S")
        deactivation_date = ""

        session = Stech.get_session(config('ENVIRONMENTS'))

        try:
            
            query_licencia = (
                session.query(
                    func.concat(literal_column("now()::date + concat(vigencia_meses, ' month')::interval")).label("dt_final"), 
                    CodLicencias
                )
                .select_from(CodLicencias)
                .filter(CodLicencias.codigo == license)
            ).all()
            

            if query_licencia:
                deactivation_date = query_licencia[0][0]
                parent_code_id = query_licencia[0][1].id_codigo # id_codigo_padre
                code = query_licencia[0][1].codigo # codigo
                vig_months = query_licencia[0][1].vigencia_meses # meses_vig

                code = license+'-'
                characters = "abcdefghijkmnpqrtuvwxyzABCDEFGHJKMNPQRTUVWXYZ2346789"

                for _ in range(20):
                    code += random.choice(characters)

                query_license_cod = (session.query(
                    CodLicencias
                    , Licencias
                    )
                    .join(Licencias, CodLicencias.id_codigo == Licencias.id_codigo_licencias)
                    .filter(Licencias.licencia == license)
                ).all()

                if not query_license_cod:
                    new_license = Licencias(
                        id_codigo_licencias = parent_code_id
                        , estado_licencia = True
                        , licencia = code
                        , fecha_activacion = activation_date
                        , fecha_desactivacion = deactivation_date
                    )

                    session.add(new_license)

                    # Realiza la confirmación para efectuar la inserción en la base de datos y obtener el ID devuelto
                    session.commit()


                    id_lecense = new_license.id_licencia

                    # Query SQL
                    query_updt = text("""
                        UPDATE cod_licencias
                        SET cont_licencias = (
                            SELECT count(*) FROM licencias
                            WHERE id_codigo_licencias = :id_codigo
                        )
                        WHERE id_codigo = :id_codigo_padre
                    """)

                    data_query_updt = {'id_codigo': parent_code_id, 'id_codigo_padre': parent_code_id}
                    session.execute(query_updt, data_query_updt)
                    session.commit()

                    return {
                        "message": "Licencia creada correctamente",
                        "code": code,
                        "month": vig_months,
                        "id_license": id_lecense
                    }, 200

                else:
                    session.rollback()
                    return {
                        "message": "Licencia ya existe"
                    }, 405
            else:
                session.rollback()
                return {
                    "message": "Licencia no existe"
                }, 400
        except SQLAlchemyError as e:
            session.rollback()
            return {
                "message": "Error al crear licencia"
            }, 500


    @classmethod
    def whitelist_code_information(self, data):
        session = Stech.get_session(config('ENVIRONMENTS'))

        try:
            query_code = (
                session.query(
                    CodLicencias
                )
                .filter(CodLicencias.codigo == data["codigo_licencia"])
            ).all()
            
            if not query_code:
                raise ValueError("Codigo Licencia No Existente")
            
            querly_white_list = (
                session.query(
                    ListaBlancaCodEmp
                )
                .filter(ListaBlancaCodEmp.est_lb == True)
                .filter(ListaBlancaCodEmp.cod_lb == data["codigo_licencia"])
                .filter(ListaBlancaCodEmp.pat_lb == data["patente"])
            ).all()

            if query_code[0].tipo_codigo == "EMPRESA" and query_code[0].lb_asig:

                if not querly_white_list:
                    return {
                        "msg": "patente no ingresada en lista",
                        "tipocod": query_code[0].tipo_codigo,
                        "codlb": query_code[0].lb_asig,
                        "patlb": False,
                        "codrec": data["codigo_licencia"],
                        "infocod": vars(query_code[0])
                    }, 400
                else:

                    if querly_white_list[0].usd_lb:
                        return {
                            "msg": "patente ingresada en lista",
                            "tipocod": query_code[0].tipo_codigo,
                            "codlb": query_code[0].lb_asig,
                            "patlb": True,
                            "codrec": data["codigo_licencia"],
                            "infocod": vars(query_code[0])
                        }, 400
                    
                    else:
                        return {
                            "msg": "patente ingresada en lista",
                            "tipocod": query_code[0].tipo_codigo,
                            "codlb": query_code[0].lb_asig,
                            "patlb": True,
                            "codrec": data["codigo_licencia"],
                            "infocod": vars(query_code[0])
                        }, 200

            elif query_code[0].tipo_codigo == "EMPRESA" and not query_code[0].lb_asig:

                return {
                    "msg": "Empresa sin lista blanca",
                    "tipocod": query_code[0].tipo_codigo,
                    "codlb": query_code[0].lb_asig,
                    "patlb": True,
                    "codrec": data["codigo_licencia"],
                    "infocod": vars(query_code[0])
                }, 200
            
            else:
                return {
                    "msg": "Codigo no empresa",
                    "tipocod": query_code[0].tipo_codigo,
                    "codlb": False,
                    "patlb": True,
                    "codrec": data["codigo_licencia"],
                    "infocod": vars(query_code[0])
                }, 400

        except ValueError as ex:
            session.rollback()
            return {
                "error": str(ex)
            }, 400
        
        except SQLAlchemyError as ex:
            session.rollback()
            return {
                "error": "Error al realizar la solicitud"
            }, 500


    @classmethod
    def update_whit_list_codemp(self, session, code_license, plate_number):
        query_update_white_list_company = text("""UPDATE listablanca_codemp 
                                                SET 
                                                    actualizado_en = now()
                                                    , usd_lb = true 
                                                WHERE 
                                                    cod_lb = :code_license 
                                                    AND pat_lb = :plate_number""")
        
        data_query_update_white_list_company = {'code_license': code_license, 'plate_number': plate_number}
        session.execute(query_update_white_list_company, data_query_update_white_list_company)
        session.commit()


    @classmethod
    def hist_codlic(self, session, id_license, plate_number, month):
        sql_hist_codlic = text(f"""SELECT public.hist_codlic(:id_license, :plate_number, :month)""")
        data_sql_hist_codlic = {'id_license': id_license, 'plate_number': plate_number, 'month': month}
        response = session.execute(sql_hist_codlic, data_sql_hist_codlic).fetchall()

        if response:
            return True
        else:
            return False
    

    @classmethod
    def new_license_code_company(self, data):
        try:
            session = Stech.get_session(config('ENVIRONMENTS'))
            
            email = data["email"]
            license_code = data["codigo_licencia"]
            plate_number = data["patente"]

            query_property_inquiry = (
                session.query(
                    GaragePatente,
                    UsuariosApp,
                    func.concat(UsuariosApp.nombre, ' ', UsuariosApp.apellido).label('nprop'),
                )
                .select_from(GaragePatente)
                .join(UsuariosApp, UsuariosApp.id_userapp == GaragePatente.id_usuario_app)
                .filter(GaragePatente.patente == plate_number)
                .filter(GaragePatente.id_usuario_app == (session.query(UsuariosApp.id_userapp).filter(UsuariosApp.email_userapp == email)).scalar())
            ).all()

            if not query_property_inquiry:
                raise ValueError("Vehiculo o usuario erroneos")
            
            old_id_license = query_property_inquiry[0][0].id_licencia
            
            response_create_code, code_response = self.create_code_license(license_code)
            if code_response != 200:
                raise ValueError(response_create_code["message"])
            
            id_license = response_create_code["id_license"]
            month = response_create_code["month"]
            plate_number = query_property_inquiry[0][0].patente
            month = f"{month} meses"

            query_update_garage = text("UPDATE garage_patente SET id_licencia = :id_license WHERE patente = :plate_number")
            data_query_update_garage = {'id_license': id_license, 'plate_number': plate_number}
            session.execute(query_update_garage, data_query_update_garage)
            session.commit()

            diasleft = case(
                (func.cast((Licencias.fecha_desactivacion - func.current_date()), Integer) < 0, 0),
                else_=func.cast((Licencias.fecha_desactivacion - func.current_date()), Integer)
            )

            query_old_code_license = (
                session.query(
                    CodLicencias.codigo,
                    CodLicencias.tipo_codigo,
                    CodLicencias.recompensa,
                    Licencias.fecha_activacion,
                    diasleft.label('diasleft')
                )
                .select_from(CodLicencias)
                .join(Licencias, Licencias.id_codigo_licencias == CodLicencias.id_codigo)
                .filter(Licencias.id_licencia == old_id_license)
            ).all()

            data_json = Stech.object_to_json(query_old_code_license)[0]

            type_code_old = data_json["tipo_codigo"]  #toldlic
            days_left = data_json["diasleft"]  #diasleft

            if not type_code_old == "GRATUITA":
                query_update_new_license = text("""UPDATE licencias 
                                                        SET 
                                                            fecha_desactivacion = fecha_desactivacion+:days_left
                                                        WHERE 
                                                            id_licencia = :id_licencia""")
                
                data_update_new_license = {'days_left': days_left, 'id_licencia': response_create_code["id_license"]}
                session.execute(query_update_new_license, data_update_new_license)
                session.commit()

                message = "Patente con nueva licencia y dias restantes agregados"
            
            else:
                message = "Patente con nueva licencia"

            self.update_whit_list_codemp(session, license_code, plate_number)
            hist_codlic = self.hist_codlic(session, response_create_code["id_license"], plate_number, month)

            if not hist_codlic:
                raise ValueError("Error al crear historial de licencia")

            response_plate_number ={
                "message": message
            }

            if query_property_inquiry[0][0].reportado_robado and query_property_inquiry[0][0].recompensa_activa:                    
                response_plate_number["devrec"] = True
            else:
                response_plate_number["devrec"] = False

            return response_plate_number, 200
                        
        except ValueError as ex:
            session.rollback()
            return {
                "error": str(ex)
            }, 400
        
        except SQLAlchemyError as ex:
            session.rollback()
            return {
                "error": str(ex)
            }, 500
    
    
    @classmethod
    def recover_reward(self, data):
        try:
            session = Stech.get_session(config('ENVIRONMENTS'))
            
            email = data["email"]
            plate_number = data["patente"]
            action = data["action"]

            query_property_inquiry = (
                session.query(
                    GaragePatente,
                    UsuariosApp,
                    func.concat(UsuariosApp.nombre, ' ', UsuariosApp.apellido).label('nprop'),
                )
                .select_from(GaragePatente)
                .join(UsuariosApp, UsuariosApp.id_userapp == GaragePatente.id_usuario_app)
                .filter(GaragePatente.reportado_robado == True)
                .filter(GaragePatente.patente == plate_number)
                .filter(GaragePatente.id_usuario_app == (session.query(UsuariosApp.id_userapp).filter(UsuariosApp.email_userapp == email)).scalar())
            ).all()

            if not query_property_inquiry:
                raise ValueError("Vehiculo sin reporte de robo")
            
            json_property_inquiry = Stech.object_to_json(query_property_inquiry)[0]

            if json_property_inquiry["GaragePatente"].origen_recom == 'Usuario':

                sql_payroll_return = text(f"""SELECT public.planillar_devolucion(:plate_number, :email, :action)""")
                data_payroll_return = {'plate_number': plate_number, 'email': email, 'action': action}
                response_payroll_return = session.execute(sql_payroll_return, data_payroll_return).fetchall()


                return {
                    "message": response_payroll_return[0][0],
                    "data": json_property_inquiry
                }, 200
            
            else:
                raise ValueError({
                    "message": "La recompensa fue establecida por un tercero por lo que no puede generarse una orden de devolución",
                    "data": json_property_inquiry
                })

        except ValueError as ex:
            session.rollback()
            return {
                "error": str(ex)
            }, 400
        
        except SQLAlchemyError as ex:
            session.rollback()
            return {
                "error": str(ex)
            }, 500


    @classmethod
    def email_request_return_reward(self, data):
        try:
            
            email = data["email"]
            plate_number = data["patente"]
            action = data["action"]
            reward = data["more"]["data"]["GaragePatente"].recompensa
            distribute_amount =  data["more"]["data"]["GaragePatente"].recompensa_repartir
            client_name = data["more"]["data"]["UsuariosApp"].nombre
            reward_validity = data["more"]["data"]["GaragePatente"].recompensa_duracion
            reward_validity = reward_validity if not reward_validity else datetime.strptime(reward_validity, '%d/%m/%Y').strftime('%d/%m/%Y')
            the_message = "maildevrecomp" if action == 1 else "mailreactrecomp"

            html_replace = {
                "NombreCliente": client_name,
                "patente": plate_number,
            }
            
            if the_message == "maildevrecomp":
                html_replace["montoreco"] =  Stech.format_to_set_locale_peso(distribute_amount)
            else:
                html_replace["montoreco"] = Stech.format_to_set_locale_peso(reward)
                html_replace["cadreco"] = reward_validity

            dict_data_mail = {
                "from": "Recuperauto <contacto@app.recuperauto.cl>",
                "to": email,
                "bcc": config("MAIL_BBC"),
                "asunto": None,
                "mensaje": the_message,
                "nombrecliente": client_name,
                "word_replace": html_replace
            }

            sent_mail = Utils_Mails.create_email_stech(the_message, dict_data_mail)

            return {
                "message": sent_mail["message"]
            }, 200

        except ValueError as ex:
            return {
                "error": str(ex)
            }, 400
        
        except Exception as ex:
            return {
                "error": str(ex)
            }, 500


    @classmethod
    def email_new_code_license_company(self, data):
        try:

            session = Stech.get_session(config('ENVIRONMENTS'))

            email = data["email"]
            plate_number = data["patente"]

            query_user_data = (
                session.query(
                    func.concat(UsuariosApp.nombre, ' ', UsuariosApp.apellido).label('nombre'),
                    Licencias.fecha_desactivacion,
                    CodLicencias.tipo_codigo,
                    CodLicencias.vigencia_meses,
                    CodLicencias.recompensa
                )
                .select_from(UsuariosApp)
                .join(GaragePatente, GaragePatente.id_usuario_app == UsuariosApp.id_userapp)
                .join(Licencias, Licencias.id_licencia == GaragePatente.id_licencia)
                .join(CodLicencias, CodLicencias.id_codigo == Licencias.id_codigo_licencias)
                .filter(GaragePatente.patente == plate_number)
                .filter(UsuariosApp.email_userapp == email)
            ).all()

            if not query_user_data:
                raise ValueError("Usuario no existe")

            json_user_data = Stech.object_to_json(query_user_data)[0]

            html_replace = {
                "NombreCliente": json_user_data["nombre"],
                "patente": plate_number,
                "viglic": json_user_data["vigencia_meses"],
                "reclic": json_user_data["recompensa"],
            }

            dict_data_mail = {
                "from": "Recuperauto <contacto@app.recuperauto.cl>",
                "to": email,
                "bcc": config("MAIL_BBC"),
                "asunto": None,
                "mensaje": "newcodlicemp",
                "nombrecliente": json_user_data["nombre"],
                "word_replace": html_replace
            }

            sent_mail = Utils_Mails.create_email_stech("newcodlicemp", dict_data_mail)

            return {
                "message": sent_mail["message"]
            }, sent_mail["response_http"]

        except ValueError as ex:
            return {
                "error": str(ex)
            }, 400
        
        except Exception as ex:
            return {
                "error": str(ex)
            }, 500


    @classmethod
    def new_code_license(self, datos):

        session = Stech.get_session(config('ENVIRONMENTS'))

        codigo = datos['codigo']
        email = datos['email']
        patente = datos['patente'].upper()

        querypropiedad = f"""
            SELECT gp.*, ua.*, concat(nombre, ' ', apellido) AS nprop 
            FROM garage_patente gp
            JOIN usuarios_app ua ON ua.id_userapp = gp.id_usuario_app
            WHERE patente = '{patente}' AND ua.email_userapp = '{email}';
        """

        try:
            result = session.execute(querypropiedad).fetchall()

            if not result:
                return {"msg": "Vehiculo o usuario erroneos", "error": 404}

            idoldlic = result[0]['id_licencia']
            resp1 = self.create_code_license(codigo)

            if 'error' in resp1 or resp1.get('msg') != "licencia creada correctamente":
                return {"msg": "Ocurrió un error. Intente de nuevo", "error": 404}

            id_licencia = resp1['id_licencia']
            meses = resp1['meses']

            queryoldlic = f"""
                SELECT l.id_licencia, cl.codigo, cl.tipo_codigo, l.fecha_desactivacion,
                    CASE WHEN (l.fecha_desactivacion::date - current_date)::int < 0 THEN 0
                    ELSE (l.fecha_desactivacion::date - current_date)::int END AS diasleft
                FROM cod_licencias cl
                JOIN licencias l ON l.id_codigo_licencias = cl.id_codigo
                WHERE l.id_licencia = {idoldlic};
            """

            resultq = session.execute(queryoldlic).fetchall()

            toldlic = resultq[0]['tipo_codigo']
            diasleft = resultq[0]['diasleft']

            queryupdpat = f"UPDATE garage_patente SET id_licencia = {id_licencia} WHERE patente = '{patente}';"

            session.execute(queryupdpat)

            hist_codlic_query = f"SELECT public.hist_codlic({id_licencia}, '{patente}', '{meses}');"
            session.execute(hist_codlic_query)

            if toldlic != 'GRATUITA':
                updnewlic = f"UPDATE licencias SET fecha_desactivacion = fecha_desactivacion + {diasleft} WHERE id_licencia = {id_licencia};"
                session.execute(updnewlic)

            return {"msg": "Patente con nueva licencia y días restantes agregados"} if toldlic != 'GRATUITA' else {"msg": "Patente con nueva licencia"}

        except SQLAlchemyError as e:
            return {"msg": f"Error en la consulta: {str(e)}"}


class Utils_Mails:

    @classmethod
    def create_email_stech(self, name_mail, data_email):
        """
        Creates and sends an email using the Stech library.

        Args:
            name_mail (str): The name of the email template to use.
            data_email (dict): A dictionary containing the email data, including recipients, subject, and word replacements.

        Returns:
            dict: A dictionary containing the result of the email sending operation, including a success flag, error message, and success message.
        """
        try:
            session = Stech.get_session(config('ENVIRONMENTS'))

            mail_template = aliased(MailTemplate)

            query_mail_template = (
                session.query(
                    mail_template.asunto_mail,
                    mail_template.html_mail
                )
                .select_from(mail_template)
                .filter(mail_template.nombre_mail == name_mail)
            ).all()

            if not query_mail_template:
                return {
                    "message": "Error getting template",
                    "response_http": 400,
                    "success": False,
                }

            # cuerpo
            html = query_mail_template[0][1]

            for key, value in data_email["word_replace"].items():
                html = html.replace(f"%{key}%", value)

            # Crear una instancia de EmailSender
            email_sender = EmailSender(
                config("MAIL_HOST"),
                config("MAIL_PORT"),
                config("MAIL_SECURE"),
                config("MAIL_USER"),
                config("MAIL_PASSWORD"),
                config("MAIL_FROMNAME"),
                config("MAIL_BBC")
            )

            if data_email["asunto"] is None:
                data_email["asunto"] = query_mail_template[0][0]

            sent_mail = email_sender.send_email(data_email["to"], data_email["asunto"], html, True)

            if sent_mail:
                return {
                    "message": "mail sent successfully",
                    "response_http": 200,
                    "success": True
                }
            
            else:
                return {
                    "message": "error sending email",
                    "response_http": 400,
                    "success": False
                }

        except Exception as ex:
            return {
                "message": str(ex),
                "errresponse_http": 500,
                "success": False
            }
        

    @classmethod
    def owner_vehicle_recovery(self, plate_number, email_userapp):
        """
        Recuperacion Vehiculo propietario
        """

        session = Stech.get_session(config('ENVIRONMENTS'))

        query_data_user = text("""
            SELECT COUNT
                (DISTINCT rpat.rpat_rutresp) AS cantidad,
                (
                SELECT
                    concat ( ua.nombre || ' ' || ua.apellido ) AS nombre 
                FROM
                    usuarios_app ua
                    JOIN garage_patente gp ON gp.id_usuario_app = ua.id_userapp 
                WHERE
                    gp.patente = :patente
                ) 
            FROM
                reportes_patente AS rpat
                LEFT JOIN grupos_usuario AS gru ON gru.id_grupo = rpat.group_id
                JOIN garage_patente gp ON gp.patente = gru.nombre
                JOIN usuarios_app ua ON ua.id_userapp = gp.id_usuario_app 
            WHERE
                gru.tipo_grupo = 'reportes' 
                AND rpat.rpat_rutresp NOT IN ('Recuperauto', ua.email_userapp) 
                AND rpat.rpat_confirmado != 3 
                AND rpat.id_comuna > 0 
                AND rpat.rpat_valido = 'true' 
                AND gp.patente = :patente
        """)

        result_data_user = session.execute(query_data_user, {'patente': plate_number}).first()

        if not result_data_user:
            return {
                "message": "codigo inexistente o erroneo",
                "http_status": 404,
                "error": True,
            }
        
        name_user = result_data_user[1]
        cant_row = (result_data_user[0] + 2) if result_data_user[0] > 0 else result_data_user[0]


        mail_template = aliased(MailTemplate)

        query_mail_template = (
            session.query(
                mail_template.asunto_mail,
                mail_template.html_mail
            )
            .select_from(mail_template)
                .filter(mail_template.nombre_mail == "recupereVehiculoprop")
            ).all()
        
        if not query_mail_template:
            return {
                "message": "Error al obtener template",
                "success": False,
            }
        
        asunto = query_mail_template[0][0]
        html = query_mail_template[0][1]

        html = html.replace("%NombreCliente%", name_user)
        html = html.replace("%patente%", plate_number)
        html = html.replace("%colabcant%", str(cant_row))

        # Crear una instancia de EmailSender
        email_sender = EmailSender(
                config("MAIL_HOST")
                , config("MAIL_PORT")
                , config("MAIL_SECURE")
                , config("MAIL_USER")
                , config("MAIL_PASSWORD")
                , config("MAIL_FROMNAME")
                , config("MAIL_BBC")
        )
        
        send_email = email_sender.send_email(email_userapp, asunto, html, True)

        if send_email:
            return {
                "message": "correo enviado correctamente",
                "success": True,
                "colab": cant_row,
            }

        else:  
            return {
                "message": "error al enviar correo",
                "success": False,
            }


    @classmethod
    def recover_pending_vehicle(self, plate_number, email_userapp):

        session = Stech.get_session(config('ENVIRONMENTS'))
        
        dt_servertime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        quety_propiedad = text("""
            SELECT
                gp.*,
                ua.*,
                concat ( nombre || ' ' || apellido ) AS nprop,
                cl.codigo,
                cl.tipo_codigo,
                cl.lb_asig,
                cl.estado_codigo 
            FROM
                garage_patente gp
                JOIN usuarios_app ua ON ua.id_userapp = gp.id_usuario_app
                JOIN licencias li ON li.id_licencia = gp.id_licencia
                JOIN cod_licencias cl ON cl.id_codigo = li.id_codigo_licencias 
            WHERE
                gp.reportado_robado = TRUE 
                AND patente = :patente 
                AND ua.email_userapp = :email
        """)

        result_propiedad = session.execute(quety_propiedad, {'patente': plate_number, 'email': email_userapp}).fetchall()

        if result_propiedad:
            call_recup = text("SELECT public.pendiente_recuperacion(:patente, :dt_servertime)")
            result_recup = session.execute(call_recup, {'patente': plate_number, 'dt_servertime': dt_servertime}).fetchall()

            session.commit()

            if result_recup:
                return {
                    "message": result_recup[0],
                    "error": False
                }
            else:
                return {
                    "message": "Vehiculo sin recuperacion pendiente",
                    "error": True
                }
        else:
            return {
                    "message": "Vehiculo sin reporte de robo",
                    "error": True
                }


    @classmethod
    def vehicle_recovery_collaborators(self, plate_number, email_userapp):
        
        session = Stech.get_session(config('ENVIRONMENTS'))

        query_data_user = text("""
            SELECT
                gp.recompensa_repartir,
                ARRAY_AGG(DISTINCT rpat.rpat_rutresp) AS email,
                (gp.recompensa_repartir / (COUNT(DISTINCT rpat.rpat_rutresp) + 2)) AS valorpp,
                (COUNT(DISTINCT rpat.rpat_rutresp) + 2) AS cantp 
            FROM
                reportes_patente rpat
                LEFT JOIN grupos_usuario gu ON gu.id_grupo = rpat.group_id
                JOIN usuarios_app ua ON rpat.id_usuario = ua.id_userapp
                JOIN garage_patente gp ON gp.patente = gu.nombre
            WHERE
                rpat.rpat_confirmado != 3
                AND rpat.rpat_rutresp NOT IN ('Recuperauto', ua.email_userapp)
                AND rpat.id_comuna > 0
                AND rpat.rpat_valido = 'true'
                AND gu.tipo_grupo = 'reportes'
                AND gu.gru_activo = 'true'
                AND gu.nombre = :patente
            GROUP BY
                gp.recompensa_repartir;
        """)

        result_data_user = session.execute(query_data_user, {'patente': plate_number}).first()

        if not result_data_user:
            return {
                "message": "No hay colaboradores",
                "http_status": 404,
                "error": True,
            }
        
        email_user = result_data_user[1][0]
        cantp = result_data_user[3]
        montop = result_data_user[2]

        
        mail_template = aliased(MailTemplate)

        query_mail_template = (
            session.query(
                mail_template.asunto_mail,
                mail_template.html_mail
            )
            .select_from(mail_template)
                .filter(mail_template.nombre_mail == "recupereVehiculocolab")
            ).all()
        
        if not query_mail_template:
            return {
                "message": "Error al obtener template",
                "success": False,
            }
        
        asunto = query_mail_template[0][0]
        html = query_mail_template[0][1]
        
        html = html.replace("%patente%", plate_number)
        html = html.replace("%colabcant%", str(cantp))
        html = html.replace("%valorpp%", f"{montop:.2f}")

        # Crear una instancia de EmailSender
        email_sender = EmailSender(
                config("MAIL_HOST")
                , config("MAIL_PORT")
                , config("MAIL_SECURE")
                , config("MAIL_USER")
                , config("MAIL_PASSWORD")
                , config("MAIL_FROMNAME")
                , config("MAIL_BBC")
        )
        
        send_email = email_sender.send_email(email_userapp, asunto, html, True)

        if send_email:
            return {
                "message": "correo enviado correctamente",
                "success": True
            }

        else:  
            return {
                "message": "error al enviar correo",
                "success": False,
            }

