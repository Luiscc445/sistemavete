// JavaScript extraido de nueva_cita.html
// Generado automaticamente el 2025-11-22 22:25:48

function updatePrice() {
        const select = document.getElementById('servicio_id');
        const option = select.options[select.selectedIndex];
        const precio = option.getAttribute('data-precio');
        const nombreServicio = option.getAttribute('data-nombre');

        // Actualizar precio
        const display = document.getElementById('precioEstimado');
        if (precio) {
            display.textContent = 'Bs. ' + parseFloat(precio).toFixed(2);
        } else {
            display.textContent = 'Bs. 0.00';
        }

        // Filtrar veterinarios
        filterVeterinarians(nombreServicio);
    }

    function filterVeterinarians(servicioNombre) {
        const vetSelect = document.getElementById('veterinario_id');
        const options = vetSelect.querySelectorAll('option');
        let foundSpecialist = false;
        let firstVisible = null;

        // Reset selection
        vetSelect.value = "";

        options.forEach(opt => {
            if (opt.value === "") return; // Skip placeholder

            const especialidad = opt.getAttribute('data-especialidad');

            // Lógica de filtrado
            if (!servicioNombre) {
                opt.style.display = "";
            } else {
                const sName = servicioNombre.toLowerCase();
                const vSpec = (especialidad || "").toLowerCase();
                let match = false;

                // Casos especiales
                if (sName.includes('dental') && vSpec.includes('odontolog')) match = true;
                else if ((sName.includes('hueso') || sName.includes('fractura')) && vSpec.includes('traumatolog')) match = true;
                else if ((sName.includes('ojo') || sName.includes('vista')) && vSpec.includes('oftalmol')) match = true;
                else if ((sName.includes('nervio') || sName.includes('cerebro')) && vSpec.includes('neurolog')) match = true;
                else if ((sName.includes('cancer') || sName.includes('tumor')) && vSpec.includes('oncolog')) match = true;
                else if ((sName.includes('eco') || sName.includes('rayos')) && vSpec.includes('imagenolog')) match = true;
                else if (vSpec.includes(sName) || sName.includes(vSpec)) match = true;

                if (match) {
                    opt.style.display = "";
                    foundSpecialist = true;
                    if (!firstVisible) firstVisible = opt;
                } else {
                    opt.style.display = "none";
                }
            }
        });

        // Fallback
        if (servicioNombre && !foundSpecialist) {
            options.forEach(opt => {
                if (opt.value === "") return;
                const vSpec = (opt.getAttribute('data-especialidad') || "").toLowerCase();
                if (vSpec.includes('general') || vSpec === "") {
                    opt.style.display = "";
                    if (!firstVisible) firstVisible = opt;
                }
            });
        }

        // Auto-select
        if (firstVisible) {
            vetSelect.value = firstVisible.value;
        }
    }