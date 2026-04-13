/*
Lógica del panel de tutor.

Se encarga de la navegación interna por secciones, del lector QR con cámara o
entrada manual, y de mostrar los datos del alumno o externo detectado para las
acciones del tutor.
*/

(function () {
    const botonesMenu = document.querySelectorAll(".btn-menu")
    const secciones = document.querySelectorAll(".seccion-panel")

    botonesMenu.forEach(boton => {
        boton.addEventListener("click", () => {
            const destino = boton.getAttribute("data-seccion")

            botonesMenu.forEach(b => b.classList.remove("activo"))
            secciones.forEach(s => s.classList.remove("activa"))

            boton.classList.add("activo")
            document.getElementById(destino).classList.add("activa")
        })
    })

    const btnCargarCamaras = document.getElementById("btnCargarCamaras")
    const btnIniciarEscaner = document.getElementById("btnIniciarEscaner")
    const btnDetenerEscaner = document.getElementById("btnDetenerEscaner")
    const selectCamara = document.getElementById("selectCamara")

    const btnModoLector = document.getElementById("btnModoLector")
    const contenedorQrManual = document.getElementById("contenedorQrManual")
    const qrKeyboardInput = document.getElementById("qrKeyboardInput")
    const btnProcesarQrManual = document.getElementById("btnProcesarQrManual")

    const resultadoAlumno = document.getElementById("resultadoAlumno")
    const resMatricula = document.getElementById("resMatricula")
    const resNombre = document.getElementById("resNombre")
    const resEmail = document.getElementById("resEmail")
    const resCarrera = document.getElementById("resCarrera")
    const resCorreoQr = document.getElementById("resCorreoQr")

    let html5QrCode = null
    let escanerActivo = false
    let ultimoTexto = ""
    let listaCamaras = []
    let bloqueoLectura = false

    /* Muestra una alerta reutilizable para mensajes del sistema. */

    function mostrarAlerta(icon, title, text) {
        if (typeof Swal !== "undefined") {
            Swal.fire({
                icon: icon,
                title: title,
                text: text,
                confirmButtonText: "Aceptar"
            })
        } else {
            alert(title + ": " + text)
        }
    }

    /* Valida si el navegador soporta acceso a cámara. */

    function soportaCamara() {
        return !!(
            navigator.mediaDevices &&
            navigator.mediaDevices.getUserMedia &&
            navigator.mediaDevices.enumerateDevices
        )
    }

    /* Oculta y limpia el bloque donde se muestran los datos del alumno leído. */

    function limpiarResultado() {
        if (resultadoAlumno) {
            resultadoAlumno.style.display = "none"
        }

        if (resMatricula) resMatricula.textContent = ""
        if (resNombre) resNombre.textContent = ""
        if (resEmail) resEmail.textContent = ""
        if (resCarrera) resCarrera.textContent = ""
        if (resCorreoQr) resCorreoQr.textContent = ""
    }

    /* Pinta en pantalla la información obtenida después de leer un QR. */

    function mostrarResultado(data) {
        if (resultadoAlumno) {
            resultadoAlumno.style.display = "block"
        }

        if (resMatricula) resMatricula.textContent = data.alumno.matricula || ""
        if (resNombre) resNombre.textContent = data.alumno.nombre || ""
        if (resEmail) resEmail.textContent = data.alumno.email || ""
        if (resCarrera) resCarrera.textContent = data.alumno.carrera || ""
        if (resCorreoQr) resCorreoQr.textContent = data.correo_qr || ""
    }

    /* Oculta los controles relacionados con la cámara cuando no se pueden usar. */

    function ocultarControlesCamara() {
        if (selectCamara) selectCamara.style.display = "none"
        if (btnIniciarEscaner) btnIniciarEscaner.style.display = "none"
        if (btnDetenerEscaner) btnDetenerEscaner.style.display = "none"
    }

    /* Vuelve visibles los controles de cámara cuando ya hay permisos y dispositivos. */

    function mostrarControlesCamara() {
        if (selectCamara) selectCamara.style.display = "inline-block"
        if (btnIniciarEscaner) btnIniciarEscaner.style.display = "inline-block"
        if (btnDetenerEscaner) btnDetenerEscaner.style.display = "inline-block"
    }

    async function pedirPermisoCamara() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "environment" }
            })
            stream.getTracks().forEach(track => track.stop())
            return true
        } catch (error) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true })
                stream.getTracks().forEach(track => track.stop())
                return true
            } catch (error2) {
                console.error("Error al pedir permiso:", error2)
                mostrarAlerta("error", "Cámara", "No se concedió permiso para usar la cámara")
                return false
            }
        }
    }

    async function cargarCamaras() {
        if (!selectCamara) return

        if (!soportaCamara()) {
            mostrarAlerta("error", "Cámara", "Este navegador no soporta acceso a cámaras")
            ocultarControlesCamara()
            return
        }

        const permiso = await pedirPermisoCamara()
        if (!permiso) {
            ocultarControlesCamara()
            return
        }

        try {
            const devices = await navigator.mediaDevices.enumerateDevices()
            listaCamaras = devices.filter(device => device.kind === "videoinput")

            selectCamara.innerHTML = ""

            if (listaCamaras.length === 0) {
                const option = document.createElement("option")
                option.value = ""
                option.textContent = "No se encontraron cámaras"
                selectCamara.appendChild(option)

                ocultarControlesCamara()
                mostrarAlerta("warning", "Cámara", "No se encontraron cámaras disponibles")
                return
            }

            listaCamaras.forEach((camara, index) => {
                const option = document.createElement("option")
                option.value = camara.deviceId

                if (camara.label && camara.label.trim() !== "") {
                    option.textContent = camara.label
                } else {
                    option.textContent = "Cámara " + (index + 1)
                }

                selectCamara.appendChild(option)
            })

            mostrarControlesCamara()

            if (btnCargarCamaras) {
                btnCargarCamaras.style.display = "none"
            }

            mostrarAlerta("success", "Cámara", "Cámaras cargadas correctamente")
        } catch (error) {
            console.error("Error al enumerar cámaras:", error)
            ocultarControlesCamara()
            mostrarAlerta("error", "Cámara", "No se pudieron listar las cámaras")
        }
    }

    /* Detiene el lector QR activo y limpia su estado interno. */

    function detenerEscaner() {
        return new Promise((resolve) => {
            if (!html5QrCode || !escanerActivo) {
                resolve()
                return
            }

            html5QrCode.stop().then(() => {
                html5QrCode.clear().catch(() => {})
                html5QrCode = null
                escanerActivo = false
                ultimoTexto = ""
                resolve()
            }).catch((error) => {
                console.error("Error al detener escáner:", error)
                try {
                    if (html5QrCode) {
                        html5QrCode.clear().catch(() => {})
                    }
                } catch (e) {}
                html5QrCode = null
                escanerActivo = false
                ultimoTexto = ""
                resolve()
            })
        })
    }

    async function iniciarEscaner() {
        if (!selectCamara || !selectCamara.value) {
            mostrarAlerta("warning", "Cámara", "Primero carga y selecciona una cámara")
            return
        }

        if (escanerActivo) {
            await detenerEscaner()
        }

        html5QrCode = new Html5Qrcode("reader")

        try {
            await html5QrCode.start(
                selectCamara.value,
                {
                    fps: 10,
                    qrbox: 250,
                    aspectRatio: 1.0
                },
                (qrCodeMessage) => {
                    procesarQr(qrCodeMessage, true)
                },
                () => {
                }
            )

            escanerActivo = true
            mostrarAlerta("success", "Escáner", "Escáner iniciado correctamente")
        } catch (error) {
            console.error("Error al iniciar escáner:", error)
            html5QrCode = null
            escanerActivo = false
            mostrarAlerta("error", "Escáner", "No se pudo iniciar la cámara seleccionada")
        }
    }

    function buscarAlumnoPorQr(contenidoQr) {
        return fetch("/buscar_alumno_qr", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                contenido_qr: contenidoQr
            })
        })
        .then(async (response) => {
            const data = await response.json()
            return {
                ok: response.ok,
                status: response.status,
                data: data
            }
        })
    }

    function procesarQr(texto, detenerCamaraAlLeer) {
        const contenidoQr = (texto || "").trim()

        if (contenidoQr === "") {
            return
        }

        if (bloqueoLectura) {
            return
        }

        if (contenidoQr === ultimoTexto) {
            return
        }

        bloqueoLectura = true
        ultimoTexto = contenidoQr

        buscarAlumnoPorQr(contenidoQr)
            .then((resultado) => {
                const data = resultado.data

                if (data.status === "ok") {
                    mostrarResultado(data)
                    mostrarAlerta("success", "Alumno encontrado", "Se encontró al estudiante correctamente")

                    if (detenerCamaraAlLeer) {
                        detenerEscaner()
                    }

                    return
                }

                if (data.status === "not_found") {
                    limpiarResultado()
                    mostrarAlerta("warning", "No encontrado", "La matrícula no existe en la base de datos")
                    return
                }

                limpiarResultado()
                mostrarAlerta("error", "Error", data.message || "Ocurrió un error al buscar")
            })
            .catch((error) => {
                console.error("Error en fetch:", error)
                limpiarResultado()
                mostrarAlerta("error", "Error", "Falló la consulta al servidor")
            })
            .finally(() => {
                if (qrKeyboardInput) {
                    qrKeyboardInput.value = ""
                }

                setTimeout(() => {
                    bloqueoLectura = false
                    ultimoTexto = ""
                }, 1500)
            })
    }

    if (btnModoLector && contenedorQrManual && qrKeyboardInput) {
        btnModoLector.addEventListener("click", () => {
            const visible = contenedorQrManual.style.display === "block"

            if (visible) {
                contenedorQrManual.style.display = "none"
                btnModoLector.textContent = "Usar lector físico"
                qrKeyboardInput.value = ""
            } else {
                contenedorQrManual.style.display = "block"
                btnModoLector.textContent = "Ocultar lector físico"
                setTimeout(() => {
                    qrKeyboardInput.focus()
                }, 100)
            }
        })
    }

    if (btnProcesarQrManual && qrKeyboardInput) {
        btnProcesarQrManual.addEventListener("click", () => {
            procesarQr(qrKeyboardInput.value, false)
        })

        qrKeyboardInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault()
                procesarQr(qrKeyboardInput.value, false)
            }
        })
    }

    if (btnCargarCamaras) {
        btnCargarCamaras.addEventListener("click", cargarCamaras)
    }

    if (btnIniciarEscaner) {
        btnIniciarEscaner.addEventListener("click", iniciarEscaner)
    }

    if (btnDetenerEscaner) {
        btnDetenerEscaner.addEventListener("click", () => {
            detenerEscaner().then(() => {
                mostrarAlerta("info", "Escáner", "Escáner detenido")
            })
        })
    }

    ocultarControlesCamara()

    if (contenedorQrManual) {
        contenedorQrManual.style.display = "none"
    }

    limpiarResultado()
})()