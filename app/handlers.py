from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import Message
import yt_dlp
import asyncio
import os


router = Router(name=__name__)


def download_video(url):
    ydl_opts = {'outtmpl': 'downloads/%(title)s.%(ext)s',
                'format': '18'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url)
        return f"downloads/{info['title']}.{info['ext']}"


@router.message(CommandStart())
async def cmd(mes: Message):
    await mes.answer('Добро пожаловать ведите ссылку на видео которую хотите скачать')


@router.message()
async def downland_video(mes: Message):
    try:
        video_url = mes.text
        video = await asyncio.to_thread(download_video, video_url)
        await mes.answer_document(types.FSInputFile(video))
        os.remove(video)
    except yt_dlp.utils.DownloadError:
        await mes.answer('Неверная ссылка! ❌')



