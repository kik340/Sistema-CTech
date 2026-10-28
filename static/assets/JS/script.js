/*
Lógica de la pantalla principal.

Este archivo controla la animación entre login y registro, ajusta alturas del
contenedor según la vista activa, muestra u oculta campos del formulario y
gestiona el botón para ver u ocultar contraseñas.
*/

const panelLogin = document.getElementById("panelLogin")
const panelRegister = document.getElementById("panelRegister")
const panelAzul = document.getElementById("panelAzul")
const contenedor = document.querySelector(".contenedor")
const btnRegistro = document.getElementById("btnRegistro")
const btnLogin = document.getElementById("btnLogin")

const formLogin = panelLogin ? panelLogin.querySelector("form") : null
const formRegister = panelRegister ? panelRegister.querySelector("form") : null

const tipoSolicitud = document.getElementById("tipo_solicitud")
const carreraSelect = document.getElementById("carrera_id")
const motivoInput = document.getElementById("motivo")
const bloqueMotivo = document.getElementById("bloqueMotivo")
const bloqueCarrera = document.getElementById("bloqueCarrera")

let alturaLogin = 0
let alturaRegistro = 0
let vistaActual = "login"
let ultimoAncho = window.innerWidth

/* Detecta si la interfaz está en resolución móvil. */

function esMovil() {
    return window.innerWidth <= 600
}

/* Calcula las alturas necesarias para login y registro según su contenido actual. */

function calcularAlturas() {
    if (formLogin) {
        alturaLogin = formLogin.scrollHeight + 90
    } else {
        alturaLogin = 500
    }

    if (formRegister) {
        alturaRegistro = formRegister.scrollHeight + 120
    } else {
        alturaRegistro = 560
    }
}

/* Ajusta la altura del contenedor principal según la vista activa y el tipo de pantalla. */

function ajustarAlturaActual() {
    calcularAlturas()

    if (esMovil()) {
        if (vistaActual === "registro") {
            contenedor.style.height = Math.max(760, alturaRegistro + 170) + "px"
        } else {
            contenedor.style.height = Math.max(650, alturaLogin + 170) + "px"
        }
    } else {
        if (vistaActual === "registro") {
            contenedor.style.height = Math.max(560, alturaRegistro) + "px"
        } else {
            contenedor.style.height = Math.max(500, alturaLogin) + "px"
        }
    }
}

/* Muestra los campos correctos en registro según si la solicitud es de alumno o externo. */

function actualizarCamposSolicitud() {
    if (!tipoSolicitud || !bloqueMotivo || !bloqueCarrera || !carreraSelect || !motivoInput) {
        return
    }

    if (tipoSolicitud.value === "externo") {
        bloqueMotivo.classList.remove("campo-oculto")
        bloqueCarrera.classList.add("campo-oculto")
        carreraSelect.value = ""
        carreraSelect.disabled = true
        motivoInput.disabled = false
    } else {
        bloqueMotivo.classList.add("campo-oculto")
        bloqueCarrera.classList.remove("campo-oculto")
        motivoInput.value = ""
        motivoInput.disabled = true
        carreraSelect.disabled = false
    }

    setTimeout(() => {
        if (vistaActual === "registro") {
            ajustarAlturaActual()
        }
    }, 50)
}

/* Limpia clases de animación para evitar superposiciones visuales. */

function limpiarEstados() {
    panelLogin.classList.remove("fade-in", "fade-out", "mostrar-login", "ocultar-login")
    panelRegister.classList.remove("fade-in", "fade-out", "mostrar-register", "ocultar-register")
}

/* Activa la vista de registro y mueve el panel decorativo según el dispositivo. */

function mostrarRegistro() {
    vistaActual = "registro"
    limpiarEstados()
    ajustarAlturaActual()

    if (esMovil()) {
        panelLogin.style.display = "block"
        panelRegister.style.display = "block"

        panelAzul.classList.remove("mover-derecha", "mover-izquierda")
        panelAzul.classList.add("mover-abajo")

        panelLogin.classList.add("ocultar-login")
        panelRegister.classList.add("mostrar-register")
    } else {
        panelLogin.style.display = "block"
        panelRegister.style.display = "block"
        panelRegister.style.opacity = "1"

        panelAzul.classList.remove("mover-derecha")
        panelAzul.classList.add("mover-izquierda")

        panelLogin.classList.add("fade-out")

        setTimeout(() => {
            panelLogin.style.display = "none"
            panelRegister.style.display = "block"
            panelRegister.style.opacity = "1"
            panelRegister.classList.add("fade-in")
            ajustarAlturaActual()
        }, 300)
    }
}

/* Activa la vista de login y devuelve el panel decorativo a su posición correspondiente. */

function mostrarLogin() {
    vistaActual = "login"
    limpiarEstados()
    ajustarAlturaActual()

    if (esMovil()) {
        panelLogin.style.display = "block"
        panelRegister.style.display = "block"

        panelAzul.classList.remove("mover-abajo", "mover-izquierda")
        panelAzul.classList.add("mover-derecha")

        panelRegister.classList.add("ocultar-register")
        panelLogin.classList.add("mostrar-login")
    } else {
        panelLogin.style.display = "block"
        panelRegister.style.display = "block"
        panelLogin.style.opacity = "1"

        panelAzul.classList.remove("mover-izquierda")
        panelAzul.classList.add("mover-derecha")

        panelRegister.classList.add("fade-out")

        setTimeout(() => {
            panelRegister.style.display = "none"
            panelLogin.style.display = "block"
            panelLogin.style.opacity = "1"
            panelLogin.classList.add("fade-in")
            ajustarAlturaActual()
        }, 300)
    }
}

/* Reconstruye el estado visual del contenedor según la vista actual. */

function inicializarPaneles() {
    limpiarEstados()

    if (vistaActual === "registro") {
        mostrarRegistro()
    } else {
        mostrarLogin()
    }
}

if (tipoSolicitud) {
    tipoSolicitud.addEventListener("change", actualizarCamposSolicitud)
}

if (btnRegistro) {
    btnRegistro.addEventListener("click", mostrarRegistro)
}

if (btnLogin) {
    btnLogin.addEventListener("click", mostrarLogin)
}

window.addEventListener("load", () => {
    vistaActual = "login"
    actualizarCamposSolicitud()
    mostrarLogin()

    const botones = document.querySelectorAll(".btn-ojo")

    botones.forEach(btn => {
        btn.addEventListener("click", () => {
            const input = btn.parentElement.querySelector("input")
            const img = btn.querySelector("img")

            img.classList.add("animar")

            setTimeout(() => {
                if (input.type === "password") {
                    input.type = "text"
                    img.src = "/static/resources/ojo.png"
                } else {
                    input.type = "password"
                    img.src = "/static/resources/ojo-cerrado.png"
                }

                img.classList.remove("animar")
            }, 120)
        })
    })
})

window.addEventListener("resize", () => {
    const anchoActual = window.innerWidth

    if (anchoActual !== ultimoAncho) {
        ultimoAncho = anchoActual
        ajustarAlturaActual()
        inicializarPaneles()
    }
})