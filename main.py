from aiogram import Bot, Dispatcher, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.types.callback_query import CallbackQuery
from aiogram.utils.deep_linking import get_start_link, decode_payload
from pytube import YouTube, Channel
import logging, re, time, requests, os

import nest_asyncio
nest_asyncio.apply()

# convert byte to MB or GB (File size)
def byte(number, str=True):
    number_kb = round(number / 1024, 1)
    number = round(number / 1024 / 1024, 1)
    if str==True:
        return f'{number_kb}KB' if number_kb < 1024 else f'{number}MB' if number < 1024 else f'{round(number / 1024, 2)}GB'
    else:
        return number

# convert seconds to minutes and hours (Video duration)
def duration(ytobj):
    duration = ytobj.length
    if duration < 60:
        return f'0:{duration}'

    elif 60 <= duration < 3600:
        minute = duration / 60
        second = duration % 60
        return f'{int(minute)}:{second}'

    else:
        hour = duration / 3600
        minute = (duration % 3600) / 60
        second = (duration % 3600) % 60
        return f'{int(hour)}:{int(minute)}:{second}'

BOT_TOKEN = '5613844224:AAGPJVwuxo-hfEI62CHLCOz5BSEws8KAOYw'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# To handle deep-linked commands
@dp.message_handler(commands=['start'])
async def deep_decode(message: Message):
    if args := message.get_args():
        try:
            print(message.from_user.username)

            # decode deep link and create youtube object
            video_url = decode_payload(args)
            ytobj = YouTube(video_url)
            
            # Access the size of the audio file to achieve the final size
            mp4_audio = ytobj.streams.get_by_itag(139)
            webm_audio = ytobj.streams.get_by_itag(249)
            
            # Filter streams (videos and audios) to display in the inline keyboard
            Streams = ytobj.streams.filter(adaptive=True, only_video=True,)
            Streams_Audio = ytobj.streams.filter(adaptive=True, only_audio=True)
            
            # Setting a number of variables to create an inline keyboard as desired
            counter, zoj, fard = 1, False, False
            kb0 = InlineKeyboardMarkup()

            # The number of keyboard buttons should be equal to the number of streams
            for stream in Streams:
                if stream.itag not in range(390, 405):
                    
                    # For each video format, on specific audio format must be considered in order to get the correct final file size from the sum of the two
                    if stream.subtype == 'mp4':
                        finall_size =  stream.filesize+mp4_audio.filesize
                    else:
                        finall_size =  stream.filesize+webm_audio.filesize

                    # Sometimes it may be only one format of one quality
                    if stream.subtype == 'webm' and counter == 1:
                        kb0.add(InlineKeyboardButton(text=f'{stream.resolution}, {stream.subtype}, {byte(finall_size)}', callback_data=f'{stream.itag}{video_url}'))
                        continue

                    # The layout of the keyboard buttons is created in 2 columns
                    elif counter % 2 != 0:
                        button0, zoj = InlineKeyboardButton(text=f'{stream.resolution}, {stream.subtype}, {byte(finall_size)}', callback_data=f'{stream.itag}{video_url}'), True
                    elif counter % 2 == 0:
                        button1, fard = InlineKeyboardButton(text=f'{stream.resolution}, {stream.subtype}, {byte(finall_size)}', callback_data=f'{stream.itag}{video_url}'), True

                    # Add buttons to keyboard when created
                    if zoj and fard:
                        kb0.add(button0, button1)
                        zoj, fard = False, False
                    counter += 1


            # To avoid creating duplicate keys
            Shit = []
            # Exactly like the previous keyboard
            for stream in Streams_Audio:
                if stream.itag not in range(390, 405):
                    finall_size =  stream.filesize

                    # This will change soon
                    # stream_type = 'm4a' if stream.subtype == 'mp4' else 'ogg'

                    # Add the button to the keyboard if the itag stream is not duplicated
                    if stream.itag not in Shit:
                        Shit.append(stream.itag)
                        kb0.add(InlineKeyboardButton(text=f'🔊 {stream.abr}, {stream.subtype}, {byte(finall_size)}', callback_data=f'{stream.itag}{video_url}'))

            # Send message containing keyboard
            msg = await message.answer(f'Select your preferred format\n\nDuration *{duration(ytobj)}*', reply_markup=kb0, parse_mode='MarkDown')
    
        # Detection of unknown errors
        except Exception as exception:
            await message.answer(f"Error: {exception}")

    # If the command did not contain a deep link
    else:
        await message.answer(f'Welcome <b>{message.from_user.first_name} {message.from_user.last_name}</b>\n\n{message.chat.id}', parse_mode='HTML')

@dp.callback_query_handler()
async def send_format(call: CallbackQuery):
    try:

        video_url, itag = (call.data[3:], call.data[:3])
        ytobj = YouTube(video_url)

        # create needed files objects (main file, 2 audio file for calculate file size(mp4, webm))
        File, mp4_audio, webm_audio = ytobj.streams.get_by_itag(itag), ytobj.streams.get_by_itag(139), ytobj.streams.get_by_itag(249)
        # Choosing the appropriate audio file for the video format, to achieve the final size of the file
        
        if File.mime_type == 'video/mp4':
            audio_filesize, audio_itag = mp4_audio.filesize, mp4_audio.itag
        elif File.mime_type == 'video/webm':
            audio_filesize, audio_itag = webm_audio.filesize, webm_audio.itag
        else:
            audio_filesize, audio_itag = 0, itag
        # audio_filesize, audio_itag = mp4_audio.filesize, mp4_audio.itag if File.mime_type == 'video/mp4' else webm_audio.filesize, webm_audio.itag if File.mime_type == 'video/webm' else 0, itag

        # create needed file for merging, and file size and caption
        audio = ytobj.streams.get_by_itag(audio_itag)
        finall_size =  File.filesize+audio_filesize
        # Caption = f'{File.title}\n\n<a href="t.me/new_bbxc">BeatboxClub</a>'
        Caption = f"{File.title}\n\n<a href='t.me/beatboxclub2018'>CHANNEL ID</a>"
        # if selected format button was a video
        
        if byte(finall_size, str=False) < 50 and File.type == 'video':
            # file's info
            FileName = f'V{itag}{video_url[17:22]}.{File.subtype}'
            AudioName = f'A{audio_itag}{video_url[17:22]}.{File.subtype}'
            Merged_File_Name = f'O{itag}{video_url[17:22]}.{File.subtype}'
            cover = f'T{itag}{video_url[17:22]}.jpeg'

            # Download video
            msg = await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Downloading Video ...')
            File.download(filename=f'{FileName}')
            audio.download(filename=f'{AudioName}')
            # Merging audio and video
            await msg.edit_text('Merging ...')
            os.system(f'ffmpeg -i /content/{FileName} -i /content/{AudioName} -c:v copy -c:a copy -map 0:v -map 1:a /content/{Merged_File_Name}')

            # chage thumbnail resolution
            os.system(f'ffmpeg -i {ytobj.thumbnail_url} -vf scale=320:240 {cover}')

            Thumbnail = f'Z{itag}{video_url[17:22]}.jpeg'
            os.system(f'ffmpeg -i {cover} -vf crop=320:180 {Thumbnail}')

            # Upload video to telegram
            await msg.edit_text('Uploading ...')
            Video = open(f'/content/{Merged_File_Name}', 'rb')
            Thumb = open(f'/content/{Thumbnail}', 'rb')
            res = await bot.send_video(chat_id=call.message.chat.id,
                video = Video,
                duration = ytobj.length,
                width = 1280,
                height = 720,
                thumb = Thumb,
                # thumb = ytobj.thumbnail_url,
                supports_streaming = True,
                caption=Caption,
                parse_mode='HTML')
            Video.close()
            Thumb.close()
            await msg.delete()

            # delete file after sending
            os.system(f'rm -v /content/{FileName} /content/{AudioName} /content/{Merged_File_Name} /content/{Thumbnail}')

            # file id
            print(res.video.file_id)

        # if selected format button was a audio
        elif byte(finall_size, str=False) < 50 and File.type == 'audio':

            # file info
            AudioName = f'A{itag}{video_url[17:22]}.{audio.subtype}'
            # Download audio
            msg = await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Downloading Audio ...')
            audio.download(filename=f'{AudioName}')
            # Upload audio to telegram
            await msg.edit_text('Uploading ...')
            Audio = open(f'/content/{AudioName}', 'rb')
            res = await bot.send_audio(chat_id=call.message.chat.id,
                audio=Audio,
                duration = ytobj.length,
                caption=Caption,
                parse_mode='HTML')
            Audio.close()
            await msg.delete()
            
            # delete file after sending
            os.system(f'rm /content/{AudioName}')
            # file id
            print(res.audio.file_id)

        else:
            await call.answer(f"[❗️] FILE IS TOO LARGE")

    except Exception as exception:
        await msg.edit_text(f"Error: {exception}")
        # await call.answer(f"Error: {exception}")
        os.system(f'rm -v /content/{FileName} /content/{AudioName} /content/{Merged_File_Name} /content/{Thumbnail}')

@dp.message_handler()
async def manual_posting(message: Message):
    if message.from_user.username == 'Abdullah_8BX78':
        try:
            text_message = message.text
            if video_id:= re.findall("watch\?v=*(.{11})|youtu.be\/(.{11})|shorts\/(.{11})|embed\/(.{11})", text_message):
                msg = await message.reply("Get info...")

                # create video url
                Match = [sorted(video_id[0])][-1][-1]
                video_url = f"https://youtu.be/{Match}"
                video_obj = YouTube(video_url)
                channel_obj = Channel(video_obj.channel_url)

                # check for video status
                try:
                    video_obj.vid_info["videoDetails"]["isUpcoming"]
                    status = f" {video_obj.vid_info['playabilityStatus']['reason']}"
                except Exception:
                    try:
                        video_obj.vid_info["videoDetails"]["isLive"]
                        status = " LIVE"
                    except KeyError:
                        status = ""

                # convert video url to deep link for starting chat in other bot (put it to inline keyboard button)
                link0 = await get_start_link(video_url, encode=True)

                Thumbnail = f'{video_url[17:22]}.jpg'
                os.system(f'ffmpeg -i {video_obj.thumbnail_url} -vf crop=640:360 {Thumbnail}')

                Thumb = open(f'/content/{Thumbnail}', 'rb')

                await bot.send_photo(
                    chat_id="@new_bbxc",
                    # chat_id="@beatboxclub2018",
                    # chat_id=message.chat.id,
                    photo=Thumb,
                    caption=f"<b>{channel_obj.channel_name}</b>{status}\n{video_obj.title}\n\n<a href='t.me/beatboxclub2018'>CHANNEL ID</a>",
                    reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text="Download", url=link0), InlineKeyboardButton(text="Watch", url=video_url)),
                    parse_mode='HTML'
                )
                Thumb.close()
                os.system(f'rm -v /content/{Thumbnail}')

                await msg.edit_text("Video sent")
            else:
                await message.answer("Invalid URL")

        except OSError as exception:
            await message.answer(f"_Video is private_\n\n{exception}", parse_mode='MarkDown')
        except Exception as exception:
            await message.answer(f"Error: {exception}")

    else:
        await message.answer("Go back to the <a href='t.me/beatboxclub2018'>Channel</a>\nand hit the <b>Download</b> button.", parse_mode='HTML')

print('running...')
executor.start_polling(dp, skip_updates=True)
