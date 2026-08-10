# CSS-шаблоны визиток DBCS

Каркас HTML фиксирован. Шаблон — только CSS-файл
`{code}.css` в этой директории.

## Корень

```html
<div class="dbcs-card tpl-{code} scheme-light|scheme-dark [no-photo] [no-qr] [no-logo]"
     style="--dbcs-accent:...; --dbcs-font:...; --dbcs-scheme:...">
```

Все селекторы шаблона **обязаны** начинаться с `.tpl-{code}`
(или быть вложенными в него), иначе стили протекут в другие темы.

## Классы каркаса

| Класс | Элемент |
|-------|---------|
| `.dbcs-card` | Корень страницы визитки |
| `.dbcs-content` | Центрированная колонка контента |
| `.dbcs-logo` / `.dbcs-logo img` | Логотип |
| `.dbcs-avatar` / `.dbcs-avatar img` / `.dbcs-avatar-fallback` | Фото / инициалы |
| `.dbcs-name` | ФИО |
| `.dbcs-title` | Должность / подзаголовок |
| `.dbcs-meta` | Отдел и др. |
| `.dbcs-company` | Компания |
| `.dbcs-bio` | Заметка / bio |
| `.dbcs-links` | Стек кнопок-ссылок |
| `.dbcs-link` | Одна кнопка (телефон, email, сайт, адрес) |
| `.dbcs-link-icon` | Иконка в кнопке |
| `.dbcs-link-label` | Текст кнопки |
| `.dbcs-qr` / `.dbcs-qr img` / `.dbcs-qr-label` | QR-код |
| `.dbcs-actions` | Блок CTA (vCard / Share) |
| `.dbcs-action` | Кнопка CTA |
| `.dbcs-action-primary` | Основная CTA |
| `.dbcs-action-secondary` | Вторичная CTA |
| `.dbcs-footer` | Подпись внизу |

## CSS-переменные персонализации

Задаются инлайном из темы визитки:

- `--dbcs-accent` — акцентный цвет (`#RRGGBB`)
- `--dbcs-scheme` — `light` или `dark`
- `--dbcs-font` — CSS font-family stack

Классы-модификаторы корня:

- `.scheme-dark` / `.scheme-light`
- `.no-photo`, `.no-qr`, `.no-logo` — скрыть блоки

## Эффекты (опционально)

Если в meta шаблона (`schema_json`) указано `"effect": "polygon"`,
рендерер включает canvas-сеть частиц на корне
(`data-effect="polygon"`). CSS должен рассчитывать на тёмный фон.

## Ограничения безопасности

Запрещены: `@import`, `expression(`, `-moz-binding`, `behavior:`.
Максимальный размер файла задаётся настройкой сервера.

## Будущее

В следующих версиях CSS может храниться в БД; контракт классов
и переменных сохранится.
