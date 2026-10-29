# Sistema CTech - Control de Acceso, Bitácoras y Tutorías vía Código QR

Aplicación web diseñada para la Benemérita Universidad Autónoma de Puebla (BUAP) enfocada en un Sistema de Control de Acceso, Bitácoras y Tutorías vía Código QR. El sistema centraliza la gestión de laboratorios garantizando el seguimiento de usuarios y equipos institucionales.

## Características Principales

*   **Gestión Multiusuario:** El sistema gestiona el acceso con diferentes roles: Alumno, Maestro, Laboratorista.
*   **Escaneo QR en Tiempo Real:** Genera y lee códigos QR mediante la cámara web en tiempo real. El tiempo de respuesta del escaneo QR es menor a 500 ms.
*   **Bitácora Detallada:** Registra la entrada, salida, edificio, salón y estado del equipo en los laboratorios de la BUAP al escanear el código QR.
*   **Gestión Académica:** El maestro puede agendar sesiones, registrar observaciones y confirmar asistencia con QR.
*   **Exportación de Reportes:** Permite la descarga de reportes filtrados en formatos Excel (.xlsx) y PDF.
*   **Notificaciones Automatizadas:** Envía correos electrónicos automáticos para notificaciones y recuperación de accesos.
*   **Accesibilidad y Desempeño:** Mantiene una disponibilidad del sistema del 99.8% durante el ciclo escolar. Presenta una interfaz web adaptable a computadoras y teléfonos móviles.
*   **Seguridad Integrada:** Implementa seguridad en contraseñas con encriptación y tokens de validación temporal.

## Tecnologías y Librerías Utilizadas

El desarrollo está construido sobre Python y MySQL, apoyándose en las siguientes librerías clave para su funcionamiento:

*   **Flask:** Framework principal para levantar el servidor web, gestionar el enrutamiento y manejar la lógica del backend.
*   **MySQL Connector / PyMySQL:** Controlador para gestionar la conexión, consultas y trazabilidad de datos en la base de datos MySQL.
*   **qrcode:** Librería encargada de la generación dinámica de las credenciales y accesos rápidos en formato QR.
*   **OpenPyXL:** Herramienta utilizada para la construcción y exportación de las bitácoras filtradas en formato Excel (.xlsx).
*   **ReportLab:** Motor para la creación nativa y diseño estructurado de los reportes en formato PDF.

## Equipo de Desarrollo

El proyecto fue hecho por el siguiente equipo de desarrolladores anónimos:
*   Voltex
*   Kik340
*   Zalo
*   OvejaTactic
*   Gusano

## Requisitos Previos

*   Python 3.10 o superior.
*   Servidor MySQL en ejecución.
*   Cámara web configurada para el escaneo de credenciales.

## Instalación y Uso

1.  Clona el repositorio en tu máquina local:
    ```bash
    git clone [https://github.com/kik340/Sistema-CTech.git](https://github.com/kik340/Sistema-CTech.git)
    cd Sistema-CTech
    ```
2.  Crea y activa un entorno virtual para aislar las dependencias:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En sistemas Linux/macOS
    # En algunos sistemas Linux con fish source venv/bin/activate.fish
    # En Windows usa: venv\Scripts\activate
    ```
3.  Instala las dependencias del proyecto:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configura tus credenciales de MySQL y detalles de conexión dentro del archivo de variables de entorno de la aplicación.
5.  Inicia el servidor:
    ```bash
    python app.py
    ```