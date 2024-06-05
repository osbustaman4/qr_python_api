import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

class EmailSender:
    def __init__(self, smtp_server, smtp_port, smtp_secure, user, password, from_name, bbc):
        """
        Inicializa un objeto EmailSender para enviar correos electrónicos mediante SMTP.

        Args:
            smtp_server (str): Dirección del servidor SMTP.
            smtp_port (int): Puerto del servidor SMTP.
            smtp_secure (bool): Indica si se utiliza una conexión segura SSL/TLS.
            user (str): Dirección de correo electrónico del remitente.
            password (str): Contraseña o clave de aplicación del remitente.
            from_name (str): Nombre del remitente que se mostrará en el correo.
            bbc (str): Dirección de correo electrónico para copia oculta (BCC).
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_secure = smtp_secure
        self.user = user
        self.password = password
        self.from_name = from_name
        self.bbc = bbc

    def send_email(self, to_email, subject, body, is_html=False):
        """
        Envía un correo electrónico al destinatario especificado.

        Args:
            to_email (str): Dirección de correo electrónico del destinatario.
            subject (str): Asunto del correo electrónico.
            body (str): Cuerpo del mensaje del correo electrónico.
            is_html (bool): Indica si el cuerpo del correo es formato HTML.

        Returns:
            bool: True si el correo se envió correctamente, False en caso de error.
        """
        try:
            # Crear el mensaje
            message = MIMEMultipart()
            message["From"] = Header(self.from_name, "utf-8")
            message["To"] = to_email
            message["Subject"] = Header(subject, "utf-8")
            if is_html:
                # Si es HTML, usar MIMEText con tipo "html"
                message.attach(MIMEText(body, "html"))
            else:
                # Si es texto plano, usar MIMEText con tipo "plain"
                message.attach(MIMEText(body, "plain"))

            # Establecer conexión con el servidor SMTP
            if self.smtp_secure:
                servidor = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                servidor = smtplib.SMTP(self.smtp_server, self.smtp_port)

            # Autenticación con el servidor
            servidor.login(self.user, self.password)

            # Configurar destinatario y copia oculta (BBC)
            destinatarios = [to_email]
            if self.bbc:
                destinatarios.append(self.bbc)

            # Enviar el mensaje
            servidor.sendmail(self.user, destinatarios, message.as_string())

            # Cerrar la conexión con el servidor
            servidor.quit()
            print("Correo enviado correctamente.")
            return True

        except Exception as e:
            print(f"Error al enviar el correo: {str(e)}")
            return False