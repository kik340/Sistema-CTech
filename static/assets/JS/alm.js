/*
Lógica del panel de alumno.

Este archivo maneja alertas del panel, apertura y cierre del menú móvil,
selección de imagen, recorte con Cropper y envío de la foto ya procesada
al servidor sin cambiar el flujo visual del usuario.

Además, incluye el escáner QR para que el alumno pueda escanear
el código QR del tutor y registrar su asistencia, y un modal para modificar contraseña.
*/

// =====================================================
// ALERTAS INICIALES
// =====================================================

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

// =====================================================
// MENÚ MÓVIL
// =====================================================

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

// =====================================================
// RECORTE DE IMAGEN (Cropper)
// =====================================================

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

// =====================================================
// ESCÁNER QR PARA REGISTRAR ASISTENCIA DEL TUTOR
// =====================================================

let stream = null
let animationId = null
let modalEscaner = null
let escaneando = false  // Evita múltiples escaneos

/* Inicializa los botones de escáner */
function inicializarBotonesEscaner() {
    const btnEscanear = document.getElementById('btnEscanearTutor')
    const btnEscanearSidebar = document.getElementById('btnEscanearTutorSidebar')
    
    if (btnEscanear) {
        btnEscanear.addEventListener('click', abrirEscaner)
    }
    
    if (btnEscanearSidebar) {
        btnEscanearSidebar.addEventListener('click', abrirEscaner)
    }
}

/* Abre el modal del escáner y solicita permisos de cámara */
function abrirEscaner() {
    if (!modalEscaner) {
        modalEscaner = document.getElementById('modalEscaner')
    }
    
    if (!modalEscaner) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se encontró el escáner QR. Contacta al administrador.'
        })
        return
    }
    
    modalEscaner.style.display = 'flex'
    iniciarCamara()
}

/* Solicita acceso a la cámara del dispositivo */
async function iniciarCamara() {
    const video = document.getElementById('videoEscaner')
    const escaneoEstado = document.getElementById('escaneoEstado')
    
    if (!video || !escaneoEstado) return
    
    try {
        // Intentar usar la cámara trasera primero
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: { exact: "environment" } }
            })
        } catch (err) {
            // Si falla, usar cualquier cámara disponible
            stream = await navigator.mediaDevices.getUserMedia({ video: true })
        }
        
        video.srcObject = stream
        video.setAttribute('playsinline', true)
        video.play()
        
        escaneoEstado.textContent = '🔍 Buscando código QR...'
        escaneoEstado.style.color = '#333'
        
        // Iniciar el escaneo continuo
        escanearContinuamente()
        
    } catch (error) {
        console.error('Error al acceder a la cámara:', error)
        escaneoEstado.textContent = '❌ No se pudo acceder a la cámara'
        escaneoEstado.style.color = 'red'
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudo acceder a la cámara. Puedes usar la opción "Subir foto del QR".'
        })
    }
}

/* Escanea el video en busca de un código QR */
function escanearContinuamente() {
    const video = document.getElementById('videoEscaner');
    const canvas = document.getElementById('canvasEscaner');
    
    if (!stream || stream.active === false) return;
    if (escaneando) return;  // Ya está procesando un QR
    
    if (video && video.readyState === video.HAVE_ENOUGH_DATA) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const code = jsQR(imageData.data, canvas.width, canvas.height, {
            inversionAttempts: "dontInvert",
        });
        
        if (code) {
            // QR detectado - procesar inmediatamente
            procesarQR(code.data);
            return;
        }
    }
    
    animationId = requestAnimationFrame(escanearContinuamente);
}

/* Envía el contenido del QR al servidor para registrar asistencia */
async function procesarQR(contenido) {
    if (escaneando) return;  // Ya está procesando
    escaneando = true;
    
    console.log("📱 QR escaneado:", contenido);
    
    // Detener el escaneo inmediatamente
    if (animationId) cancelAnimationFrame(animationId);
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    
    // Cerrar el modal del escáner inmediatamente
    cerrarModalEscaner();
    
    // Mostrar loading
    Swal.fire({
        title: 'Procesando...',
        text: 'Verificando tu asistencia',
        allowOutsideClick: false,
        didOpen: () => Swal.showLoading()
    });
    
    try {
        const response = await fetch('/alumno/escanear_qr_rotativo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ contenido_qr: contenido })
        });
        
        const resultado = await response.json();
        
        if (resultado.status === 'ok') {
            Swal.fire({
                icon: 'success',
                title: '✅ ¡Asistencia registrada!',
                text: resultado.message,
                timer: 2500,
                showConfirmButton: false
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: resultado.message || 'No se pudo registrar la asistencia',
                confirmButtonColor: '#b30000'
            });
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error de conexión',
            text: 'No se pudo conectar con el servidor',
            confirmButtonColor: '#b30000'
        });
    }
    
    escaneando = false;
}

/* Reinicia el escáner después de un error */
function reiniciarEscaner() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop())
        stream = null
    }
    escaneando = false;
    const escaneoEstado = document.getElementById('escaneoEstado')
    if (escaneoEstado) {
        escaneoEstado.textContent = '📱 Alinea el QR del tutor en la cámara'
        escaneoEstado.style.color = '#333'
    }
    iniciarCamara()
}

/* Cierra el modal del escáner y libera recursos */
function cerrarModalEscaner() {
    if (animationId) cancelAnimationFrame(animationId)
    if (stream) {
        stream.getTracks().forEach(track => track.stop())
        stream = null
    }
    if (modalEscaner) {
        modalEscaner.style.display = 'none'
    }
}

/* Lee un QR desde una imagen subida (alternativa a la cámara) */
async function leerQRDesdeArchivo(file) {
    if (escaneando) return;
    escaneando = true;
    
    Swal.fire({
        title: '📡 Procesando imagen...',
        text: 'Leyendo código QR',
        allowOutsideClick: false,
        didOpen: () => Swal.showLoading()
    })
    
    const canvas = document.getElementById('canvasEscaner')
    const img = new Image()
    const reader = new FileReader()
    
    reader.onload = async (e) => {
        img.src = e.target.result
        img.onload = async () => {
            canvas.width = img.width
            canvas.height = img.height
            const ctx = canvas.getContext('2d')
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
            
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
            const code = jsQR(imageData.data, canvas.width, canvas.height)
            
            if (code) {
                Swal.close();
                cerrarModalEscaner();
                
                const response = await fetch('/alumno/escanear_qr_rotativo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ contenido_qr: code.data })
                })
                
                const resultado = await response.json()
                
                if (resultado.status === 'ok') {
                    Swal.fire({
                        icon: 'success',
                        title: '✅ ¡Asistencia registrada!',
                        text: resultado.message,
                        timer: 2500,
                        showConfirmButton: false
                    })
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: resultado.message || 'No se pudo registrar la asistencia',
                        confirmButtonColor: '#b30000'
                    })
                }
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'No se pudo leer el código QR en la imagen',
                    confirmButtonColor: '#b30000'
                })
            }
            escaneando = false;
        }
    }
    reader.readAsDataURL(file)
}

/* Configura los eventos del modal de escáner (se ejecuta al cargar la página) */
function configurarEventosEscaner() {
    const btnSubirFotoQR = document.getElementById('btnSubirFotoQR')
    const btnCancelarEscaner = document.getElementById('btnCancelarEscaner')
    const cerrarEscaner = document.getElementById('cerrarEscaner')
    const inputFotoQR = document.getElementById('inputFotoQR')
    
    if (btnSubirFotoQR) {
        btnSubirFotoQR.onclick = () => {
            if (inputFotoQR) inputFotoQR.click()
        }
    }
    
    if (btnCancelarEscaner) {
        btnCancelarEscaner.onclick = cerrarModalEscaner
    }
    
    if (cerrarEscaner) {
        cerrarEscaner.onclick = cerrarModalEscaner
    }
    
    if (inputFotoQR) {
        inputFotoQR.onchange = (e) => {
            if (e.target.files && e.target.files[0]) {
                leerQRDesdeArchivo(e.target.files[0])
            }
        }
    }
    
    // Cerrar al hacer clic fuera del modal
    if (modalEscaner) {
        modalEscaner.onclick = (e) => {
            if (e.target === modalEscaner) cerrarModalEscaner()
        }
    }
}

// =====================================================
// MODAL PARA MODIFICAR USUARIO
// =====================================================

const modalModificar = document.getElementById('modalModificar')
const btnAbrirModificar = document.getElementById('btnAbrirModificar')
const cerrarModificar = document.getElementById('cerrarModificar')
const cancelarModificar = document.getElementById('cancelarModificar')

function abrirModalModificar() {
    if (modalModificar) {
        modalModificar.classList.add('activo')
        // Limpiar campos de contraseña al abrir
        const nuevaPass = document.getElementById('nueva_password')
        const confirmPass = document.getElementById('confirmar_password')
        if (nuevaPass) nuevaPass.value = ''
        if (confirmPass) confirmPass.value = ''
    }
}

function cerrarModalModificar() {
    if (modalModificar) {
        modalModificar.classList.remove('activo')
    }
}

// Event listeners para el modal de modificar usuario
if (btnAbrirModificar) {
    btnAbrirModificar.addEventListener('click', abrirModalModificar)
}

if (cerrarModificar) {
    cerrarModificar.addEventListener('click', cerrarModalModificar)
}

if (cancelarModificar) {
    cancelarModificar.addEventListener('click', cerrarModalModificar)
}

if (modalModificar) {
    modalModificar.addEventListener('click', (e) => {
        if (e.target === modalModificar) {
            cerrarModalModificar()
        }
    })
}

// =====================================================
// INICIALIZACIÓN
// =====================================================

/* Espera a que el DOM esté completamente cargado */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        modalEscaner = document.getElementById('modalEscaner')
        configurarEventosEscaner()
        inicializarBotonesEscaner()
    })
} else {
    modalEscaner = document.getElementById('modalEscaner')
    configurarEventosEscaner()
    inicializarBotonesEscaner()
}