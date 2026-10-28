"""Gestor de correos del sistema.

Este módulo concentra el envío de emails HTML para notificar altas de usuarios
y confirmar cambios de contraseña.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailSender:
    """Encapsula el envío de correos HTML usados por el sistema."""

    def __init__(self):
        self.remitente = "itsa.secretaria.academica@gmail.com"
        self.clave = "xttw azfo wmdg lixy"

    def _enviar_html(self, destino, asunto, cuerpo_html):
        mensaje = MIMEMultipart("alternative")
        mensaje["From"] = self.remitente
        mensaje["To"] = destino
        mensaje["Subject"] = asunto
        mensaje.attach(MIMEText(cuerpo_html, "html", "utf-8"))

        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(self.remitente, self.clave)
        servidor.sendmail(self.remitente, destino, mensaje.as_string())
        servidor.quit()

    def enviar_datos_acceso(self, destino, nombre, matricula, email_institucional):
        logo_url = "https://itsa-qr-prueba.cyber2vuab.uk/static/resources/logo.png"
        asunto = "Datos de acceso - ITSA QR"

        cuerpo_html = f"""
        <html>
        <body style="margin:0; padding:0; font-family: Arial, sans-serif; background-color:#f4f4f4;">
            <div style="max-width:600px; margin:auto; background:white; border-radius:10px; overflow:hidden;">
                <div style="background:#b30000; padding:20px; text-align:center;">
                    <img src="{logo_url}" style="width:80px; background:white; border-radius:50%; padding:10px;">
                    <h2 style="color:white; margin:10px 0 0 0;">Instituto Tecnológico Superior de Atlixco</h2>
                </div>

                <div style="padding:25px; text-align:center;">
                    <h3 style="color:#333;">Hola {nombre}</h3>
                    <p style="color:#555;">Tu acceso al sistema fue generado correctamente.</p>

                    <div style="margin:25px 0; padding:15px; border:1px solid #ddd; border-radius:8px; background:#fafafa;">
                        <p><strong>Matrícula:</strong> {matricula}</p>
                        <p><strong>Correo institucional:</strong> {email_institucional}</p>
                        <p><strong>Contraseña:</strong> La misma que utilizaste en el panel</p>
                    </div>

                    <p style="color:#555;">Ya puedes iniciar sesión en el sistema.</p>
                    <a href="https://itsa-qr-prueba.cyber2vuab.uk">Inicia sesión</a>
                </div>

                <div style="background:#111; color:#ccc; text-align:center; padding:15px; font-size:12px;">
                    © ITSA - Sistema QR<br>NO RESPONDER ESTE CORREO
                </div>
            </div>
        </body>
        </html>
        """

        self._enviar_html(destino, asunto, cuerpo_html)

    def enviar_correo_confirmacion_password(
        self, destino, nombre, matricula, email_institucional
    ):
        logo_url = "https://itsa-qr-prueba.cyber2vuab.uk/static/resources/logo.png"
        asunto = "Confirmación de cambio de contraseña - ITSA QR"

        cuerpo_html = f"""
        <html>
        <body style="margin:0; padding:0; font-family: Arial, sans-serif; background-color:#f4f4f4;">
            <div style="max-width:600px; margin:auto; background:white; border-radius:10px; overflow:hidden;">
                <div style="background:#b30000; padding:20px; text-align:center;">
                    <img src="{logo_url}" style="width:80px; background:white; border-radius:50%; padding:10px;">
                    <h2 style="color:white; margin:10px 0 0 0;">Instituto Tecnológico Superior de Atlixco</h2>
                </div>

                <div style="padding:25px; text-align:center;">
                    <h3 style="color:#333;">Hola {nombre}</h3>
                    <p style="color:#555;">Se confirmó un cambio de contraseña en tu cuenta institucional.</p>

                    <div style="margin:25px 0; padding:15px; border:1px solid #ddd; border-radius:8px; background:#fafafa;">
                        <p><strong>Matrícula:</strong> {matricula}</p>
                        <p><strong>Correo institucional:</strong> {email_institucional}</p>
                    </div>

                    <p style="color:#555;">Si tú no realizaste este cambio, repórtalo de inmediato.</p>
                </div>

                <div style="background:#111; color:#ccc; text-align:center; padding:15px; font-size:12px;">
                    © ITSA - Sistema QR<br>NO RESPONDER ESTE CORREO
                </div>
            </div>
        </body>
        </html>
        """

        self._enviar_html(destino, asunto, cuerpo_html)
