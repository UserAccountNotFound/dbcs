# CSS-шаблоны визиток DBCS

Каркас HTML фиксирован (`PublicCardRenderer` на frontend). Шаблон — только CSS-файл
`{code}.css` в этой директории.

Текущие файлы: `classic`, `modern`, `compact`, `corporate`, `creative`.

Раздача: `GET /api/v1/templates/{code}/css` (без авторизации).  
Каталог настраивается через `TEMPLATES_CSS_DIR` (по умолчанию этот путь).

## Корень

```html
<div class="dbcs-card tpl-{code} scheme-light|scheme-dark [no-photo] [no-qr] [no-logo]"
     style="--dbcs-accent:...; --dbcs-font:...; --dbcs-scheme:..."
     data-effect="polygon|…">
```

Все селекторы шаблона **обязаны** начинаться с `.tpl-{code}`
(или быть вложенными в него), иначе стили протекут в другие темы.

## Классы каркаса

| Класс | Элемент |
|-------|---------|
| `.dbcs-card` | Корень страницы визитки |
| `.dbcs-content` | Центрированная колонка контента |
| `.dbcs-logo` / `.dbcs-logo img` | Логотип |
| `.dbcs-avatar` / `.dbcs-avatar img` | Фото |
| `.dbcs-name` | ФИО |
| `.dbcs-title` | Должность / подзаголовок |
| `.dbcs-company` | Компания |
| `.dbcs-bio` | Заметка |
| `.dbcs-links` | Стек кнопок-ссылок |
| `.dbcs-link` | Кнопка (телефон, email, сайт, адрес, мессенджеры) |
| `.dbcs-link-icon` | Иконка |
| `.dbcs-link-label` | Текст |
| `.dbcs-qr` / `.dbcs-qr img` / `.dbcs-qr-label` | QR |
| `.dbcs-actions` | CTA (vCard / Share) на публичной странице |
| `.dbcs-action` / `-primary` / `-secondary` | Кнопки CTA |
| `.dbcs-footer` | Подпись |
| `.dbcs-preview` | Режим превью в селекторе шаблонов (уменьшенный каркас) |

## CSS-переменные персонализации

Задаются инлайном из темы визитки:

- `--dbcs-accent` — акцентный цвет (`#RRGGBB`)
- `--dbcs-scheme` — `light` или `dark`
- `--dbcs-font` — CSS font-family stack

Модификаторы корня: `.scheme-dark` / `.scheme-light`, `.no-photo`, `.no-qr`, `.no-logo`.

## Meta шаблона (`schema_json`)

Опционально:

- `default_accent`, `default_scheme` — подставляются при выборе шаблона в форме
- `effect: "polygon"` — canvas-сеть частиц (`data-effect="polygon"`, не в preview)

## Ограничения безопасности

При загрузке CSS через админку запрещены опасные конструкции
(`@import`, `expression(`, `-moz-binding`, `behavior:` и т.п.).
Максимальный размер файла задаётся настройками сервера.

## Будущее

CSS может храниться в БД; контракт классов и переменных сохранится.
