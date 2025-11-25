// app/static/js/tutor/pago_exitoso.js

document.addEventListener('DOMContentLoaded', function () {
    // Inicializar animaciones AOS si la librería está cargada
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            once: true,
            offset: 50
        });
    }

    // Auto-descarga opcional después de 2 segundos (descomentar si se desea)
    /*
    setTimeout(function() {
        if (typeof downloadReceipt === 'function') {
            // downloadReceipt(); // Esto iniciaría la descarga automática
        }
    }, 2000);
    */
});