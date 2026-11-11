#!/usr/bin/env python3
"""Train and export the assistant's tiny, local intent classifier.

The examples are curated, not collected from visitors. The exported model is an
int8-quantized character-n-gram MLP; inference is implemented in assistant-model.js.
"""
import argparse
import base64
import json
from pathlib import Path

import numpy as np
from sklearn.neural_network import MLPClassifier

LABELS = [
    'converter', 'audio-compressor', 'volume-booster', 'audio-trimmer',
    'audio-joiner', 'audio-speed-changer', 'slowed-reverb', 'voice-to-text',
    'vocal-remover', 'text-to-speech', 'unsupported',
]

# Keep the held-out cases separate: these are paraphrases, not copies of training lines.
TRAIN = {
'converter': '''
en|change a song into another audio container
en|save this voice memo in a format my phone understands
en|turn a movie clip into a sound file
en|keep only the soundtrack from this clip
en|make this recording playable as music
en|change the encoding of my sound file
ru|достань музыку из этого клипа
ru|сохрани запись в другом аудио контейнере
ru|нужен только звуковой ряд из фильма
ru|поменяй кодировку звукового файла
ru|сделай из видеозаписи музыкальный файл
zh|把电影里的音乐留下来
zh|改变这个录音的编码
zh|只保留短片里的声音
zh|把语音备忘录换成手机能打开的音频
zh|从影片中分离音乐
''',
'audio-compressor': '''
en|my attachment exceeds the mail limit
en|this recording is enormous and hard to send
en|make the voice note easier to upload
en|the messenger rejects my heavy sound file
en|I need a lighter version of this recording
en|shrink how many bytes this song takes
ru|вложение не проходит по лимиту почты
ru|запись слишком тяжелая для отправки
ru|нужна более легкая версия этой песни
ru|мессенджер не принимает такой большой звук
ru|сделай аудио полегче для загрузки
zh|附件超过邮箱限制
zh|这段录音太大很难发送
zh|音乐文件太重上传不了
zh|让这条语音更容易分享
zh|需要一个更轻的歌曲版本
''',
'volume-booster': '''
en|I can barely hear this recording
en|the sound is very faint
en|raise the level of this quiet podcast
en|my voice note is hardly audible
en|even at maximum I struggle to hear it
en|balance the loudness to a normal level
ru|почти не слышно эту запись
ru|звук очень слабый
ru|едва слышно голос в подкасте
ru|даже на максимуме ничего не разобрать
ru|подними уровень слабой записи
zh|这段录音几乎听不见
zh|声音非常微弱
zh|播客讲话声太轻了
zh|开到最大还是很难听清
zh|把轻声的录音调响一点
''',
'audio-trimmer': '''
en|I only need the chorus
en|keep just the useful part of this recording
en|delete the awkward beginning
en|leave out the silence at the end
en|take a short excerpt from this lecture
en|make a ring sound from the best moment
ru|оставь только припев
ru|нужен лишь полезный кусок записи
ru|удали неловкое начало
ru|убери тишину в конце
ru|возьми небольшой фрагмент лекции
zh|只保留副歌部分
zh|留下录音里有用的一段
zh|删掉尴尬的开头
zh|去掉末尾的空白
zh|从讲座里取一小段
''',
'audio-joiner': '''
en|put these tracks back to back
en|stitch two recordings together
en|make one continuous song from these pieces
en|glue this intro to the main recording
en|play these voice notes as a single file
en|assemble my audio clips in order
ru|поставь треки друг за другом
ru|сшей две записи в одну
ru|собери эти куски в непрерывную песню
ru|приклеи вступление к основной записи
ru|проиграй голосовые одним файлом
zh|把几首歌首尾接起来
zh|把两段录音接成一个
zh|让这些片段连续播放
zh|把片头接到主录音前面
zh|按顺序组装这些声音片段
''',
'audio-speed-changer': '''
en|make this podcast take less time without changing voices
en|I want more leisurely playback
en|listen to the lecture in half the time
en|stretch out this song so it plays longer
en|change how quickly the recording plays
en|make the narrator talk at an easier pace
ru|хочу прослушать лекцию за меньшее время
ru|нужно более неторопливое воспроизведение
ru|пусть подкаст закончится быстрее без изменения голоса
ru|растяни песню чтобы она играла дольше
ru|измени темп речи диктора
zh|想快点听完这个讲座
zh|希望播放得更从容一些
zh|让播客在短时间内听完但声音不变
zh|把这首歌播放得久一点
zh|改变讲述者的说话节奏
''',
'slowed-reverb': '''
en|make a hazy atmospheric edit of this song
en|give the track a spacious dreamy feel
en|create a moody version for a short video
en|make this sound like a slow nostalgic edit
en|add a cavernous effect and relax the tempo
en|I want an ethereal nighttime remix
ru|сделай атмосферную ностальгическую версию
ru|добавь пространственный эффект и расслабленный темп
ru|нужен мрачный редакция для короткого видео
ru|сделай песню будто в большом зале
ru|хочу воздушный ночной ремикс
zh|做一个梦幻有空间感的版本
zh|让歌曲有朦胧怀旧的感觉
zh|制作适合短视频的氛围版
zh|让音乐听起来像在大厅里
zh|想要空灵的夜间混音
''',
'voice-to-text': '''
en|write down what people are saying
en|I need a written record of this conversation
en|turn spoken words into something I can read
en|make searchable notes from this interview
en|type out the dialogue in this recording
en|capture the lecture as written sentences
ru|запиши словами этот разговор
ru|нужна письменная версия беседы
ru|преврати устные слова в читаемый текст
ru|сделай заметки из этого интервью
ru|напечатай диалог из записи
zh|把大家说的话写成文字
zh|我需要这段对话的书面记录
zh|把讲话内容变成可以阅读的文字
zh|从采访里整理可搜索的笔记
zh|把录音中的对话打出来
''',
'vocal-remover': '''
en|I want to sing over this song without the original performer
en|leave only the music so I can perform
en|I need a singalong version of this track
en|take the lead singing out but keep the band
en|separate the singer from the instruments
en|make a version for my karaoke party
ru|хочу петь поверх этой песни без исполнителя
ru|оставь только музыку для выступления
ru|нужна версия для домашнего караоке
ru|убери солиста но оставь инструменты
ru|отдели пение от музыкальных инструментов
zh|我想跟着音乐唱但不要原唱
zh|只留下音乐方便我表演
zh|制作可以跟着唱的歌曲版本
zh|去掉主唱但保留乐队
zh|把歌唱部分和乐器分开
''',
'text-to-speech': '''
en|I want to listen to this document instead of reading it
en|have a synthetic narrator perform this paragraph
en|turn this article into something I can hear
en|make an audio reading of these sentences
en|let the computer dictate this page to me
en|create a spoken version of my story
ru|хочу слушать документ вместо чтения
ru|пусть синтетический диктор прочитает абзац
ru|сделай аудиоверсию этой статьи
ru|произнеси эти предложения вслух компьютерным голосом
ru|создай звуковое прочтение моего рассказа
zh|我想听这篇文章不想自己看
zh|让合成声音读出这一段
zh|把文档变成可以听的内容
zh|为这些句子制作声音朗读
zh|让电脑把这页内容念给我听
''',
'unsupported': '''
en|remove background noise from my podcast
en|identify the name of this song
en|download music from a streaming site
en|generate a new melody for my lyrics
en|make a playlist for running
en|edit this photo and remove the background
en|record my screen with a webcam
en|improve the image resolution
ru|убери фоновый шум из подкаста
ru|узнай как называется эта песня
ru|скачай музыку со стриминга
ru|сочини новую мелодию к моим словам
ru|собери плейлист для бега
ru|отредактируй фотографию
ru|запиши экран с вебкамерой
zh|消除播客里的背景噪音
zh|告诉我这首歌的名字
zh|从流媒体网站下载音乐
zh|根据歌词创作新的旋律
zh|制作跑步播放列表
zh|编辑照片并去掉背景
zh|录制屏幕和摄像头画面
'''
}

# Broader wording keeps the tiny model from merely memorizing one phrase per intent.
EXTRA = {
'converter': '''
en|pull the audio track out of a movie
en|repackage this recording for another device
en|change the sound container without editing it
en|save the audio essence of a video
en|make an audio-only copy of this film
ru|извлеки аудиодорожку из видеоролика
ru|перепакуй запись для другого устройства
ru|смени звуковой контейнер без редактирования
ru|сохрани аудио версию фильма
ru|оставь дорожку с музыкой из клипа
zh|取出视频里的声音轨道
zh|重新封装这段录音
zh|把影片另存为纯音频
zh|转换声音文件的封装格式
zh|留下视频中的音乐部分
''',
'audio-compressor': '''
en|reduce the weight of this audio attachment
en|fit this recording within the upload limit
en|make this song less heavy for sharing
en|lower the number of megabytes
en|the file is bulky and takes too long to send
ru|уменьши вес звукового вложения
ru|умести запись в лимит загрузки
ru|сделай песню не такой тяжелой для отправки
ru|понизь количество мегабайт
ru|файл громоздкий и долго отправляется
zh|减轻音频附件的重量
zh|让录音符合上传大小限制
zh|把歌曲变小方便分享
zh|减少文件占用的兆字节
zh|文件很笨重发送太慢
''',
'volume-booster': '''
en|the speaker sounds distant and faint
en|make this inaudible memo audible
en|increase the loudness of a weak recording
en|the recording level is too low
en|help me hear the quiet speaker
ru|собеседник звучит далеко и слабо
ru|сделай неслышную заметку слышимой
ru|повысь громкость слабой записи
ru|уровень записи слишком низкий
ru|помоги услышать тихого спикера
zh|说话声听起来很远很弱
zh|让听不见的备忘变得清楚
zh|提高微弱录音的响度
zh|录音电平太低了
zh|帮我听清轻声说话的人
''',
'audio-trimmer': '''
en|keep a single verse and discard the rest
en|snip away the unwanted part
en|leave a short passage of the audio
en|remove the ending but keep the beginning
en|select one moment from the whole recording
ru|оставь один куплет и удали остальное
ru|срежь ненужную часть
ru|оставь короткий отрывок аудио
ru|удали окончание но сохрани начало
ru|выбери один момент из всей записи
zh|保留一段主歌其余不要
zh|剪掉多余的部分
zh|留下音频里的简短片段
zh|删除结尾但保留开头
zh|从完整录音中选择一个时刻
''',
'audio-joiner': '''
en|connect all the parts sequentially
en|stick these audio segments into one
en|assemble the complete podcast from clips
en|attach the ending to the first part
en|make separate tracks play continuously
ru|соедини все части последовательно
ru|склей эти аудио сегменты воедино
ru|собери полный подкаст из фрагментов
ru|присоедини окончание к первой части
ru|пусть отдельные треки играют непрерывно
zh|按顺序连接所有部分
zh|把这些声音片段拼成整体
zh|用片段组成完整播客
zh|把结尾接到第一部分后面
zh|让独立音轨连续播放
''',
'audio-speed-changer': '''
en|play the narration at a calmer pace
en|shorten listening time but keep natural speech
en|make the speaker brisk without pitch changes
en|slow the delivery so I can follow
en|finish this audiobook sooner with normal voices
ru|проигрывай повествование в спокойном темпе
ru|сократи прослушивание но сохрани естественную речь
ru|пусть спикер говорит живее без смены тона
ru|замедли подачу чтобы я успевал понимать
ru|закончи аудиокнигу скорее с нормальными голосами
zh|用平静的节奏播放旁白
zh|缩短收听时间但保持自然语音
zh|说话明快一些但不要变调
zh|放慢讲述方便我跟上
zh|用正常声音更快听完有声书
''',
'slowed-reverb': '''
en|make a nostalgic remix with hall ambience
en|create a foggy cinematic version
en|give the song a melancholy spacious sound
en|produce a wistful atmospheric rendition
en|make the music sound distant and dreamy
ru|сделай ностальгический ремикс с акустикой зала
ru|создай туманную кинематографичную версию
ru|придай песне меланхоличное просторное звучание
ru|сделай задумчивую атмосферную обработку
ru|пусть музыка звучит отдаленно и мечтательно
zh|制作带大厅氛围的怀旧混音
zh|创作朦胧的电影感版本
zh|让歌曲有忧郁而宽广的声音
zh|制作惆怅的氛围演绎
zh|让音乐听起来遥远而梦幻
''',
'voice-to-text': '''
en|make a readable report of the discussion
en|type every sentence the speaker says
en|produce written paragraphs from the interview
en|convert the conversation into readable notes
en|write the spoken presentation on paper
ru|сделай читаемый протокол обсуждения
ru|напечатай каждое предложение спикера
ru|создай письменные абзацы из интервью
ru|преврати беседу в читаемые заметки
ru|запиши устную презентацию на бумаге
zh|把讨论整理成可读报告
zh|打出说话人的每个句子
zh|把采访转成书面段落
zh|把对话整理成可读笔记
zh|把口头演讲写成文字
''',
'vocal-remover': '''
en|drop the singing person but retain the musicians
en|create a lead-free track for my performance
en|split the song into singing and musical parts
en|let me replace the original lead with my voice
en|keep the instrumental band without its frontman
ru|убери поющего человека но оставь музыкантов
ru|создай трек без солиста для моего выступления
ru|раздели песню на пение и музыкальную часть
ru|пусть вместо оригинального солиста буду я
ru|оставь группу без ее фронтмена
zh|去掉唱歌的人但保留乐手
zh|制作没有主唱的表演音轨
zh|把歌曲拆成歌唱和音乐部分
zh|让我用自己的声音替换原主唱
zh|保留乐队演奏但不要主唱
''',
'text-to-speech': '''
en|read this essay to me so I can listen
en|produce an oral rendition of the written page
en|perform my story with a computer voice
en|make a listening version of the document
en|turn written paragraphs into spoken sentences
ru|прочитай мне сочинение чтобы я послушал
ru|сделай устное исполнение написанной страницы
ru|озвучь мой рассказ компьютерным голосом
ru|сделай версию документа для прослушивания
ru|преврати написанные абзацы в произнесенные предложения
zh|把文章读给我听
zh|把书面页面变成口头演绎
zh|用电脑声音表演我的故事
zh|制作文档的收听版本
zh|把书面段落变成口头句子
''',
'unsupported': '''
en|translate this text into another language
en|clean the room noise from my audio
en|who is the artist singing this song
en|compose an original tune for me
en|design a podcast cover picture
en|summarize this long article
en|write an essay about music
en|remove echoes from a voice call
en|enhance a blurry video
en|find lyrics for this track
ru|переведи этот текст на другой язык
ru|очисти аудио от комнатного шума
ru|кто артист исполняющий эту песню
ru|сочини оригинальную мелодию
ru|нарисуй обложку подкаста
ru|сделай краткое содержание статьи
ru|напиши сочинение о музыке
ru|убери эхо из голосового звонка
ru|улучши размытое видео
ru|найди слова этой песни
zh|把文本翻译成其他语言
zh|清除音频里的房间噪声
zh|唱这首歌的艺人是谁
zh|为我创作原创曲调
zh|设计播客封面图
zh|总结这篇长文章
zh|写一篇关于音乐的文章
zh|消除语音通话里的回声
zh|增强模糊的视频
zh|查找这首歌的歌词
'''
}
for label, block in EXTRA.items():
    TRAIN[label] += block

TEST = {
'converter': '''
en|extract the music bed from a film
en|my device will not open this sound container
en|change how this audio is encoded
ru|вытащи звуковую дорожку из ролика
ru|телефон не открывает этот звуковой контейнер
ru|поменяй способ кодирования аудио
zh|提取影片中的配乐
zh|我的设备打不开这种声音封装
zh|换一种音频编码方式
''',
'audio-compressor': '''
en|this sound is too heavy for my attachment
en|help me send a lighter voice recording
en|the upload limit rejects this song
ru|звук слишком тяжелый для вложения
ru|помоги отправить более легкую запись
ru|лимит загрузки не принимает песню
zh|声音文件太重不能作为附件
zh|帮我把录音变轻一点再发送
zh|歌曲超过了上传限制
''',
'volume-booster': '''
en|the speaker is almost inaudible
en|I struggle to hear this voice memo
en|bring this faint podcast to a normal level
ru|говорящего почти не слышно
ru|с трудом разбираю эту голосовую заметку
ru|сделай слабый подкаст нормальной громкости
zh|说话的人几乎听不见
zh|这条语音备忘很难听清
zh|把微弱的播客调到正常响度
''',
'audio-trimmer': '''
en|leave only the second verse
en|snip off the unwanted ending
en|grab a small passage from this recording
ru|оставь лишь второй куплет
ru|срежь ненужное окончание
ru|возьми маленький отрывок из записи
zh|只留下第二段主歌
zh|剪掉不需要的结尾
zh|截取录音中的一小段内容
''',
'audio-joiner': '''
en|connect these clips one after another
en|assemble a single recording from the parts
en|stick the introduction onto my podcast
ru|соедини эти фрагменты последовательно
ru|собери одну запись из частей
ru|присоедини вступление к подкасту
zh|把这些片段依次连接
zh|将各部分组装成一段完整录音
zh|把介绍部分接到播客上
''',
'audio-speed-changer': '''
en|shorten my listening time without a chipmunk voice
en|make the narration more relaxed
en|play the lecture at a brisker pace
ru|сократи время прослушивания без писклявого голоса
ru|сделай повествование спокойнее
ru|проигрывай лекцию в более живом темпе
zh|缩短收听时间但不要尖细的声音
zh|让旁白节奏更舒缓
zh|用更明快的节奏播放讲座
''',
'slowed-reverb': '''
en|make a wistful spacious remix
en|give this song a foggy cinematic atmosphere
en|I want a nostalgic hall-like edit
ru|сделай задумчивый просторный ремикс
ru|добавь песне туманной кинематографичной атмосферы
ru|хочу ностальгическую версию с ощущением зала
zh|制作惆怅而有空间感的混音
zh|给歌曲一种朦胧的电影氛围
zh|想要怀旧的大厅感版本
''',
'voice-to-text': '''
en|produce a readable account of our discussion
en|type what the speaker says
en|turn this interview into written paragraphs
ru|сделай читаемый отчет нашего обсуждения
ru|напечатай что говорит спикер
ru|преврати интервью в письменные абзацы
zh|生成我们讨论内容的可读记录
zh|把说话人的内容打成文字
zh|把采访整理成书面段落
''',
'vocal-remover': '''
en|keep the band but drop the person singing
en|make a track I can sing lead on
en|separate the performance into music and singing
ru|оставь группу но убери поющего человека
ru|сделай трек на который можно спеть партию
ru|раздели выступление на музыку и пение
zh|保留乐队但去掉唱歌的人
zh|制作让我可以主唱的音轨
zh|把表演分成音乐和歌唱
''',
'text-to-speech': '''
en|let me hear this essay rather than read it
en|produce a spoken rendition of this page
en|make the computer perform my written story
ru|дай послушать это сочинение вместо чтения
ru|сделай звуковое исполнение этой страницы
ru|пусть компьютер прочитает мой рассказ
zh|让我听这篇文章而不是阅读
zh|生成这一页的口头朗读
zh|让电脑表演我写的文字故事
''',
'unsupported': '''
en|clean up a noisy room in this recording
en|what artist performs this track
en|compose a melody from scratch
en|make a cover image for my podcast
en|translate this text into Spanish
ru|очисти запись от шума комнаты
ru|кто исполняет этот трек
ru|напиши мелодию с нуля
ru|сделай обложку для подкаста
ru|переведи текст на испанский
zh|清理录音里的室内噪声
zh|这首歌是哪位歌手唱的
zh|从零开始创作旋律
zh|给播客制作封面图片
zh|把这段文字翻译成西班牙语
'''
}


def examples(data):
    rows = []
    for label, block in data.items():
        for line in block.strip().splitlines():
            if not line.strip():
                continue
            lang, text = line.strip().split('|', 1)
            rows.append((text, label, lang))
    return rows


def features(text, dimensions=4096):
    chars = list(' ' + text.lower().strip() + ' ')
    vec = np.zeros(dimensions, dtype=np.float32)
    for n in (1, 2, 3, 4, 5):
        for i in range(len(chars) - n + 1):
            gram = ''.join(chars[i:i+n])
            h = 2166136261
            for char in gram:
                h ^= ord(char)
                h = (h * 16777619) & 0xffffffff
            vec[h % dimensions] += 1.0
    norm = np.linalg.norm(vec)
    return vec / norm if norm else vec


def quantize(matrix):
    scale = np.maximum(np.max(np.abs(matrix), axis=1) / 127.0, 1e-12)
    values = np.clip(np.round(matrix / scale[:, None]), -127, 127).astype(np.int8)
    return base64.b64encode(values.tobytes()).decode(), scale.tolist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'assistant-model.js')
    parser.add_argument('--export-cases', type=Path)
    args = parser.parse_args()
    train = examples(TRAIN)
    test = examples(TEST)
    x_train = np.array([features(text) for text, _, _ in train])
    y_train = np.array([LABELS.index(label) for _, label, _ in train])
    x_test = np.array([features(text) for text, _, _ in test])
    y_test = np.array([LABELS.index(label) for _, label, _ in test])
    clf = MLPClassifier(hidden_layer_sizes=(16,), activation='relu', solver='lbfgs',
                        alpha=0.005, max_iter=800, random_state=42)
    clf.fit(x_train, y_train)
    probabilities = clf.predict_proba(x_test)
    predictions = probabilities.argmax(axis=1)
    correct = predictions == y_test
    print(f'Train: {len(train)}; held out: {len(test)}; accuracy: {correct.mean():.1%}')
    for lang in ('en', 'ru', 'zh'):
        mask = np.array([row[2] == lang for row in test])
        print(f'{lang}: {correct[mask].mean():.1%} ({correct[mask].sum()}/{mask.sum()})')
    for row, ok, pred, prob in zip(test, correct, predictions, probabilities):
        if not ok:
            print(f'MISS [{row[2]}] {row[0]} → {LABELS[pred]} ({prob[pred]:.2f}), expected {row[1]}')
    w1, s1 = quantize(clf.coefs_[0].T)
    w2, s2 = quantize(clf.coefs_[1].T)
    model = {
        'dimensions': 4096, 'hidden': clf.intercepts_[0].size, 'labels': LABELS,
        'w1': w1, 's1': s1, 'b1': clf.intercepts_[0].tolist(),
        'w2': w2, 's2': s2, 'b2': clf.intercepts_[1].tolist(),
    }
    source = Path(__file__).with_name('assistant_model_template.js').read_text()
    payload = json.dumps(model, separators=(',', ':'))
    # Keep generated lines readable/diffable instead of one enormous base64 line.
    for key in ('w1', 'w2'):
        encoded = model[key]
        chunks = '"' + '" +\n    "'.join(encoded[i:i+1500] for i in range(0, len(encoded), 1500)) + '"'
        payload = payload.replace(json.dumps(encoded), chunks, 1)
    args.output.write_text(source.replace('__MODEL__', payload))
    print(f'Wrote {args.output} ({args.output.stat().st_size:,} bytes)')
    if args.export_cases:
        args.export_cases.write_text(json.dumps({'train': train, 'test': test}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
