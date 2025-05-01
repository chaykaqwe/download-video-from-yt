from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp
import asyncio


async def get_available_formats(url):
    def _fetch_formats():
        with yt_dlp.YoutubeDL({}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            return [
                {
                    'format_id': fmt['format_id'],
                    'resolution': fmt.get('resolution', 'audio only'),
                    'ext': fmt['ext']
                }
                for fmt in formats if fmt.get('resolution')  # оставляем только видео
            ]

    formats = await asyncio.to_thread(_fetch_formats)
    return formats


def generate_format_keyboard(formats, url):
    format_titles = {
        "4320p": "8K Ultra HD",
        "2160p": "4K Ultra HD",
        "1440p": "2K Quad HD",
        "1080p": "Full HD",
        "720p": "HD",
        "480p": "SD",
        "360p": "Low",
        "240p": "Very Low",
        "144p": "Minimal",
        "audio only": "Audio"
    }

    # Очистим повторы через множество
    unique_buttons = {}

    for fmt in formats:
        resolution = fmt.get('resolution', 'audio only')
        ext = fmt['ext']

        # Преобразуем "1920x1080" в "1080p"
        if "x" in resolution:
            try:
                height = resolution.split('x')[1]
                resolution = f"{height}p"
            except IndexError:
                resolution = "Unknown"

        title = format_titles.get(resolution, resolution)
        button_text = f"{title} ({ext})"

        # Используем текст как ключ, чтобы избежать дублей
        if button_text not in unique_buttons:
            unique_buttons[button_text] = fmt['format_id']

    # Теперь отсортируем кнопки по качеству
    sort_order = [
        "8K Ultra HD", "4K Ultra HD", "2K Quad HD", "Full HD",
        "HD", "SD", "Low", "Very Low", "Minimal", "Audio"
    ]

    def sort_key(button_text):
        for i, quality in enumerate(sort_order):
            if quality in button_text:
                return i
        return len(sort_order)

    sorted_buttons = sorted(unique_buttons.items(), key=lambda item: sort_key(item[0]))

    # Создание клавиатуры
    builder = InlineKeyboardBuilder()

    for button_text, format_id in sorted_buttons:
        builder.button(
            text=button_text,
            callback_data=f"format_{format_id}_{url}"
        )

    builder.adjust(2)
    return builder.as_markup()