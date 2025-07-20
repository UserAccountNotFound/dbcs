// mnsn.js
// Управление элементами интерфейса для Мессенджеров и Социальных Сетей
//



document.addEventListener('DOMContentLoaded', function() {
    const socialContainer = document.getElementById('additional-social-media');
    const addSocialBtn = document.getElementById('add-social-btn');
    
    // Получаем конфиг из глобальной переменной, переданной из бэкенда
    const socialOptions = window.socialConfig.filter(social => 
        !['telegram', 'whatsapp'].includes(social.key) && 
        !document.querySelector(`input[name="${social.key}"]`)
    );

    function createSocialField(social) {
        const fieldDiv = document.createElement('div');
        fieldDiv.className = 'relative flex items-center space-x-2';
        fieldDiv.innerHTML = `
            <div class="flex-grow">
                <label for="${social.key}" class="block text-sm font-medium text-gray-700">
                    <i class="${social.icon} mr-2 ${social.class.split(' ')[0]}"></i>${social.label}
                </label>
                <div class="mt-1 flex rounded-md shadow-sm">
                    <input type="text" id="${social.key}" name="${social.key}"
                           class="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                           placeholder="${social.placeholder}">
                </div>
            </div>
            <button type="button" class="remove-social-btn mt-6 text-red-600 hover:text-red-800">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
            </button>
        `;
        
        fieldDiv.querySelector('.remove-social-btn').addEventListener('click', function() {
            fieldDiv.remove();
            addSocialBtn.style.display = 'inline-flex';
        });
        
        return fieldDiv;
    }

    function createSocialSelector() {
        const availableSocials = socialOptions.filter(social => 
            !document.querySelector(`input[name="${social.key}"]`)
        );

        if (availableSocials.length === 0) {
            addSocialBtn.style.display = 'none';
            return;
        }

        const fieldDiv = document.createElement('div');
        fieldDiv.className = 'relative flex items-center space-x-2';
        
        const select = document.createElement('select');
        select.className = 'social-select mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500';
        
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Выбрать из списка';
        select.appendChild(defaultOption);
        
        availableSocials.forEach(social => {
            const option = document.createElement('option');
            option.value = social.key;
            option.textContent = social.label;
            option.dataset.social = JSON.stringify(social);
            select.appendChild(option);
        });
        
        select.addEventListener('change', function() {
            if (this.value) {
                const selectedSocial = JSON.parse(this.options[this.selectedIndex].dataset.social);
                const socialField = createSocialField(selectedSocial);
                fieldDiv.replaceWith(socialField);
                
                if (availableSocials.length <= 1) {
                    addSocialBtn.style.display = 'none';
                }
            }
        });
        
        fieldDiv.appendChild(select);
        socialContainer.appendChild(fieldDiv);
    }

    addSocialBtn.addEventListener('click', createSocialSelector);
});