from io import BytesIO

import segno


def generate_qr_svg(content: str) -> bytes:
    """
    Генерирует QR-код в формате SVG.

    SVG удобен тем, что:
    - масштабируется без потери качества;
    - мало весит;
    - может быть отображен в PWA и веб-интерфейсе.
    """
    qr = segno.make(content, error="m")

    buffer = BytesIO()
    qr.save(
        buffer,
        kind="svg",
        scale=4,
        dark="#000000",
        light="#ffffff",
    )

    return buffer.getvalue()