/*!
    * Start Bootstrap - SB Admin v7.0.7 (https://startbootstrap.com/template/sb-admin)
    * Copyright 2013-2023 Start Bootstrap
    * Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-sb-admin/blob/master/LICENSE)
    */
// 
// Scripts
// 

window.addEventListener('DOMContentLoaded', event => {

    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        // Uncomment Below to persist sidebar toggle between refreshes
        // if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
        //     document.body.classList.toggle('sb-sidenav-toggled');
        // }
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }

    // Mobile responsive sidebar enhancements
    const layoutSidenav = document.getElementById('layoutSidenav_nav');
    const layoutContent = document.getElementById('layoutSidenav_content');

    // Crear overlay para móviles
    const overlay = document.createElement('div');
    overlay.classList.add('sidebar-overlay');
    overlay.style.display = 'none';
    document.body.appendChild(overlay);

    // Función para cerrar el sidebar
    function closeSidebar() {
        document.body.classList.remove('sb-sidenav-toggled');
        overlay.style.display = 'none';
        localStorage.setItem('sb|sidebar-toggle', 'false');
    }

    // Función para abrir el sidebar
    function openSidebar() {
        document.body.classList.add('sb-sidenav-toggled');
        if (window.innerWidth < 992) {
            overlay.style.display = 'block';
        }
        localStorage.setItem('sb|sidebar-toggle', 'true');
    }

    // Click en overlay cierra el sidebar
    overlay.addEventListener('click', closeSidebar);

    // Detectar si estamos en móvil
    function isMobile() {
        return window.innerWidth < 992;
    }

    // Cerrar sidebar en móvil al hacer clic en un enlace
    if (layoutSidenav) {
        const sidebarLinks = layoutSidenav.querySelectorAll('.nav-link');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (isMobile() && document.body.classList.contains('sb-sidenav-toggled')) {
                    closeSidebar();
                }
            });
        });
    }

    // Manejar cambios de tamaño de ventana
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            // En desktop, remover overlay
            if (!isMobile()) {
                overlay.style.display = 'none';
            } else if (document.body.classList.contains('sb-sidenav-toggled')) {
                overlay.style.display = 'block';
            }
        }, 250);
    });

    // Soporte para gestos de deslizamiento (swipe) en móvil
    let touchStartX = 0;
    let touchEndX = 0;

    document.addEventListener('touchstart', e => {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    document.addEventListener('touchend', e => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, { passive: true });

    function handleSwipe() {
        if (!isMobile()) return;

        const swipeThreshold = 50;
        const swipeDistance = touchEndX - touchStartX;

        // Swipe right para abrir (solo si comenzó desde el borde izquierdo)
        if (swipeDistance > swipeThreshold && touchStartX < 50) {
            openSidebar();
        }

        // Swipe left para cerrar
        if (swipeDistance < -swipeThreshold && document.body.classList.contains('sb-sidenav-toggled')) {
            closeSidebar();
        }
    }

});
