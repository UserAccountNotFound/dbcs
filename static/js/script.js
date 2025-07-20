// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация поля ввода местоположения, если оно существует
    const locationInput = document.getElementById('location');
    if (locationInput) {
        initializeLocationInput(locationInput);
    }
});

function initializeLocationInput(input) {
    // Обновление placeholder
    //input.placeholder = 'Вставте ссылку на карты Google';

    // Опционально: Добавление кнопки для получения ссылки на карты
    const helpButton = document.createElement('button');
    helpButton.type = 'button';
    helpButton.className = 'mt-2 text-sm text-blue-600 hover:text-blue-800';
    helpButton.textContent = 'Как получить ссылку на ваше местоположение?';
    helpButton.onclick = showLocationHelp;
    input.parentNode.appendChild(helpButton);
}

function showLocationHelp() {
    alert(`Чтобы получить ссылку на ваше местоположение:
        1. Откройте Google Maps
        2. Найдите ваше местонахождение location
        3. Кликните 'Поделиться' нажмите на пин 'вашего' местоположения
        4. Скопируйте предоставленную ссылку`);
}

// Обработчик предпросмотра изображения
function previewImage(input) {
    const preview = document.getElementById('preview-image');
    const defaultPhoto = document.getElementById('default-photo');

    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.classList.remove('hidden');
            defaultPhoto.classList.add('hidden');
        }

        reader.readAsDataURL(input.files[0]);
    }
}

// Функции модального окна QR-кода
function showQRModal(qrCode, cardUrl) {
    const modal = document.getElementById('qr-modal');
    if (modal) {
        document.getElementById('qr-image').src = 'data:image/png;base64,' + qrCode;
        document.getElementById('share-link').value = cardUrl;
        modal.classList.remove('hidden');
    }
}

function closeModal() {
    const modal = document.getElementById('qr-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function copyLink() {
    const linkInput = document.getElementById('share-link');
    if (linkInput) {
        linkInput.select();
        document.execCommand('copy');

        const button = event.target;
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        setTimeout(() => {
            button.textContent = originalText;
        }, 2000);
    }
}

function shareCard(platform) {
    const url = document.getElementById('share-link').value;
    const text = "Моя электронная визитка";

    switch(platform) {
        case 'whatsapp':
            window.open(`https://wa.me/?text=${encodeURIComponent(text + ' ' + url)}`);
            break;
        case 'email':
            window.open(`mailto:?subject=Электронная визитная карта&body=${encodeURIComponent(text + '\n\n' + url)}`);
            break;
        case 'twitter':
            window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text + ' ' + url)}`);
            break;
    }
}