// JavaScript extraido de pagar_cita.html
// Generado automaticamente el 2025-11-22 22:25:48

document.addEventListener('DOMContentLoaded', function () {
        // Initialize Modals
        const modalCard = new bootstrap.Modal(document.getElementById('modalCard'));
        const modalQR = new bootstrap.Modal(document.getElementById('modalQR'));
        const loadingOverlay = document.getElementById('loadingOverlay');

        // Payment method selection
        document.querySelectorAll('.payment-method-card').forEach(card => {
            card.addEventListener('click', function () {
                const radio = this.querySelector('input[type="radio"]');
                radio.checked = true;
            });
        });

        // Handle payment process
        window.handlePaymentProcess = function () {
            const selected = document.querySelector('input[name="metodo_pago"]:checked');
            if (!selected) {
                showNotification('Por favor selecciona un método de pago', 'warning');
                return;
            }

            if (selected.value === 'tarjeta_credito') {
                modalCard.show();
            } else if (selected.value === 'qr_bancario') {
                modalQR.show();
            } else {
                if (confirm('¿Confirmar pago en efectivo al asistir a la cita?')) {
                    showLoading();
                    setTimeout(() => {
                        document.getElementById('pagoForm').submit();
                    }, 1000);
                }
            }
        };

        // Card interactions
        const card3d = document.getElementById('card3d');
        const cvvInput = document.getElementById('cvv');
        const numberInput = document.getElementById('numero_tarjeta');
        const nameInput = document.getElementById('nombre_tarjeta');
        const expiryInput = document.getElementById('fecha_vencimiento');

        const displayNumber = document.getElementById('displayNumber');
        const displayName = document.getElementById('displayName');
        const displayExpiry = document.getElementById('displayExpiry');
        const displayCvv = document.getElementById('displayCvv');

        // Flip card on CVV focus
        cvvInput.addEventListener('focus', () => {
            card3d.classList.add('flipped');
        });

        cvvInput.addEventListener('blur', () => {
            card3d.classList.remove('flipped');
        });

        // Live card updates
        numberInput.addEventListener('input', (e) => {
            let val = e.target.value.replace(/\D/g, '').substring(0, 16);
            let formatted = val.match(/.{1,4}/g)?.join(' ') || '';
            e.target.value = formatted;

            // Update display - simple text format
            if (formatted) {
                displayNumber.textContent = formatted;
            } else {
                displayNumber.textContent = '#### #### #### ####';
            }
        });

        nameInput.addEventListener('input', (e) => {
            const val = e.target.value.toUpperCase();
            displayName.textContent = val || 'NOMBRE APELLIDO';
        });

        expiryInput.addEventListener('input', (e) => {
            let val = e.target.value.replace(/\D/g, '').substring(0, 4);
            if (val.length >= 2) {
                val = val.substring(0, 2) + '/' + val.substring(2);
            }
            e.target.value = val;
            displayExpiry.textContent = val || 'MM/AA';
        });

        cvvInput.addEventListener('input', (e) => {
            const val = e.target.value.substring(0, 4);
            displayCvv.textContent = val ? '•'.repeat(val.length) : '•••';
        });

        // Process card payment
        window.processCardPayment = function () {
            const number = numberInput.value.replace(/\s/g, '');
            const name = nameInput.value;
            const expiry = expiryInput.value;
            const cvv = cvvInput.value;

            if (!number || number.length < 13) {
                showNotification('Ingresa un número de tarjeta válido', 'error');
                numberInput.focus();
                return;
            }

            if (!name || name.length < 3) {
                showNotification('Ingresa el nombre del titular', 'error');
                nameInput.focus();
                return;
            }

            if (!expiry || expiry.length !== 5) {
                showNotification('Ingresa una fecha de vencimiento válida', 'error');
                expiryInput.focus();
                return;
            }

            if (!cvv || cvv.length < 3) {
                showNotification('Ingresa el CVV', 'error');
                cvvInput.focus();
                return;
            }

            modalCard.hide();
            showLoading();

            setTimeout(() => {
                document.getElementById('pagoForm').submit();
            }, 2000);
        };

        // Process QR payment
        window.processQRPayment = function () {
            modalQR.hide();
            showLoading();

            setTimeout(() => {
                document.getElementById('pagoForm').submit();
            }, 1500);
        };

        // Show loading
        function showLoading() {
            loadingOverlay.classList.add('active');
        }

        // Show notification
        function showNotification(message, type) {
            const colors = {
                success: '#10b981',
                error: '#ef4444',
                warning: '#f59e0b'
            };

            const notification = document.createElement('div');
            notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type] || colors.success};
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
            notification.innerHTML = `
            <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'exclamation-circle'}-fill me-2"></i>
            ${message}
        `;
            document.body.appendChild(notification);

            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }

        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    });

    // Animation styles
    const style = document.createElement('style');
    style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
    document.head.appendChild(style);