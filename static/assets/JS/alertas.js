/*
Archivo central de alertas del sistema.

Se encarga de leer el parámetro "r" de la URL, traducirlo a un mensaje legible
y mostrar la notificación correspondiente con SweetAlert. También expone una
función global para reutilizar alertas desde otros módulos.
*/

(function () {
    /* Muestra una alerta reutilizable para mensajes del sistema. */
    function mostrarAlerta(icono, titulo, mensaje) {
        Swal.fire({
            icon: icono,
            title: titulo,
            text: mensaje
        })
    }

    window.mostrarAlerta = mostrarAlerta

    const mensajes = {
        login: {
            error: {
                "user_wrong": "El usuario no existe",
                "password_wrong": "La contraseña está incorrecta",
                "empty_login": "No puede haber datos vacíos",
                "matricula_wrong": "La matrícula no tiene un formato válido",
                "tipo_wrong": "No se pudo identificar el tipo de usuario"
            },
            success: {
                "login_ok": "Inicio de sesión correcto",
                "password_changed": "La contraseña se cambió correctamente. Inicia sesión nuevamente."
            }
        },

        registro: {
            error: {
                "empty_register": "Todos los campos son obligatorios",
                "matricula_exists": "La matrícula ya existe",
                "email_exists": "El correo ya está registrado",
                "empty_request": "Todos los campos de la solicitud son obligatorios",
                "error": "Ocurrió un error al procesar la solicitud",
                "not_found": "No se encontró el registro solicitado"
            },
            success: {
                "request_ok": "Solicitud enviada correctamente",
                "ok": "Operación realizada correctamente"
            }
        },

        tutor: {
            error: {
                "error": "Ocurrió un problema en la operación",
                "group_exists": "Ese grupo ya está registrado",
                "group_occupied": "Ese grupo ya tiene tutor asignado",
                "student_not_found": "No se encontró el alumno",
                "group_not_found": "No se encontró el grupo",
                "student_group_exists": "Ese alumno ya está asignado a ese grupo",
                "subject_exists": "Esa materia ya está registrada para esa carrera y semestre"
            },
            success: {
                "approved": "Solicitud aprobada correctamente",
                "rejected": "Solicitud rechazada correctamente",
                "group_assigned": "Te asignaste el grupo correctamente",
                "student_group_ok": "Alumno agregado al grupo correctamente"
            }
        },

        qr: {
            error: {
                "qr_wrong": "El código QR no tiene un formato válido",
                "qr_not_found": "No se encontró el alumno o externo",
                "qr_expirado": "❌ El QR ha expirado. Solicita uno nuevo al tutor",
                "qr_ya_usado": "⚠️ Este QR ya fue usado por otro alumno. ¡Solicita un QR nuevo!",
                "no_pertenece_grupo": "❌ No perteneces a este grupo",
                "sesion_inactiva": "⏹️ La sesión de tutoría ya finalizó"
            },
            success: {
                "asistencia_registrada": "✅ ¡Asistencia registrada correctamente!"
            }
        },

        escaneo: {
            error: {
                "sin_camara": "❌ No se pudo acceder a la cámara",
                "qr_no_detectado": "❌ No se pudo leer el código QR",
                "error_conexion": "❌ Error de conexión con el servidor",
                "formato_invalido": "❌ Formato de QR inválido"
            },
            info: {
                "buscando_qr": "🔍 Buscando código QR...",
                "alinea_qr": "📱 Alinea el QR del tutor en la cámara",
                "procesando": "📡 Procesando QR..."
            }
        },

        laboratorista: {
            error: {
                "equipment_exists": "El número de serie ya existe o el código ya se repitió",
                "equipment_busy": "Ese equipo ya está prestado o no está disponible",
                "empty_request": "Faltan datos por llenar",
                "error": "Ocurrió un problema en la operación"
            },
            success: {
                "loan_ok": "Préstamo registrado correctamente",
                "device_registered": "Dispositivo registrado correctamente",
                "ok": "Operación realizada correctamente"
            },
            warning: {
                "device_expired": "Se venció el tiempo de uso del dispositivo"
            }
        }
    }

    const busqueda = new URLSearchParams(window.location.search)
    const codigo = busqueda.get("r")
    const dispositivo = busqueda.get("device")

    if (codigo) {
        let mensaje = null
        let tipo = "error"
        let titulo = "Error"

        // Login
        if (mensajes.login.error[codigo]) {
            mensaje = mensajes.login.error[codigo]
            tipo = "error"
            titulo = "Error"
        }

        if (mensajes.login.success[codigo]) {
            mensaje = mensajes.login.success[codigo]
            tipo = "success"
            titulo = "Correcto"
        }

        // Registro
        if (mensajes.registro.error[codigo]) {
            mensaje = mensajes.registro.error[codigo]
            tipo = "error"
            titulo = "Error"
        }

        if (mensajes.registro.success[codigo]) {
            mensaje = mensajes.registro.success[codigo]
            tipo = "success"
            titulo = "Correcto"
        }

        // Tutor
        if (mensajes.tutor.error[codigo]) {
            mensaje = mensajes.tutor.error[codigo]
            tipo = "error"
            titulo = "Error"
        }

        if (mensajes.tutor.success[codigo]) {
            mensaje = mensajes.tutor.success[codigo]
            tipo = "success"
            titulo = "Correcto"
        }

        // QR
        if (mensajes.qr.error[codigo]) {
            mensaje = mensajes.qr.error[codigo]
            tipo = "error"
            titulo = "Error"
        }

        if (mensajes.qr.success[codigo]) {
            mensaje = mensajes.qr.success[codigo]
            tipo = "success"
            titulo = "Correcto"
        }

        // Escaneo
        if (mensajes.escaneo.error[codigo]) {
            mensaje = mensajes.escaneo.error[codigo]
            tipo = "error"
            titulo = "Error"
        }

        if (mensajes.escaneo.info[codigo]) {
            mensaje = mensajes.escaneo.info[codigo]
            tipo = "info"
            titulo = "Información"
        }

        // Laboratorista
        if (mensajes.laboratorista.error[codigo]) {
            mensaje = mensajes.laboratorista.error[codigo]
            tipo = "error"
            titulo = "Error"
        }

        if (mensajes.laboratorista.success[codigo]) {
            mensaje = mensajes.laboratorista.success[codigo]
            tipo = "success"
            titulo = "Correcto"
        }

        if (mensajes.laboratorista.warning[codigo]) {
            mensaje = mensajes.laboratorista.warning[codigo]
            tipo = "warning"
            titulo = "Aviso"
        }

        if (codigo === "device_expired" && dispositivo) {
            mensaje = `Se acabó el tiempo del dispositivo: ${dispositivo}`
            tipo = "warning"
            titulo = "Tiempo terminado"
        }

        if (mensaje) {
            mostrarAlerta(tipo, titulo, mensaje)
        }

        window.history.replaceState({}, document.title, window.location.pathname)
    }
})()