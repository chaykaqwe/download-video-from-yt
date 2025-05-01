from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
import yt_dlp
import asyncio
import os
import zipfile
import re
from typing import Optional

from keyboard import get_available_formats, generate_format_keyboard

router = Router(name=__name__)


def compress_file(input_path: str, output_path: str) -> None:
    """Сжимает файл в ZIP-архив"""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(input_path, arcname=os.path.basename(input_path))


def download_video(url, format):
    ydl_opts = {'outtmpl': 'downloads/%(title)s.%(ext)s',
                'format': f"{format}+bestaudio[ext=m4a]/mp4"}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url)
        return f"downloads/{info['title']}.{info['ext']}"


@router.message(CommandStart())
async def cmd(mes: Message):
    await mes.answer('Добро пожаловать! Введите ссылку на видео для скачивания')


@router.message()
async def what_format(mes: Message):
    url = mes.text
    formats = await get_available_formats(url)
    if not formats:
        await mes.answer('Не удалось найти форматы для этого видео 😞')
        return

    keyboard = generate_format_keyboard(formats, url)
    await mes.answer('Выберите нужный формат 🎬', reply_markup=keyboard)


def sanitize_filename(filename: str, placeholder: str = "_") -> str:
    """Очищает имя файла от недопустимых символов"""
    # Список запрещенных символов: \ / : * ? " < > |
    cleaned_name = re.sub(r'[\\/:*?"<>|]', placeholder, filename)
    # Удаляем ведущие и завершающие пробелы/точки
    cleaned_name = cleaned_name.strip().strip('.')
    # Убираем двойные подчеркивания
    return re.sub(r'_+', '_', cleaned_name)


def download_video(url, format_code) -> Optional[str]:
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = sanitize_filename(info['title'])

        if format_code != '140':
            ydl_opts = {
                'outtmpl': f'downloads/{title}.%(ext)s',
                'format': f"{format_code}+bestaudio[ext=m4a]/mp4",
            }
        else:
            ydl_opts = {
                'outtmpl': f'downloads/{title}.%(ext)s',
                'format': f"{format_code}"
            }


        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            return f"downloads/{title}.{info['ext']}"

    except Exception as e:
        return None


@router.callback_query(F.data.startswith("format_"))
async def downland_video(callback: CallbackQuery):
    try:
        await callback.answer("Начинаем загрузку...")
        _, format_id, url = callback.data.split("_", 2)

        video_path = await asyncio.to_thread(download_video, url, format_id)
        if not video_path or not os.path.exists(video_path):
            raise FileNotFoundError("Ошибка создания файла")

        # Генерируем безопасное имя для архива
        zip_name = sanitize_filename(os.path.basename(video_path)) + ".zip"
        zip_path = os.path.join("downloads", zip_name)

        await asyncio.to_thread(compress_file, video_path, zip_path)

        try:
            await callback.message.answer_document(
                document=types.FSInputFile(zip_path, filename=zip_name),
                caption="Ваше видео в архиве 📁",
                request_timeout=30
            )
        finally:
            for path in [video_path, zip_path]:
                if os.path.exists(path):
                    os.remove(path)

    except Exception as e:
        error_msg = f"Ошибка: {sanitize_filename(str(e))}"[:200]
        await callback.message.answer(error_msg)