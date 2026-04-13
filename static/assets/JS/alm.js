/*
Lógica del panel de alumno.

Este archivo maneja alertas del panel, apertura y cierre del menú móvil,
selección de imagen, recorte con Cropper y envío de la foto ya procesada
al servidor sin cambiar el flujo visual del usuario.
*/

const mensajes = {
    "image_ok": { icon: "success", title: "Correcto", text: "Imagen subida correctamente" },
    "image_empty": { icon: "error", title: "Error", text: "Debes seleccionar una imagen" },
    "image_wrong": { icon: "error", title: "Error", text: "Formato de imagen no válido" }
}

const busqueda = new URLSearchParams(window.location.search)
const r = busqueda.get("r")

if (r && mensajes[r]) {
    Swal.fire({
        icon: mensajes[r].icon,
        title: mensajes[r].title,
        text: mensajes[r].text
    })
    window.history.replaceState({}, document.title, window.location.pathname)
}

const btnMenuMovil = document.getElementById("btnMenuMovil")
const sidebarAlumno = document.getElementById("sidebarAlumno")
const cerrarSidebar = document.getElementById("cerrarSidebar")
const overlaySidebar = document.getElementById("overlaySidebar")

if (btnMenuMovil) {
    btnMenuMovil.addEventListener("click", () => {
        sidebarAlumno.classList.add("activo")
        overlaySidebar.classList.add("activo")
        btnMenuMovil.style.visibility = "hidden"
    })
}

if (cerrarSidebar) {
    cerrarSidebar.addEventListener("click", () => {
        sidebarAlumno.classList.remove("activo")
        overlaySidebar.classList.remove("activo")
        btnMenuMovil.style.visibility = "visible"
    })
}

if (overlaySidebar) {
    overlaySidebar.addEventListener("click", () => {
        sidebarAlumno.classList.remove("activo")
        overlaySidebar.classList.remove("activo")
    })
}

const inputFoto = document.getElementById("inputFoto")
const btnSeleccionarImagen = document.getElementById("btnSeleccionarImagen")
const modalRecorte = document.getElementById("modalRecorte")
const cerrarModalRecorte = document.getElementById("cerrarModalRecorte")
const btnCancelarRecorte = document.getElementById("btnCancelarRecorte")
const btnGuardarRecorte = document.getElementById("btnGuardarRecorte")
const imagenRecorte = document.getElementById("imagenRecorte")

let cropper = null
let archivoSeleccionado = null

/* Abre el modal de recorte y prepara Cropper con formato cuadrado. */

function abrirModalRecorte(src) {
    imagenRecorte.src = src
    modalRecorte.classList.add("activo")

    if (cropper) {
        cropper.destroy()
        cropper = null
    }

    setTimeout(() => {
        cropper = new Cropper(imagenRecorte, {
            aspectRatio: 1,
            viewMode: 1,
            dragMode: "move",
            autoCropArea: 1,
            responsive: true,
            background: false
        })
    }, 100)
}

/* Cierra el modal, destruye la instancia de recorte y limpia el estado temporal. */

function cerrarRecorte() {
    modalRecorte.classList.remove("activo")

    if (cropper) {
        cropper.destroy()
        cropper = null
    }

    imagenRecorte.src = ""
    inputFoto.value = ""
    archivoSeleccionado = null
}

btnSeleccionarImagen.addEventListener("click", () => {
    inputFoto.click()
})

inputFoto.addEventListener("change", (e) => {
    const archivo = e.target.files[0]

    if (!archivo) return

    const extensionesValidas = ["image/png", "image/jpeg", "image/webp"]

    if (!extensionesValidas.includes(archivo.type)) {
        Swal.fire({
            icon: "error",
            title: "Error",
            text: "Formato de imagen no válido"
        })
        inputFoto.value = ""
        return
    }

    archivoSeleccionado = archivo

    const lector = new FileReader()
    lector.onload = function (ev) {
        abrirModalRecorte(ev.target.result)
    }
    lector.readAsDataURL(archivo)
})

cerrarModalRecorte.addEventListener("click", cerrarRecorte)
btnCancelarRecorte.addEventListener("click", cerrarRecorte)

btnGuardarRecorte.addEventListener("click", () => {
    if (!cropper || !archivoSeleccionado) return

    const extensionOriginal = archivoSeleccionado.name.split(".").pop().toLowerCase()

    let mimeType = "image/png"
    let extensionFinal = "png"

    if (extensionOriginal === "jpg" || extensionOriginal === "jpeg") {
        mimeType = "image/jpeg"
        extensionFinal = "jpg"
    } else if (extensionOriginal === "webp") {
        mimeType = "image/webp"
        extensionFinal = "webp"
    }

    const canvas = cropper.getCroppedCanvas({
        width: 500,
        height: 500,
        imageSmoothingEnabled: true,
        imageSmoothingQuality: "high"
    })

    canvas.toBlob(async (blob) => {
        if (!blob) {
            Swal.fire({
                icon: "error",
                title: "Error",
                text: "No se pudo recortar la imagen"
            })
            return
        }

        const formData = new FormData()
        formData.append("foto", blob, "recorte." + extensionFinal)

        try {
            const respuesta = await fetch("/subir_imagen_alumno", {
                method: "POST",
                body: formData
            })

            if (respuesta.redirected) {
                window.location.href = respuesta.url
                return
            }

            if (respuesta.ok) {
                Swal.fire({
                    icon: "success",
                    title: "Correcto",
                    text: "Imagen subida correctamente"
                }).then(() => {
                    window.location.reload()
                })
            } else {
                Swal.fire({
                    icon: "error",
                    title: "Error",
                    text: "No se pudo subir la imagen"
                })
            }

            cerrarRecorte()
        } catch (error) {
            Swal.fire({
                icon: "error",
                title: "Error",
                text: "Ocurrió un problema al subir la imagen"
            })
        }
    }, mimeType, 0.95)
})