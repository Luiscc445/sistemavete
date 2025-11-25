// JavaScript para pagar_cita.html con soporte de facturación boliviana
// Sistema de pagos con validaciones completas

document.addEventListener('DOMContentLoaded', function () {
    // Initialize Modals
    const modalCard = new bootstrap.Modal(document.getElementById('modalCard'));
    const modalQR = new bootstrap.Modal(document.getElementById('modalQR'));
    const modalFactura = new bootstrap.Modal(document.getElementById('modalFactura'));
    const modalConfirmacion = new bootstrap.Modal(document.getElementById('modalConfirmacion'));
    const loadingOverlay = document.getElementById('loadingOverlay');

    // Store selected payment method
    let selectedPaymentMethod = null;
    let requiereFactura = false;
    let facturaData = {};

    // Payment method selection
    document.querySelectorAll('.payment-method-card').forEach(card => {
        card.addEventListener('click', function () {
            const radio = this.querySelector('input[type="radio"]');
            radio.checked = true;
            selectedPaymentMethod = radio.value;
        });
    });

    // Factura tipo selector
    document.querySelectorAll('.factura-tipo-option').forEach(option => {
        option.addEventListener('click', function () {
            document.querySelectorAll('.factura-tipo-option').forEach(o => o.classList.remove('active'));
            this.classList.add('active');
            
            const tipo = this.dataset.tipo;
            const complementoRow = document.getElementById('complementoRow');
            const nitGroup = document.getElementById('nitGroup');
            const razonSocialGroup = document.getElementById('razonSocialGroup');
            const nitInput = document.getElementById('nit_cliente');
            const razonInput = document.getElementById('razon_social');

            // Reset and configure fields based on type
            nitInput.classList.remove('is-invalid');
            razonInput.classList.remove('is-invalid');

            if (tipo === 'ci') {
                complementoRow.style.display = 'flex';
                nitInput.placeholder = 'Ej: 12345678';
                nitInput.setAttribute('maxlength', '10');
                razonInput.placeholder = 'Nombre completo del titular';
                document.querySelector('#nitGroup .form-label-modern').innerHTML = 
                    '<i class="bi bi-person-vcard me-2"></i>Cédula de Identidad<span class="required-asterisk">*</span>';
            } else if (tipo === 'sin') {
                complementoRow.style.display = 'none';
                nitInput.value = '0';
                razonInput.value = 'S/N';
                nitInput.disabled = true;
                razonInput.disabled = true;
            } else {
                // NIT
                complementoRow.style.display = 'none';
                nitInput.placeholder = 'Ej: 1234567890';
                nitInput.setAttribute('maxlength', '15');
                razonInput.placeholder = 'Ej: EMPRESA EJEMPLO S.R.L.';
                nitInput.disabled = false;
                razonInput.disabled = false;
                document.querySelector('#nitGroup .form-label-modern').innerHTML = 
                    '<i class="bi bi-hash me-2"></i>NIT / Número de Documento<span class="required-asterisk">*</span>';
            }
        });
    });

    // Handle payment process - Show factura modal first
    window.handlePaymentProcess = function () {
        const selected = document.querySelector('input[name="metodo_pago"]:checked');
        if (!selected) {
            showNotification('Por favor selecciona un método de pago', 'warning');
            return;
        }

        selectedPaymentMethod = selected.value;
        
        // Show factura modal
        modalFactura.show();
    };

    // Continue without invoice
    window.continuarSinFactura = function () {
        requiereFactura = false;
        facturaData = {};
        
        document.getElementById('hidden_requiere_factura').value = '0';
        document.getElementById('hidden_nit').value = '';
        document.getElementById('hidden_razon_social').value = '';
        
        modalFactura.hide();
        showPaymentModal();
    };

    // Confirm invoice and pay
    window.confirmarFacturaYPagar = function () {
        // Validate invoice fields
        const tipoDoc = document.querySelector('input[name="tipo_documento"]:checked').value;
        const nit = document.getElementById('nit_cliente').value.trim();
        const razonSocial = document.getElementById('razon_social').value.trim();
        const email = document.getElementById('email_factura').value.trim();

        let isValid = true;

        if (tipoDoc !== 'sin_nit') {
            // Validate NIT
            if (!nit || !validateNIT(nit, tipoDoc)) {
                document.getElementById('nit_cliente').classList.add('is-invalid');
                document.getElementById('nitError').textContent = 
                    tipoDoc === 'ci' ? 'Ingresa un número de CI válido (solo números)' : 'Ingresa un NIT válido (solo números)';
                isValid = false;
            } else {
                document.getElementById('nit_cliente').classList.remove('is-invalid');
            }

            // Validate Razón Social
            if (!razonSocial || razonSocial.length < 3) {
                document.getElementById('razon_social').classList.add('is-invalid');
                document.getElementById('razonSocialError').textContent = 'Ingresa el nombre o razón social (mínimo 3 caracteres)';
                isValid = false;
            } else if (!validateName(razonSocial)) {
                document.getElementById('razon_social').classList.add('is-invalid');
                document.getElementById('razonSocialError').textContent = 'El nombre no puede contener números';
                isValid = false;
            } else {
                document.getElementById('razon_social').classList.remove('is-invalid');
            }
        }

        // Validate email if provided
        if (email && !validateEmail(email)) {
            showNotification('Por favor ingresa un correo electrónico válido', 'warning');
            return;
        }

        if (!isValid) {
            showNotification('Por favor completa correctamente los campos de facturación', 'error');
            return;
        }

        // Store invoice data
        requiereFactura = true;
        facturaData = {
            tipo_documento: tipoDoc,
            nit: tipoDoc === 'sin_nit' ? '0' : nit,
            razon_social: tipoDoc === 'sin_nit' ? 'S/N' : razonSocial.toUpperCase(),
            email: email,
            complemento: document.getElementById('complemento_ci').value || '',
            expedido_en: document.getElementById('expedido_en').value || ''
        };

        // Set hidden fields
        document.getElementById('hidden_requiere_factura').value = '1';
        document.getElementById('hidden_nit').value = facturaData.nit;
        document.getElementById('hidden_razon_social').value = facturaData.razon_social;
        document.getElementById('hidden_email_factura').value = facturaData.email;
        document.getElementById('hidden_tipo_documento').value = facturaData.tipo_documento;

        modalFactura.hide();
        showPaymentModal();
    };

    // Show appropriate payment modal
    function showPaymentModal() {
        const metodosLabel = {
            'tarjeta_credito': 'Tarjeta de Crédito/Débito',
            'qr_bancario': 'Código QR Bancario',
            'efectivo': 'Efectivo en Consultorio'
        };

        // Update confirmation modal
        document.getElementById('confirmMetodoPago').textContent = metodosLabel[selectedPaymentMethod] || selectedPaymentMethod;
        
        if (requiereFactura && facturaData.razon_social) {
            document.getElementById('confirmFacturaRow').style.display = 'flex';
            document.getElementById('confirmFacturaNombre').textContent = facturaData.razon_social;
        } else {
            document.getElementById('confirmFacturaRow').style.display = 'none';
        }

        if (selectedPaymentMethod === 'tarjeta_credito') {
            modalCard.show();
        } else if (selectedPaymentMethod === 'qr_bancario') {
            modalQR.show();
        } else {
            // Cash payment - show confirmation
            document.getElementById('confirmacionMensaje').textContent = 
                'El pago se realizará en efectivo al momento de tu cita. ¿Confirmas la reserva?';
            modalConfirmacion.show();
        }
    }

    // Process final payment
    window.procesarPagoFinal = function() {
        modalConfirmacion.hide();
        showLoading();
        
        setTimeout(() => {
            document.getElementById('pagoForm').submit();
        }, 1500);
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

    // Live card updates with validation
    numberInput.addEventListener('input', (e) => {
        let val = e.target.value.replace(/\D/g, '').substring(0, 16);
        let formatted = val.match(/.{1,4}/g)?.join(' ') || '';
        e.target.value = formatted;

        if (formatted) {
            displayNumber.textContent = formatted;
        } else {
            displayNumber.textContent = '#### #### #### ####';
        }
    });

    nameInput.addEventListener('input', (e) => {
        // Only allow letters and spaces
        let val = e.target.value.replace(/[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ\s]/g, '');
        e.target.value = val.toUpperCase();
        displayName.textContent = val.toUpperCase() || 'NOMBRE APELLIDO';
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
        let val = e.target.value.replace(/\D/g, '').substring(0, 4);
        e.target.value = val;
        displayCvv.textContent = val ? '•'.repeat(val.length) : '•••';
    });

    // Process card payment with validation
    window.processCardPayment = function () {
        const number = numberInput.value.replace(/\s/g, '');
        const name = nameInput.value;
        const expiry = expiryInput.value;
        const cvv = cvvInput.value;

        // Card number validation
        if (!number || number.length < 13 || !luhnCheck(number)) {
            showNotification('Ingresa un número de tarjeta válido', 'error');
            numberInput.focus();
            return;
        }

        // Name validation - no numbers allowed
        if (!name || name.length < 3) {
            showNotification('Ingresa el nombre del titular', 'error');
            nameInput.focus();
            return;
        }

        if (!validateName(name)) {
            showNotification('El nombre no puede contener números', 'error');
            nameInput.focus();
            return;
        }

        // Expiry validation
        if (!expiry || expiry.length !== 5) {
            showNotification('Ingresa una fecha de vencimiento válida', 'error');
            expiryInput.focus();
            return;
        }

        // Validate expiry date is in the future
        const [month, year] = expiry.split('/');
        const expiryDate = new Date(2000 + parseInt(year), parseInt(month) - 1);
        if (expiryDate < new Date()) {
            showNotification('La tarjeta está vencida', 'error');
            expiryInput.focus();
            return;
        }

        // CVV validation
        if (!cvv || cvv.length < 3) {
            showNotification('Ingresa el CVV', 'error');
            cvvInput.focus();
            return;
        }

        modalCard.hide();
        showLoading();
        animateLoadingSteps();

        setTimeout(() => {
            document.getElementById('pagoForm').submit();
        }, 3000);
    };

    // Process QR payment
    window.processQRPayment = function () {
        modalQR.hide();
        showLoading();
        animateLoadingSteps();

        setTimeout(() => {
            document.getElementById('pagoForm').submit();
        }, 2500);
    };

    // Animate loading steps
    function animateLoadingSteps() {
        const steps = ['step1', 'step2', 'step3'];
        let currentStep = 0;

        function activateStep() {
            if (currentStep > 0) {
                const prevStep = document.getElementById(steps[currentStep - 1]);
                prevStep.classList.remove('active');
                prevStep.classList.add('completed');
                prevStep.querySelector('i').className = 'bi bi-check-circle-fill';
            }

            if (currentStep < steps.length) {
                const step = document.getElementById(steps[currentStep]);
                step.classList.add('active');
                step.querySelector('i').className = 'bi bi-arrow-right-circle-fill';
                currentStep++;
                setTimeout(activateStep, 800);
            }
        }

        activateStep();
    }

    // Show loading
    function showLoading() {
        loadingOverlay.classList.add('active');
    }

    // Validation helpers
    function validateNIT(nit, tipo) {
        if (tipo === 'ci') {
            return /^\d{5,10}$/.test(nit);
        }
        return /^\d{7,15}$/.test(nit);
    }

    function validateName(name) {
        // Name should not contain numbers
        return !/\d/.test(name);
    }

    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    // Luhn algorithm for card validation
    function luhnCheck(num) {
        let arr = (num + '')
            .split('')
            .reverse()
            .map(x => parseInt(x));
        let lastDigit = arr.shift();
        let sum = arr.reduce((acc, val, i) => {
            if (i % 2 === 0) {
                val *= 2;
                if (val > 9) val -= 9;
            }
            return acc + val;
        }, 0);
        sum += lastDigit;
        return sum % 10 === 0;
    }

    // Show notification
    function showNotification(message, type) {
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#0ea5e9'
        };

        const icons = {
            success: 'check-circle',
            error: 'x-circle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };

        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type] || colors.info};
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            z-index: 10000;
            animation: slideIn 0.3s ease;
            display: flex;
            align-items: center;
            gap: 12px;
            max-width: 400px;
        `;
        notification.innerHTML = `
            <i class="bi bi-${icons[type] || icons.info}-fill" style="font-size: 1.25rem;"></i>
            <span>${message}</span>
        `;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 4000);
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Real-time input validation
    document.getElementById('nit_cliente')?.addEventListener('input', function(e) {
        // Only allow numbers
        e.target.value = e.target.value.replace(/\D/g, '');
    });

    document.getElementById('razon_social')?.addEventListener('input', function(e) {
        // Allow letters, spaces, dots, and special characters but no numbers for personal names
        // For business names (NIT), numbers might be in the name like "S.R.L."
        this.classList.remove('is-invalid');
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
