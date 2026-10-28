/*
Lógica del panel del maestro / docente.

Se encarga de la navegación interna por secciones, del lector QR con cámara o
entrada manual, y de mostrar los datos del alumno detectado.

Además, incluye la funcionalidad de QR Rotativo (el maestro genera QR, los alumnos escanean)
que cambia automáticamente después de cada escaneo.
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

    // =====================================================
    // ESCÁNER QR PARA LEER QR DE ALUMNOS
    // =====================================================

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

    function soportaCamara() {
        return !!(
            navigator.mediaDevices &&
            navigator.mediaDevices.getUserMedia &&
            navigator.mediaDevices.enumerateDevices
        )
    }

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

    function ocultarControlesCamara() {
        if (selectCamara) selectCamara.style.display = "none"
        if (btnIniciarEscaner) btnIniciarEscaner.style.display = "none"
        if (btnDetenerEscaner) btnDetenerEscaner.style.display = "none"
    }

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
                () => {}
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
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ contenido_qr: contenidoQr })
        })
        .then(async (response) => {
            const data = await response.json()
            return { ok: response.ok, status: response.status, data: data }
        })
    }

    function procesarQr(texto, detenerCamaraAlLeer) {
        const contenidoQr = (texto || "").trim()
        if (contenidoQr === "") return
        if (bloqueoLectura) return
        if (contenidoQr === ultimoTexto) return

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
                if (qrKeyboardInput) qrKeyboardInput.value = ""
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
                setTimeout(() => { qrKeyboardInput.focus() }, 100)
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
    if (contenedorQrManual) contenedorQrManual.style.display = "none"
    limpiarResultado()

    // =====================================================
    // QR ROTATIVO (MAESTRO GENERA QR, ALUMNOS ESCANEAN)
    // =====================================================

    let intervaloQR = null
    let sesionActivaQR = false
    let sesionIdActivo = null

    const selectGrupoRotativo = document.getElementById("selectGrupoRotativo")
    const qrRotativoInfo = document.getElementById("qrRotativoInfo")
    const qrRotativoImg = document.getElementById("qrRotativoImg")
    const btnIniciarSesionQR = document.getElementById("btnIniciarSesionQR")
    const btnDetenerSesionQR = document.getElementById("btnDetenerSesionQR")
    const btnActualizarQR = document.getElementById("btnActualizarQR")
    const totalAsistenciasSpan = document.getElementById("totalAsistencias")
    const totalAlumnosGrupo = document.getElementById("totalAlumnosGrupo")
    const listaAsistenciasRotativo = document.getElementById("listaAsistenciasRotativo")
    const qrEstado = document.getElementById("qrEstado")

    async function cargarInfoGrupo() {
        const grupoId = selectGrupoRotativo ? selectGrupoRotativo.value : null
        if (!grupoId) {
            if (qrRotativoInfo) qrRotativoInfo.style.display = "none"
            return
        }

        if (qrRotativoInfo) qrRotativoInfo.style.display = "block"

        try {
            const response = await fetch(`/maestro/obtener_info_grupo/${grupoId}`)
            const data = await response.json()
            if (data.status === "ok" && totalAlumnosGrupo) {
                totalAlumnosGrupo.textContent = data.total_alumnos
            } else if (totalAlumnosGrupo) {
                totalAlumnosGrupo.textContent = "Cargando..."
            }
        } catch (error) {
            console.error("Error al cargar información del grupo:", error)
            if (totalAlumnosGrupo) totalAlumnosGrupo.textContent = "Error"
        }
    }

    async function iniciarSesionQR() {
        const grupoId = selectGrupoRotativo ? selectGrupoRotativo.value : null;
        const parcial = document.getElementById('selectParcial') ? document.getElementById('selectParcial').value : '1';
        
        if (!grupoId) {
            if (typeof Swal !== "undefined") {
                Swal.fire({
                    icon: "warning",
                    title: "Selecciona un grupo",
                    text: "Debes seleccionar un grupo antes de iniciar la sesión"
                });
            }
            return;
        }

        if (typeof Swal !== "undefined") {
            Swal.fire({
                title: "Iniciando sesión...",
                text: "Por favor espera",
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading()
            });
        }

        try {
            const response = await fetch(`/maestro/iniciar_sesion_qr/${grupoId}`, {
                method: "POST",
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ parcial: parcial })
            });
            const data = await response.json();

            if (data.status === "ok") {
                sesionIdActivo = data.sesion_id;
                sesionActivaQR = true;

                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "success",
                        title: "Sesión iniciada",
                        text: data.message,
                        timer: 2000,
                        showConfirmButton: false
                    });
                }

                if (btnIniciarSesionQR) btnIniciarSesionQR.style.display = "none";
                if (btnDetenerSesionQR) btnDetenerSesionQR.style.display = "inline-block";
                if (btnActualizarQR) btnActualizarQR.style.display = "inline-block";

                cargarQRRotativo();
                cargarAsistenciasRotativo();

                if (intervaloQR) clearInterval(intervaloQR);
                intervaloQR = setInterval(() => {
                    if (sesionActivaQR) {
                        cargarQRRotativo();
                        cargarAsistenciasRotativo();
                    }
                }, 5000);
            } else {
                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "error",
                        title: "Error",
                        text: data.message || "No se pudo iniciar la sesión"
                    });
                }
            }
        } catch (error) {
            console.error("Error al iniciar sesión QR:", error);
            if (typeof Swal !== "undefined") {
                Swal.fire({
                    icon: "error",
                    title: "Error",
                    text: "Error de conexión con el servidor"
                });
            }
        }
    }

    async function cargarQRRotativo() {
        if (!sesionActivaQR || !sesionIdActivo) return

        try {
            const response = await fetch(`/maestro/obtener_qr_sesion/${sesionIdActivo}`)
            const data = await response.json()

            if (data.status === "ok") {
                if (qrRotativoImg) qrRotativoImg.src = `data:image/png;base64,${data.qr_base64}`
                if (totalAsistenciasSpan) totalAsistenciasSpan.textContent = data.total_asistencias

                if (qrEstado) {
                    if (data.activa) {
                        qrEstado.innerHTML = '<span class="estado-activo">🟢 Sesión activa - Escaneando...</span>'
                    } else {
                        qrEstado.innerHTML = '<span class="estado-inactivo">🔴 Sesión finalizada</span>'
                    }
                }
            } else if (data.status === "sesion_terminada") {
                sesionActivaQR = false
                if (intervaloQR) clearInterval(intervaloQR)
                if (qrEstado) qrEstado.innerHTML = '<span class="estado-inactivo">⏹️ Sesión finalizada</span>'
                if (btnIniciarSesionQR) btnIniciarSesionQR.style.display = "inline-block"
                if (btnDetenerSesionQR) btnDetenerSesionQR.style.display = "none"
                if (btnActualizarQR) btnActualizarQR.style.display = "none"
            }
        } catch (error) {
            console.error("Error al cargar QR:", error)
            if (qrEstado) {
                qrEstado.innerHTML = '<span class="estado-inactivo">❌ Error al cargar QR</span>'
            }
        }
    }

    async function cargarAsistenciasRotativo() {
        if (!sesionIdActivo) return

        try {
            const response = await fetch(`/maestro/obtener_asistencias_sesion/${sesionIdActivo}`)
            const data = await response.json()

            if (listaAsistenciasRotativo) {
                if (data.status === "ok" && data.asistencias && data.asistencias.length > 0) {
                    const html = data.asistencias.map(a => `
                        <div class="asistencia-item">
                            <span class="asistencia-nombre">👤 ${a.nombre || a.nombre_completo || a.alumno_nombre || 'Alumno'}</span>
                            <span class="asistencia-matricula">📋 ${a.matricula || a.alumno_matricula || ''}</span>
                            <span class="asistencia-hora">⏰ ${a.hora || a.fecha_asistencia || ''}</span>
                        </div>
                    `).join("")
                    listaAsistenciasRotativo.innerHTML = html
                } else {
                    listaAsistenciasRotativo.innerHTML = '<p class="texto-vacio">Aún no hay asistencias registradas</p>'
                }
            }
        } catch (error) {
            console.error("Error al cargar asistencias:", error)
        }
    }

    async function detenerSesionQR() {
        if (!sesionIdActivo) return

        if (typeof Swal !== "undefined") {
            Swal.fire({
                title: "¿Detener sesión?",
                text: "Los alumnos ya no podrán escanear el QR",
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#b30000",
                confirmButtonText: "Sí, detener",
                cancelButtonText: "Cancelar"
            }).then(async (result) => {
                if (result.isConfirmed) {
                    await ejecutarDetenerSesion()
                }
            })
        } else {
            await ejecutarDetenerSesion()
        }
    }

    async function ejecutarDetenerSesion() {
        try {
            const response = await fetch(`/maestro/detener_sesion_qr/${sesionIdActivo}`, { method: "POST" })
            const data = await response.json()

            if (data.status === "ok") {
                sesionActivaQR = false
                if (intervaloQR) clearInterval(intervaloQR)

                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "success",
                        title: "Sesión detenida",
                        text: data.message,
                        timer: 2000,
                        showConfirmButton: false
                    })
                }

                if (btnIniciarSesionQR) btnIniciarSesionQR.style.display = "inline-block"
                if (btnDetenerSesionQR) btnDetenerSesionQR.style.display = "none"
                if (btnActualizarQR) btnActualizarQR.style.display = "none"
                if (qrEstado) qrEstado.innerHTML = '<span class="estado-inactivo">⏹️ Sesión finalizada</span>'
                sesionIdActivo = null
            }
        } catch (error) {
            console.error("Error al detener sesión:", error)
        }
    }

    async function actualizarQRManual() {
        if (sesionActivaQR && sesionIdActivo) {
            await cargarQRRotativo()
            if (typeof Swal !== "undefined") {
                Swal.fire({
                    icon: "success",
                    title: "QR actualizado",
                    text: "El código QR ha sido renovado",
                    timer: 1500,
                    showConfirmButton: false
                })
            }
        }
    }

    if (selectGrupoRotativo) {
        selectGrupoRotativo.addEventListener("change", function() {
            cargarInfoGrupo()
            if (sesionActivaQR) {
                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "info",
                        title: "Grupo cambiado",
                        text: "La sesión anterior se ha cerrado. Inicia una nueva sesión para el grupo seleccionado.",
                        timer: 2000
                    })
                }
                sesionActivaQR = false
                sesionIdActivo = null
                if (intervaloQR) clearInterval(intervaloQR)
                if (btnIniciarSesionQR) btnIniciarSesionQR.style.display = "inline-block"
                if (btnDetenerSesionQR) btnDetenerSesionQR.style.display = "none"
                if (btnActualizarQR) btnActualizarQR.style.display = "none"
                if (qrEstado) qrEstado.innerHTML = '<span class="estado-activo">🔴 Esperando iniciar sesión...</span>'
                if (qrRotativoImg) qrRotativoImg.src = ""
                if (totalAsistenciasSpan) totalAsistenciasSpan.textContent = "0"
                if (listaAsistenciasRotativo) listaAsistenciasRotativo.innerHTML = '<p class="texto-vacio">Aún no hay asistencias registradas</p>'
            }
        })
    }
    if (btnIniciarSesionQR) {
        btnIniciarSesionQR.addEventListener("click", iniciarSesionQR)
    }
    if (btnDetenerSesionQR) {
        btnDetenerSesionQR.addEventListener("click", detenerSesionQR)
    }
    if (btnActualizarQR) {
        btnActualizarQR.addEventListener("click", actualizarQRManual)
    }
})();