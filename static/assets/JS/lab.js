/*
Lógica del panel de laboratorista.

Aquí se controla el menú lateral, la lectura del QR, la consulta del usuario,
el registro del préstamo, la actualización periódica del estado de equipos y
la interacción general del panel del laboratorio.
*/

const botonesMenu = document.querySelectorAll(".btn-menu")
const secciones = document.querySelectorAll(".seccion")
const readerElement = document.getElementById("reader")
const btnToggleMenu = document.getElementById("btnToggleMenu")
const menuMobileOpciones = document.getElementById("menuMobileOpciones")
const sidebarMobile = document.getElementById("sidebarMobile")
const sidebarOverlay = document.getElementById("sidebarOverlay")
const btnCerrarSidebar = document.getElementById("btnCerrarSidebar")
const sidebarTitulo = document.getElementById("sidebarTitulo")

let html5QrCode = null
let scannerActivo = false
let escaneoEnProceso = false
function abrirSidebar() {
    if (sidebarMobile) sidebarMobile.classList.add("activo")
    if (sidebarOverlay) sidebarOverlay.classList.add("activo")
}

function cerrarSidebar() {
    if (sidebarMobile) sidebarMobile.classList.remove("activo")
    if (sidebarOverlay) sidebarOverlay.classList.remove("activo")
}

function obtenerNombreSeccion(idSeccion) {
    const nombres = {
        "seccion-dispositivos": "Dispositivos en uso",
        "seccion-registrar": "Registrar equipo",
        "seccion-prestamo": "Préstamo",
        "seccion-excel": "Excel"
    }
    return nombres[idSeccion] || "Menú"
}

async function buscarQR(contenidoQR) {
    const respuesta = await fetch("/laboratorista/buscar_usuario_qr", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ contenido_qr: contenidoQR })
    })

    const data = await respuesta.json()

    if (data.status !== "ok") {
        Swal.fire({
            icon: "error",
            title: "Error",
            text: data.message || "No se encontró el usuario"
        })
        return
    }

    document.getElementById("txtMatricula").textContent = data.usuario.matricula
    document.getElementById("txtNombre").textContent = data.usuario.nombre_completo
    document.getElementById("txtCorreo").textContent = data.usuario.email
    document.getElementById("txtTipo").textContent = data.usuario.tipo_usuario
    document.getElementById("txtCarrera").textContent = data.usuario.carrera

    document.getElementById("matricula_usuario").value = data.usuario.matricula
    document.getElementById("tipo_usuario").value = data.usuario.tipo_usuario
}

async function iniciarScanner() {
    if (scannerActivo) return

    try {
        readerElement.innerHTML = ""
        html5QrCode = new Html5Qrcode("reader")

        const cameras = await Html5Qrcode.getCameras()

        if (!cameras || cameras.length === 0) {
            readerElement.innerHTML = "No se detectó ninguna cámara"
            return
        }

        let camaraId = cameras[0].id

        const trasera = cameras.find(c =>
            (c.label || "").toLowerCase().includes("back") ||
            (c.label || "").toLowerCase().includes("rear") ||
            (c.label || "").toLowerCase().includes("trasera")
        )

        if (trasera) {
            camaraId = trasera.id
        }

        await html5QrCode.start(
            camaraId,
            {
                fps: 10,
                qrbox: { width: 180, height: 180 }
            },
            async (decodedText) => {
                if (escaneoEnProceso) return
                escaneoEnProceso = true

                try {
                    await buscarQR(decodedText)
                    await detenerScanner()
                } catch (e) {
                    escaneoEnProceso = false
                }
            },
            () => { }
        )

        scannerActivo = true
        escaneoEnProceso = false
    } catch (error) {
        readerElement.innerHTML = "No se pudo iniciar la cámara. Revisa permisos del navegador."
        console.error(error)
    }
}

async function detenerScanner() {
    if (!html5QrCode) return

    try {
        if (scannerActivo) {
            await html5QrCode.stop()
        }
        await html5QrCode.clear()
    } catch (error) {
        console.error(error)
    }

    html5QrCode = null
    scannerActivo = false
    escaneoEnProceso = false
    readerElement.innerHTML = "Activa esta sección para iniciar la cámara"
}

async function activarSeccion(idSeccion) {
    botonesMenu.forEach(b => {
        b.classList.remove("activo")
        if (b.dataset.seccion === idSeccion) {
            b.classList.add("activo")
        }
    })

    secciones.forEach(s => s.classList.remove("activa"))
    const seccionActiva = document.getElementById(idSeccion)
    if (seccionActiva) {
        seccionActiva.classList.add("activa")
    }

    if (sidebarTitulo) {
        sidebarTitulo.textContent = obtenerNombreSeccion(idSeccion)
    }

    cerrarSidebar()

    if (idSeccion === "seccion-prestamo") {
        setTimeout(() => {
            iniciarScanner()
        }, 300)
    } else {
        await detenerScanner()
    }
}

botonesMenu.forEach(boton => {
    boton.addEventListener("click", async () => {
        await activarSeccion(boton.dataset.seccion)
    })
})

if (btnToggleMenu) {
    btnToggleMenu.addEventListener("click", () => {
        abrirSidebar()
    })
}

if (btnCerrarSidebar) {
    btnCerrarSidebar.addEventListener("click", () => {
        cerrarSidebar()
    })
}

if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", () => {
        cerrarSidebar()
    })
}

async function actualizarDispositivosTiempoReal() {
    try {
        const respuesta = await fetch("/laboratorista/equipos_estado")
        const data = await respuesta.json()

        if (data.status !== "ok") return

        const grid = document.getElementById("gridDispositivos")
        if (!grid) return

        let html = ""

        data.equipos.forEach(equipo => {
            html += `
                <div class="card-dispositivo ${equipo.estado}">
                    <div class="img-box">
                        <img src="/static/resources/monitor.png" alt="Equipo">
                    </div>
                    <h3>${equipo.nombre_equipo}</h3>
                    ${equipo.estado !== "disponible" && equipo.nombre_usuario
                    ? `<p class="nombre-ocupante">${equipo.nombre_usuario}</p>`
                    : ""
                }
                </div>
            `
        })

        grid.innerHTML = html

        if (data.vencidos && data.vencidos.length > 0) {
            Swal.fire({
                icon: "warning",
                title: "Tiempo terminado",
                text: "Se acabó el tiempo del dispositivo: " + data.vencidos.join(", ")
            })
        }
    } catch (error) {
        console.log("No se pudo actualizar la lista de dispositivos")
    }
}

setInterval(actualizarDispositivosTiempoReal, 5000)