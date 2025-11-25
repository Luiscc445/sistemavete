// JavaScript extraido de perfil.html
// Generado automaticamente el 2025-11-22 22:25:48

AOS.init({
    duration: 800,
    once: true,
    offset: 50
});

// Cargar imágenes guardadas al iniciar
window.addEventListener('load', function () {
    loadSavedImages();
});

// Función para comprimir imagen antes de guardar
function compressImage(file, maxWidth = 1920, quality = 0.85) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = (event) => {
            const img = new Image();
            img.src = event.target.result;
            img.onload = () => {
                const canvas = document.createElement('canvas');
                let width = img.width;
                let height = img.height;

                // Redimensionar si es necesario
                if (width > maxWidth) {
                    height = (height * maxWidth) / width;
                    width = maxWidth;
                }

                canvas.width = width;
                canvas.height = height;

                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);

                // Convertir a base64 con compresión
                canvas.toBlob(
                    (blob) => {
                        const reader = new FileReader();
                        reader.readAsDataURL(blob);
                        reader.onloadend = () => resolve(reader.result);
                        reader.onerror = reject;
                    },
                    'image/jpeg',
                    quality
                );
            };
            img.onerror = reject;
        };
        reader.onerror = reject;
    });
}

// Guardar imagen en localStorage con manejo de errores
function saveImageToStorage(key, imageData) {
    try {
        localStorage.setItem(key, imageData);
        return true;
    } catch (e) {
        console.error('Error guardando en localStorage:', e);

        // Si falla, intentar limpiar espacio y reintentar
        if (e.name === 'QuotaExceededError') {
            console.log('Limpiando espacio en localStorage...');

            // Limpiar solo imágenes antiguas si existen
            const keysToClean = ['temp_uploads', 'old_images', 'cache_'];
            for (let i = 0; i < localStorage.length; i++) {
                const storageKey = localStorage.key(i);
                if (keysToClean.some(prefix => storageKey && storageKey.startsWith(prefix))) {
                    localStorage.removeItem(storageKey);
                }
            }

            // Reintentar
            try {
                localStorage.setItem(key, imageData);
                return true;
            } catch (retryError) {
                console.error('Error en reintento:', retryError);
                showToast('Advertencia', 'La imagen es muy grande. Se mostrará pero no se guardará permanentemente.', 'warning');
                return false;
            }
        }
        return false;
    }
}

// Cargar imágenes desde localStorage
function loadSavedImages() {
    try {
        // Cargar avatar
        const savedAvatar = localStorage.getItem('rambopet_profile_avatar');
        if (savedAvatar) {
            const avatar = document.getElementById('profileAvatar');
            avatar.src = savedAvatar;
            document.getElementById('avatarData').value = savedAvatar;
        }

        // Cargar portada
        const savedCover = localStorage.getItem('rambopet_profile_cover');
        if (savedCover) {
            const coverPhoto = document.getElementById('coverPhoto');
            coverPhoto.style.backgroundImage = `url(${savedCover})`;
            coverPhoto.style.backgroundSize = 'cover';
            coverPhoto.style.backgroundPosition = 'center';
            coverPhoto.style.backgroundRepeat = 'no-repeat';

            // Ocultar gradient y pattern
            const gradient = coverPhoto.querySelector('.cover-gradient');
            const pattern = coverPhoto.querySelector('.cover-pattern');
            if (gradient) gradient.style.opacity = '0';
            if (pattern) pattern.style.opacity = '0';

            document.getElementById('coverData').value = savedCover;
        }
    } catch (error) {
        console.error('Error cargando imágenes:', error);
    }
}

// Variables globales
let avatarFile = null;
let coverFile = null;
let currentZoom = 1;
let currentPhotoSrc = '';

// View Avatar Photo
function viewAvatarPhoto() {
    const avatar = document.getElementById('profileAvatar');
    const viewer = document.getElementById('photoViewer');
    const viewerImage = document.getElementById('viewerImage');
    const photoType = document.getElementById('viewerPhotoType');

    currentPhotoSrc = avatar.src;
    viewerImage.src = currentPhotoSrc;
    photoType.textContent = 'Foto de perfil';
    viewer.classList.add('active');
    currentZoom = 1;
    updateZoom();

    document.body.style.overflow = 'hidden';
}

// View Cover Photo
function viewCoverPhoto() {
    const cover = document.getElementById('coverPhoto');
    const viewer = document.getElementById('photoViewer');
    const viewerImage = document.getElementById('viewerImage');
    const photoType = document.getElementById('viewerPhotoType');

    // Get background image or use gradient
    const bgImage = cover.style.backgroundImage;
    if (bgImage && bgImage !== 'none') {
        currentPhotoSrc = bgImage.slice(5, -2); // Remove url(" and ")
        viewerImage.src = currentPhotoSrc;
        photoType.textContent = 'Foto de portada';
        viewer.classList.add('active');
        currentZoom = 1;
        updateZoom();

        document.body.style.overflow = 'hidden';
    }
}

// Close Photo Viewer
function closePhotoViewer(event) {
    if (event && event.target !== event.currentTarget) return;

    const viewer = document.getElementById('photoViewer');
    viewer.classList.remove('active');
    document.body.style.overflow = '';
    currentZoom = 1;
}

// Zoom In
function zoomIn() {
    if (currentZoom < 3) {
        currentZoom += 0.25;
        updateZoom();
    }
}

// Zoom Out
function zoomOut() {
    if (currentZoom > 0.5) {
        currentZoom -= 0.25;
        updateZoom();
    }
}

// Update Zoom
function updateZoom() {
    const viewerImage = document.getElementById('viewerImage');
    const zoomLevel = document.getElementById('zoomLevel');

    viewerImage.style.transform = `scale(${currentZoom})`;
    zoomLevel.textContent = Math.round(currentZoom * 100) + '%';
}

// Download Photo
function downloadPhoto() {
    const link = document.createElement('a');
    link.href = currentPhotoSrc;
    link.download = 'foto_perfil_rambopet_' + Date.now() + '.jpg';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast('¡Descargado!', 'La foto se ha descargado correctamente', 'success');
}

// Keyboard shortcuts
document.addEventListener('keydown', function (e) {
    const viewer = document.getElementById('photoViewer');
    if (!viewer.classList.contains('active')) return;

    if (e.key === 'Escape') {
        closePhotoViewer();
    } else if (e.key === '+' || e.key === '=') {
        zoomIn();
    } else if (e.key === '-') {
        zoomOut();
    }
});

// Preview Avatar con compresión
async function previewAvatar(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validar tipo de archivo
    if (!file.type.startsWith('image/')) {
        showToast('Error', 'Por favor selecciona una imagen válida', 'error');
        return;
    }

    // Validar tamaño (máximo 10MB antes de compresión)
    if (file.size > 10 * 1024 * 1024) {
        showToast('Error', 'La imagen no debe superar 10MB', 'error');
        return;
    }

    try {
        // Comprimir imagen
        const compressedImage = await compressImage(file, 800, 0.85);

        const img = document.getElementById('profileAvatar');
        img.src = compressedImage;
        avatarFile = file;

        // Guardar en hidden input
        document.getElementById('avatarData').value = compressedImage;

        // Guardar en localStorage con clave única
        const saved = saveImageToStorage('rambopet_profile_avatar', compressedImage);

        if (saved) {
            showToast('¡Perfecto!', 'Foto de perfil actualizada y guardada correctamente', 'success');
        } else {
            showToast('Actualizado', 'Foto de perfil actualizada (temporal)', 'warning');
        }
    } catch (error) {
        console.error('Error procesando imagen:', error);
        showToast('Error', 'No se pudo procesar la imagen', 'error');
    }
}

// Preview Cover con compresión
async function previewCover(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validar tipo de archivo
    if (!file.type.startsWith('image/')) {
        showToast('Error', 'Por favor selecciona una imagen válida', 'error');
        return;
    }

    // Validar tamaño (máximo 10MB antes de compresión)
    if (file.size > 10 * 1024 * 1024) {
        showToast('Error', 'La imagen no debe superar 10MB', 'error');
        return;
    }

    try {
        // Comprimir imagen
        const compressedImage = await compressImage(file, 1920, 0.85);

        const coverPhoto = document.getElementById('coverPhoto');

        // Aplicar imagen como background
        coverPhoto.style.backgroundImage = `url(${compressedImage})`;
        coverPhoto.style.backgroundSize = 'cover';
        coverPhoto.style.backgroundPosition = 'center';
        coverPhoto.style.backgroundRepeat = 'no-repeat';

        coverFile = file;

        // Guardar en hidden input
        document.getElementById('coverData').value = compressedImage;

        // Ocultar gradient y pattern para ver mejor la imagen
        const gradient = coverPhoto.querySelector('.cover-gradient');
        const pattern = coverPhoto.querySelector('.cover-pattern');
        if (gradient) gradient.style.opacity = '0';
        if (pattern) pattern.style.opacity = '0';

        // Guardar en localStorage con clave única
        const saved = saveImageToStorage('rambopet_profile_cover', compressedImage);

        if (saved) {
            showToast('¡Perfecto!', 'Foto de portada actualizada y guardada correctamente', 'success');
        } else {
            showToast('Actualizado', 'Foto de portada actualizada (temporal)', 'warning');
        }
    } catch (error) {
        console.error('Error procesando imagen:', error);
        showToast('Error', 'No se pudo procesar la imagen', 'error');
    }
}

// Upload con simulación de progreso
function simulateUpload(callback) {
    const overlay = document.getElementById('uploadOverlay');
    const progressBar = document.getElementById('uploadProgressBar');

    overlay.classList.add('active');
    let progress = 0;

    const interval = setInterval(() => {
        progress += Math.random() * 30;
        if (progress > 100) progress = 100;

        progressBar.style.width = progress + '%';

        if (progress >= 100) {
            clearInterval(interval);
            setTimeout(() => {
                overlay.classList.remove('active');
                if (callback) callback();
            }, 500);
        }
    }, 200);
}

// Show Toast Notification
function showToast(title, message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;

    let icon, iconColor;
    if (type === 'success') {
        icon = 'bi-check-circle-fill';
        iconColor = 'var(--success)';
    } else if (type === 'warning') {
        icon = 'bi-exclamation-triangle-fill';
        iconColor = 'var(--warning)';
    } else {
        icon = 'bi-x-circle-fill';
        iconColor = 'var(--danger)';
    }

    toast.innerHTML = `
        <i class="bi ${icon}" style="color: ${iconColor}"></i>
        <div class="toast-content">
            <h4>${title}</h4>
            <p>${message}</p>
        </div>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Handle form submission
document.querySelector('.profile-form').addEventListener('submit', function (e) {
    e.preventDefault();

    simulateUpload(() => {
        showToast('¡Éxito!', 'Perfil actualizado correctamente', 'success');
        // Aquí enviarías el formulario al servidor
        this.submit();
    });
});

// Password Modal Functions
function openPasswordModal() {
    const modal = document.getElementById('passwordModal');
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closePasswordModal() {
    const modal = document.getElementById('passwordModal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

// Confirm Delete Account
function confirmDeleteAccount() {
    if (confirm('⚠️ ADVERTENCIA\n\n¿Estás seguro de que deseas eliminar tu cuenta?\n\nEsta acción es permanente e irreversible. Se eliminarán:\n\n• Todos tus datos personales\n• Información de tus mascotas\n• Historial de citas\n• Archivos adjuntos\n\n¿Deseas continuar?')) {
        if (confirm('⚠️ ÚLTIMA CONFIRMACIÓN\n\nPor favor confirma una vez más que deseas eliminar permanentemente tu cuenta.\n\n¿Estás absolutamente seguro?')) {
            // Aquí iría la lógica para eliminar la cuenta
            showToast('Procesando', 'Eliminando cuenta...', 'warning');

            setTimeout(() => {
                showToast('Cuenta Eliminada', 'Tu cuenta ha sido eliminada exitosamente', 'success');
                // Redirigir al logout o página de inicio
                // window.location.href = '/logout';
            }, 2000);
        }
    }
}

// Close modal on Escape key
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        const passwordModal = document.getElementById('passwordModal');
        if (passwordModal.classList.contains('active')) {
            closePasswordModal();
        }
    }
});

// Toggle Password Visibility
window.togglePassword = function (button) {
    const input = button.previousElementSibling;
    const icon = button.querySelector('i');

    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('bi-eye');
        icon.classList.add('bi-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('bi-eye-slash');
        icon.classList.add('bi-eye');
    }
};

// Animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);