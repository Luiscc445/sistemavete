/**
 * Sistema de Validaciones Globales - Veterinaria RamboPet
 * Validaciones en tiempo real para formularios
 */

(function() {
    'use strict';

    // Configuración de validaciones
    const ValidationConfig = {
        // Regex patterns
        patterns: {
            email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            phone: /^[67]\d{7}$/, // Bolivia: 8 dígitos empezando con 6 o 7
            phoneLandline: /^[234]\d{6,7}$/, // Bolivia: fijos
            onlyLetters: /^[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ\s]+$/,
            onlyNumbers: /^\d+$/,
            alphanumeric: /^[a-zA-Z0-9áéíóúüñÁÉÍÓÚÜÑ\s]+$/,
            nit: /^\d{7,15}$/,
            ci: /^\d{5,10}$/,
            password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{6,}$/
        },

        // Mensajes de error
        messages: {
            required: 'Este campo es obligatorio',
            email: 'Ingresa un correo electrónico válido',
            phone: 'Ingresa un número de celular válido (8 dígitos)',
            onlyLetters: 'Este campo solo puede contener letras',
            onlyNumbers: 'Este campo solo puede contener números',
            minLength: 'Debe tener al menos {min} caracteres',
            maxLength: 'No puede tener más de {max} caracteres',
            nit: 'Ingresa un NIT válido (7-15 dígitos)',
            ci: 'Ingresa un CI válido (5-10 dígitos)',
            password: 'La contraseña debe tener al menos 6 caracteres, una mayúscula, una minúscula y un número',
            passwordMatch: 'Las contraseñas no coinciden',
            futureDate: 'La fecha debe ser futura',
            pastDate: 'La fecha debe ser pasada o actual',
            noNumbers: 'Este campo no puede contener números'
        }
    };

    // Clase principal de validación
    class FormValidator {
        constructor(form, options = {}) {
            this.form = typeof form === 'string' ? document.querySelector(form) : form;
            this.options = {
                validateOnInput: true,
                validateOnBlur: true,
                showErrors: true,
                scrollToError: true,
                ...options
            };
            this.errors = {};

            if (this.form) {
                this.init();
            }
        }

        init() {
            // Add validation attributes to inputs
            this.form.querySelectorAll('[data-validate]').forEach(input => {
                this.setupInput(input);
            });

            // Form submit handler
            this.form.addEventListener('submit', (e) => {
                if (!this.validateForm()) {
                    e.preventDefault();
                    if (this.options.scrollToError) {
                        this.scrollToFirstError();
                    }
                }
            });
        }

        setupInput(input) {
            const rules = input.dataset.validate.split('|');

            if (this.options.validateOnInput) {
                input.addEventListener('input', () => this.validateInput(input, rules));
            }

            if (this.options.validateOnBlur) {
                input.addEventListener('blur', () => this.validateInput(input, rules));
            }

            // Auto-format inputs based on type
            this.setupAutoFormat(input, rules);
        }

        setupAutoFormat(input, rules) {
            // Only letters - remove numbers as user types
            if (rules.includes('onlyLetters') || rules.includes('noNumbers')) {
                input.addEventListener('input', (e) => {
                    const start = e.target.selectionStart;
                    const filtered = e.target.value.replace(/[0-9]/g, '');
                    if (filtered !== e.target.value) {
                        e.target.value = filtered;
                        // Maintain cursor position
                        const newPos = start - 1;
                        e.target.setSelectionRange(newPos >= 0 ? newPos : 0, newPos >= 0 ? newPos : 0);
                    }
                });
            }

            // Only numbers
            if (rules.includes('onlyNumbers') || rules.includes('nit') || rules.includes('ci')) {
                input.addEventListener('input', (e) => {
                    e.target.value = e.target.value.replace(/\D/g, '');
                });
            }

            // Phone formatting
            if (rules.includes('phone')) {
                input.addEventListener('input', (e) => {
                    let value = e.target.value.replace(/\D/g, '');
                    if (value.length > 8) value = value.substring(0, 8);
                    e.target.value = value;
                });
            }

            // Uppercase for names in some contexts
            if (rules.includes('uppercase')) {
                input.addEventListener('input', (e) => {
                    e.target.value = e.target.value.toUpperCase();
                });
            }

            // Capitalize first letter of each word
            if (rules.includes('capitalize')) {
                input.addEventListener('blur', (e) => {
                    e.target.value = e.target.value.toLowerCase()
                        .split(' ')
                        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                        .join(' ');
                });
            }
        }

        validateInput(input, rules) {
            const value = input.value.trim();
            const fieldName = input.name || input.id;
            let isValid = true;
            let errorMessage = '';

            for (const rule of rules) {
                const [ruleName, ruleValue] = rule.split(':');

                switch (ruleName) {
                    case 'required':
                        if (!value) {
                            isValid = false;
                            errorMessage = ValidationConfig.messages.required;
                        }
                        break;

                    case 'email':
                        if (value && !ValidationConfig.patterns.email.test(value)) {
                            isValid = false;
                            errorMessage = ValidationConfig.messages.email;
                        }
                        break;

                    case 'phone':
                        if (value && !ValidationConfig.patterns.phone.test(value)) {
                            isValid = false;
                            errorMessage = ValidationConfig.messages.phone;
                        }
                        break;

                    case 'onlyLetters':
                    case 'noNumbers':
                        if (value && !ValidationConfig.patterns.onlyLetters.test(value)) {
                            isValid = false;
                            errorMessage = ValidationConfig.messages.noNumbers;
                        }
                        break;

                    case 'onlyNumbers':
                        if (value && !ValidationConfig.patterns.onlyNumbers.test(value)) {
                            isValid = false;
                            errorMessage = ValidationConfig.messages.onlyNumbers;
                        }
                        break;

                    case 'nit':
                        if (value && !ValidationConfig.patterns.nit.test(value)) {
                            isValid = false;
                            errorMessage = ValidationConfig.messages.nit;
                        }
                        break;

                    case 'ci':
                        if (value && !ValidationConfig.patterns.ci.test(value)) {
                            isValid = false;
                            errorMessage = ValidationConfig.messages.ci;
                        }
                        break;

                    case 'minLength':
                        if (value && value.length < parseInt(ruleValue)) {
                            isValid = false;
                            errorMessage = ValidationConfig.messages.minLength.replace('{min}', ruleValue);
                        }
                        break;

                    case 'maxLength':
                        if (value && value.length > parseInt(ruleValue)) {
                            isValid = false;
                            errorMessage = ValidationConfig.messages.maxLength.replace('{max}', ruleValue);
                        }
                        break;

                    case 'password':
                        if (value && !ValidationConfig.patterns.password.test(value)) {
                            isValid = false;
                            errorMessage = ValidationConfig.messages.password;
                        }
                        break;

                    case 'match':
                        const matchInput = document.querySelector(`[name="${ruleValue}"]`) || 
                                          document.getElementById(ruleValue);
                        if (matchInput && value !== matchInput.value) {
                            isValid = false;
                            errorMessage = ValidationConfig.messages.passwordMatch;
                        }
                        break;

                    case 'futureDate':
                        if (value) {
                            const inputDate = new Date(value);
                            const today = new Date();
                            today.setHours(0, 0, 0, 0);
                            if (inputDate < today) {
                                isValid = false;
                                errorMessage = ValidationConfig.messages.futureDate;
                            }
                        }
                        break;

                    case 'pastDate':
                        if (value) {
                            const inputDate = new Date(value);
                            const today = new Date();
                            if (inputDate > today) {
                                isValid = false;
                                errorMessage = ValidationConfig.messages.pastDate;
                            }
                        }
                        break;
                }

                if (!isValid) break;
            }

            // Update error state
            if (this.options.showErrors) {
                this.updateErrorDisplay(input, isValid, errorMessage);
            }

            this.errors[fieldName] = isValid ? null : errorMessage;
            return isValid;
        }

        updateErrorDisplay(input, isValid, errorMessage) {
            // Remove existing error
            input.classList.remove('is-invalid', 'is-valid');
            
            // Find or create error element
            let errorEl = input.parentElement.querySelector('.validation-error');
            if (!errorEl) {
                errorEl = document.createElement('div');
                errorEl.className = 'validation-error';
                input.parentElement.appendChild(errorEl);
            }

            if (isValid) {
                input.classList.add('is-valid');
                errorEl.style.display = 'none';
                errorEl.textContent = '';
            } else {
                input.classList.add('is-invalid');
                errorEl.style.display = 'block';
                errorEl.textContent = errorMessage;
            }
        }

        validateForm() {
            let isValid = true;
            
            this.form.querySelectorAll('[data-validate]').forEach(input => {
                const rules = input.dataset.validate.split('|');
                if (!this.validateInput(input, rules)) {
                    isValid = false;
                }
            });

            return isValid;
        }

        scrollToFirstError() {
            const firstError = this.form.querySelector('.is-invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
        }

        reset() {
            this.errors = {};
            this.form.querySelectorAll('[data-validate]').forEach(input => {
                input.classList.remove('is-invalid', 'is-valid');
                const errorEl = input.parentElement.querySelector('.validation-error');
                if (errorEl) {
                    errorEl.style.display = 'none';
                }
            });
        }
    }

    // Real-time validation helpers
    const Validators = {
        // Prevent numbers in input
        noNumbers: function(input) {
            input.addEventListener('input', function(e) {
                const value = e.target.value;
                const filtered = value.replace(/[0-9]/g, '');
                if (filtered !== value) {
                    const start = e.target.selectionStart;
                    e.target.value = filtered;
                    const newPos = Math.max(0, start - (value.length - filtered.length));
                    e.target.setSelectionRange(newPos, newPos);
                    showInputFeedback(e.target, 'No se permiten números en este campo', 'warning');
                }
            });
        },

        // Only allow numbers
        onlyNumbers: function(input) {
            input.addEventListener('input', function(e) {
                e.target.value = e.target.value.replace(/\D/g, '');
            });
        },

        // Phone format (Bolivia)
        phone: function(input) {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length > 8) value = value.substring(0, 8);
                e.target.value = value;
            });
        },

        // Email validation
        email: function(input) {
            input.addEventListener('blur', function(e) {
                const value = e.target.value.trim();
                if (value && !ValidationConfig.patterns.email.test(value)) {
                    showInputFeedback(e.target, 'Correo electrónico inválido', 'error');
                }
            });
        },

        // Capitalize name
        name: function(input) {
            input.addEventListener('input', function(e) {
                e.target.value = e.target.value.replace(/[0-9]/g, '');
            });
            input.addEventListener('blur', function(e) {
                e.target.value = e.target.value
                    .toLowerCase()
                    .split(' ')
                    .filter(word => word.length > 0)
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ');
            });
        }
    };

    // Show temporary feedback on input
    function showInputFeedback(input, message, type = 'info') {
        const colors = {
            error: '#ef4444',
            warning: '#f59e0b',
            success: '#10b981',
            info: '#3b82f6'
        };

        // Check if feedback already exists
        let feedback = input.parentElement.querySelector('.input-feedback');
        if (feedback) {
            clearTimeout(feedback._timeout);
        } else {
            feedback = document.createElement('div');
            feedback.className = 'input-feedback';
            feedback.style.cssText = `
                position: absolute;
                top: -30px;
                left: 0;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.75rem;
                color: white;
                background: ${colors[type]};
                opacity: 0;
                transform: translateY(5px);
                transition: all 0.2s ease;
                z-index: 100;
                white-space: nowrap;
            `;
            input.parentElement.style.position = 'relative';
            input.parentElement.appendChild(feedback);
        }

        feedback.textContent = message;
        feedback.style.background = colors[type];

        // Animate in
        setTimeout(() => {
            feedback.style.opacity = '1';
            feedback.style.transform = 'translateY(0)';
        }, 10);

        // Remove after delay
        feedback._timeout = setTimeout(() => {
            feedback.style.opacity = '0';
            feedback.style.transform = 'translateY(5px)';
            setTimeout(() => feedback.remove(), 200);
        }, 2500);
    }

    // Auto-initialize on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        // Auto-apply validations based on data attributes
        document.querySelectorAll('[data-validate-type]').forEach(input => {
            const type = input.dataset.validateType;
            if (Validators[type]) {
                Validators[type](input);
            }
        });

        // Apply to common field names automatically
        const autoValidateFields = {
            'nombre': 'name',
            'apellido': 'name',
            'nombre_completo': 'name',
            'first_name': 'name',
            'last_name': 'name',
            'telefono': 'phone',
            'celular': 'phone',
            'phone': 'phone',
            'email': 'email',
            'correo': 'email'
        };

        Object.entries(autoValidateFields).forEach(([fieldName, validationType]) => {
            document.querySelectorAll(`[name="${fieldName}"], [name*="${fieldName}"], #${fieldName}`).forEach(input => {
                if (!input.dataset.validateType && Validators[validationType]) {
                    Validators[validationType](input);
                }
            });
        });
    });

    // Export to global scope
    window.FormValidator = FormValidator;
    window.Validators = Validators;
    window.ValidationConfig = ValidationConfig;

})();

// Add validation styles
const validationStyles = document.createElement('style');
validationStyles.textContent = `
    .is-invalid {
        border-color: #ef4444 !important;
        background-color: rgba(239, 68, 68, 0.05) !important;
    }

    .is-valid {
        border-color: #10b981 !important;
        background-color: rgba(16, 185, 129, 0.05) !important;
    }

    .validation-error {
        color: #ef4444;
        font-size: 0.75rem;
        margin-top: 4px;
        display: none;
        animation: fadeInError 0.2s ease;
    }

    @keyframes fadeInError {
        from {
            opacity: 0;
            transform: translateY(-5px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .input-shake {
        animation: shake 0.4s ease;
    }

    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        50% { transform: translateX(5px); }
        75% { transform: translateX(-5px); }
    }
`;
document.head.appendChild(validationStyles);

