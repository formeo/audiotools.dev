#!/usr/bin/env python3
"""Build the format pages (/mp4-to-mp3/, /video-to-mp3/, /mp3-to-wav/, /wav-to-mp3/ and their /zh/ versions).

    python3 scripts/build_landing.py   # then runs scripts/seo_sync.py (FAQ JSON-LD)

Each page is the converter page (converter/index.html or zh/converter/index.html) with its own head, heading,
text and FAQ, and the output format chosen in advance (<body data-default-format>). The converter code is not
copied by hand: after changing the converter, run this script again.
"""
import re
import subprocess
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://audiotools.dev'

# Shared numbers used in the copy (MP3 size = bitrate × time; WAV = 44.1 kHz × 16 bit × 2 channels)
# 128 kbps ≈ 0.96 MB/min, 192 kbps ≈ 1.44 MB/min, 320 kbps = 2.4 MB/min, CD-quality WAV ≈ 10.6 MB/min.

PAGES = {
'mp4-to-mp3': {'format': 'mp3', 'en': {
    'title': 'MP4 to MP3 Converter — Free, No Upload | AudioTools.dev',
    'description': 'Convert MP4 to MP3 in your browser: drop the video, keep MP3, download. The video is never uploaded. Free, no sign-up, works with several files at once.',
    'keywords': 'mp4 to mp3, mp4 to mp3 converter, convert mp4 to mp3, mp4 to mp3 free, extract audio from mp4, mp4 audio to mp3',
    'og_title': 'MP4 to MP3 Converter — Free, No Upload',
    'app': 'MP4 to MP3 Converter',
    'h1': 'MP4 to MP3 Converter',
    'lead': 'Take the sound from an MP4 video and save it as MP3, right in your browser. Nothing is uploaded.',
    'steps_title': 'How to convert MP4 to MP3',
    'steps': [('Drop your MP4', 'Or several of them: they are converted one after another.'),
              ('Keep MP3 selected', 'Pick a bitrate; 192 kbps is high quality.'),
              ('Download the MP3', 'The video never leaves your device.')],
    'body': '''<h2>Convert MP4 to MP3 online, free</h2>
            <p>To convert MP4 to MP3, drop the video on the box above, keep MP3 selected and click “Convert”. The converter reads the audio track in your browser and saves it as an MP3 at the bitrate you choose (128–320 kbps). The video is never uploaded, and the original file stays as it was.</p>
            <h3>What happens to the picture?</h3>
            <p>Only the sound is kept. The video track is skipped, so the MP3 is a fraction of the MP4's size: about 1.4 MB per minute at 192 kbps, whatever the video's resolution.</p>
            <h3>Which bitrate to choose</h3>
            <ul>
                <li>128 kbps — speech, lectures, podcasts (about 1 MB per minute)</li>
                <li>192 kbps — music in high quality, the default</li>
                <li>320 kbps — maximum quality (2.4 MB per minute)</li>
            </ul>
            <h3>Long videos and many files</h3>
            <p>The file is read in pieces instead of being loaded whole, so long videos and files of several hundred megabytes work in current browsers. Drop several MP4s at once to get each MP3 separately or all of them in a ZIP.</p>
            <h3>Videos from iPhone and Android</h3>
            <p>Phone videos are MP4 or MOV with AAC sound. Chrome, Edge and Safari read them on computers and phones; Firefox depends on the codecs your system provides.</p>''',
    'faq_title': 'Frequently Asked Questions',
    'faq': [('How do I convert MP4 to MP3?', 'Drop the MP4 on this page, keep MP3 selected, choose a bitrate and click Convert. Download the MP3 when it is ready; the video is converted in your browser.'),
            ('Is my MP4 uploaded anywhere?', 'No. The audio is read and encoded in your browser, so the video never leaves your device.'),
            ('Does converting MP4 to MP3 reduce quality?', 'The sound in an MP4 is usually AAC, and converting it to MP3 encodes it again. At 192 kbps or more the difference is hard to hear. For no further loss, choose WAV or FLAC instead of MP3.'),
            ('Can I convert several MP4 files at once?', 'Yes. Drop several videos: they are converted one after another, and you can download each MP3 or all of them as a ZIP.'),
            ('Does it work on an iPhone?', 'Yes. Open this page in Safari, pick the video from your photos or files and download the MP3.')],
}, 'zh': {
    'title': 'MP4 转 MP3 — 免费在线转换，无需上传 | AudioTools.dev',
    'description': '在浏览器中把 MP4 转为 MP3：拖入视频，保持 MP3，下载即可。视频不会被上传。免费，无需注册，可一次转换多个文件。',
    'keywords': 'MP4转MP3, MP4转MP3在线, 视频转MP3, 提取MP4音频, 免费MP4转MP3, MP4音频提取',
    'og_title': 'MP4 转 MP3 — 免费在线转换，无需上传',
    'app': 'MP4 转 MP3 转换器',
    'h1': 'MP4 转 MP3',
    'lead': '在浏览器中提取 MP4 视频的声音并保存为 MP3，不上传任何内容。',
    'steps_title': '如何把 MP4 转为 MP3',
    'steps': [('拖入 MP4', '也可以一次拖入多个，它们会依次转换。'), ('保持选择 MP3', '选择码率；192 kbps 即为高品质。'), ('下载 MP3', '视频不会离开您的设备。')],
    'body': '''<h2>免费在线把 MP4 转为 MP3</h2>
            <p>要把 MP4 转为 MP3，只需把视频拖到上方的框中，保持选择 MP3，然后点击“转换”。转换器会在浏览器中读取音轨，并按您选择的码率（128–320 kbps）保存为 MP3。视频不会被上传，原文件保持不变。</p>
            <h3>画面会怎样？</h3>
            <p>只保留声音，视频轨会被跳过，因此 MP3 只有 MP4 的一小部分大小：192 kbps 约每分钟 1.4 MB，与视频分辨率无关。</p>
            <h3>如何选择码率</h3>
            <ul>
                <li>128 kbps — 语音、讲座、播客（约每分钟 1 MB）</li>
                <li>192 kbps — 高品质音乐，默认选项</li>
                <li>320 kbps — 最高品质（每分钟 2.4 MB）</li>
            </ul>
            <h3>长视频和多个文件</h3>
            <p>文件是分块读取的，而不是一次性载入，因此在新版浏览器中，长视频和几百 MB 的文件也能处理。一次拖入多个 MP4，可以分别下载每个 MP3，也可以打包成 ZIP 下载。</p>
            <h3>iPhone 和 Android 拍的视频</h3>
            <p>手机视频是带 AAC 声音的 MP4 或 MOV。Chrome、Edge 和 Safari 在电脑和手机上都能读取；Firefox 取决于系统提供的编解码器。</p>''',
    'faq_title': '常见问题',
    'faq': [('如何把 MP4 转为 MP3？', '把 MP4 拖到本页，保持选择 MP3，选择码率后点击“转换”。完成后下载 MP3；视频在您的浏览器中转换。'),
            ('我的 MP4 会被上传吗？', '不会。音频在您的浏览器中读取和编码，视频不会离开您的设备。'),
            ('MP4 转 MP3 会降低音质吗？', 'MP4 里的声音通常是 AAC，转成 MP3 会再编码一次。在 192 kbps 及以上很难听出区别。如果不想再有任何损失，请选择 WAV 或 FLAC 而不是 MP3。'),
            ('可以一次转换多个 MP4 吗？', '可以。拖入多个视频，它们会依次转换，可以单独下载每个 MP3，也可以打包成 ZIP 下载。'),
            ('在 iPhone 上能用吗？', '能。在 Safari 中打开本页，从照片或文件中选择视频，然后下载 MP3。')],
}},

'video-to-mp3': {'format': 'mp3', 'en': {
    'title': 'Video to MP3 Converter — Extract Audio Free | AudioTools.dev',
    'description': 'Extract the audio from MP4, MOV, MKV or WebM videos and save it as MP3, M4A or WAV. Runs in your browser, nothing is uploaded. Free, no sign-up.',
    'keywords': 'video to mp3, extract audio from video, video to audio converter, mov to mp3, mkv to mp3, webm to mp3, convert video to mp3 free',
    'og_title': 'Video to MP3 — Extract Audio Free, No Upload',
    'app': 'Video to MP3 Converter',
    'h1': 'Video to MP3',
    'lead': 'Pull the audio out of any video — MP4, MOV, MKV, WebM — and save it as MP3. Free, nothing is uploaded.',
    'steps_title': 'How to extract audio from a video',
    'steps': [('Drop the video', 'MP4, MOV, MKV, WebM or M4V, one or several.'),
              ('Choose the format', 'MP3 for listening anywhere, M4A for small files, WAV or FLAC for editing.'),
              ('Download the audio', 'Everything happens in your browser.')],
    'body': '''<h2>Extract audio from video online</h2>
            <p>To get the audio from a video, drop the file on the box above and click “Convert”. The converter keeps only the sound and saves it as MP3 by default, or as M4A, WAV or FLAC. It runs in your browser, so the video is never uploaded.</p>
            <h3>Supported video formats</h3>
            <p>MP4, MOV (iPhone), MKV, WebM and M4V. The sound inside can be AAC, MP3, Opus or Vorbis. Opus, Vorbis and MP3 work in every current browser; AAC, the usual sound in phone videos, is read by Chrome, Edge and Safari, and by Firefox where your system provides the codec.</p>
            <h3>Common uses</h3>
            <ul>
                <li>A talk, lecture or webinar recording to listen to on the go</li>
                <li>The music or sound from a clip</li>
                <li>Voice notes that were recorded as video</li>
                <li>A podcast episode from a video recording</li>
            </ul>
            <h3>MP3, M4A, WAV or FLAC?</h3>
            <p>MP3 plays everywhere. M4A (AAC) is a little smaller at the same quality. WAV and FLAC are lossless, which is what you want if you will edit the audio afterwards.</p>
            <h3>Videos from websites</h3>
            <p>The converter works with video files on your device. It does not download videos from YouTube or other sites.</p>''',
    'faq_title': 'Frequently Asked Questions',
    'faq': [('How do I extract audio from a video?', 'Drop the video on this page, choose MP3 (or M4A, WAV, FLAC) and click Convert. The sound is saved as a new file; the video is converted in your browser.'),
            ('Which video formats work?', 'MP4, MOV, MKV, WebM and M4V. Phone videos with AAC sound work in Chrome, Edge and Safari; Firefox depends on your system.'),
            ('Can I get the audio as M4A or WAV instead of MP3?', 'Yes. Choose M4A, WAV or FLAC before converting. WAV and FLAC are lossless.'),
            ('Is my video uploaded?', 'No. The video is read in your browser and never leaves your device.'),
            ('Can I paste a YouTube link?', 'No. The converter works with video files on your device; it does not download from YouTube or other websites.')],
}, 'zh': {
    'title': '视频转 MP3 — 免费在线提取音频 | AudioTools.dev',
    'description': '从 MP4、MOV、MKV 或 WebM 视频中提取音频，保存为 MP3、M4A 或 WAV。在浏览器中运行，不上传任何内容。免费，无需注册。',
    'keywords': '视频转MP3, 视频提取音频, 视频转音频, MOV转MP3, MKV转MP3, WebM转MP3, 免费视频转MP3',
    'og_title': '视频转 MP3 — 免费在线提取音频，无需上传',
    'app': '视频转 MP3 转换器',
    'h1': '视频转 MP3',
    'lead': '从任意视频（MP4、MOV、MKV、WebM）中提取声音并保存为 MP3。免费，不上传任何内容。',
    'steps_title': '如何从视频中提取音频',
    'steps': [('拖入视频', 'MP4、MOV、MKV、WebM 或 M4V，一个或多个。'), ('选择格式', 'MP3 到处都能播放，M4A 文件更小，WAV 或 FLAC 适合编辑。'), ('下载音频', '一切都在浏览器中完成。')],
    'body': '''<h2>在线从视频中提取音频</h2>
            <p>要获取视频中的音频，只需把文件拖到上方的框中并点击“转换”。转换器只保留声音，默认保存为 MP3，也可以保存为 M4A、WAV 或 FLAC。它在浏览器中运行，视频不会被上传。</p>
            <h3>支持的视频格式</h3>
            <p>MP4、MOV（iPhone）、MKV、WebM 和 M4V。其中的声音可以是 AAC、MP3、Opus 或 Vorbis。Opus、Vorbis 和 MP3 在所有新版浏览器中都可用；手机视频常见的 AAC 声音可由 Chrome、Edge 和 Safari 读取，Firefox 则取决于系统是否提供该编解码器。</p>
            <h3>常见用途</h3>
            <ul>
                <li>把演讲、讲座或网络研讨会的录像变成随时可听的音频</li>
                <li>提取短片中的音乐或声音</li>
                <li>把录成视频的语音备忘转为音频</li>
                <li>从视频录像中做出一期播客</li>
            </ul>
            <h3>MP3、M4A、WAV 还是 FLAC？</h3>
            <p>MP3 到处都能播放。M4A（AAC）在同等音质下略小。WAV 和 FLAC 是无损格式，如果之后还要编辑音频，就选它们。</p>
            <h3>网站上的视频</h3>
            <p>转换器处理的是您设备上的视频文件，不会从 YouTube 或其他网站下载视频。</p>''',
    'faq_title': '常见问题',
    'faq': [('如何从视频中提取音频？', '把视频拖到本页，选择 MP3（或 M4A、WAV、FLAC）后点击“转换”。声音会保存为一个新文件；视频在您的浏览器中转换。'),
            ('支持哪些视频格式？', 'MP4、MOV、MKV、WebM 和 M4V。带 AAC 声音的手机视频可在 Chrome、Edge 和 Safari 中使用；Firefox 取决于您的系统。'),
            ('可以把音频保存为 M4A 或 WAV 而不是 MP3 吗？', '可以。转换前选择 M4A、WAV 或 FLAC 即可。WAV 和 FLAC 是无损格式。'),
            ('我的视频会被上传吗？', '不会。视频在您的浏览器中读取，不会离开您的设备。'),
            ('可以粘贴 YouTube 链接吗？', '不可以。转换器处理的是您设备上的视频文件，不会从 YouTube 或其他网站下载。')],
}},

'mp3-to-wav': {'format': 'wav', 'en': {
    'title': 'MP3 to WAV Converter — Free, No Upload | AudioTools.dev',
    'description': 'Convert MP3 to WAV (16-bit PCM) in your browser for editors, samplers and apps that need WAV. Free, no upload, convert one file or a whole batch.',
    'keywords': 'mp3 to wav, mp3 to wav converter, convert mp3 to wav, mp3 to wav free, mp3 to wav online, mp3 to wav 16 bit',
    'og_title': 'MP3 to WAV Converter — Free, No Upload',
    'app': 'MP3 to WAV Converter',
    'h1': 'MP3 to WAV Converter',
    'lead': 'Turn MP3 into uncompressed WAV for editors, samplers and apps that need WAV. Free, in your browser.',
    'steps_title': 'How to convert MP3 to WAV',
    'steps': [('Drop your MP3', 'One file or many at once.'),
              ('Keep WAV selected', 'It is already chosen on this page.'),
              ('Download the WAV', 'Converted on your device, never uploaded.')],
    'body': '''<h2>Convert MP3 to WAV online, free</h2>
            <p>To convert MP3 to WAV, drop the MP3 on the box above, keep WAV selected and click “Convert”. You get an uncompressed 16-bit PCM WAV with the same sample rate and channels as the MP3. It is made in your browser; nothing is uploaded.</p>
            <h3>Why convert MP3 to WAV?</h3>
            <ul>
                <li>Audio editors and DAWs that work best with WAV</li>
                <li>Samplers, drum machines and DJ gear that only load WAV</li>
                <li>Apps, phone systems and game engines that ask for WAV files</li>
                <li>Editing without encoding to MP3 again after every save</li>
            </ul>
            <h3>Will the WAV sound better?</h3>
            <p>No. MP3 is lossy: what it dropped when it was made cannot come back. The WAV keeps exactly the sound the MP3 had, no better and no worse. What WAV gives you is that further editing and saving loses nothing more.</p>
            <h3>How big will the WAV be?</h3>
            <p>About 10.6 MB per minute for CD-quality stereo (44.1 kHz, 16-bit), roughly ten times the MP3. A 4-minute song becomes about 42 MB.</p>''',
    'faq_title': 'Frequently Asked Questions',
    'faq': [('How do I convert MP3 to WAV?', 'Drop the MP3 on this page, keep WAV selected and click Convert, then download the WAV. The conversion happens in your browser.'),
            ('Does converting MP3 to WAV improve quality?', 'No. The WAV has exactly the sound of the MP3; it only stops further loss when you edit and save again.'),
            ('What bit depth and sample rate is the WAV?', '16-bit PCM, with the same sample rate and number of channels as the original MP3.'),
            ('Can I convert many MP3 files to WAV at once?', 'Yes. Drop them all: they are converted one after another, and you can download each WAV or all of them as a ZIP.'),
            ('Is my MP3 uploaded?', 'No. The file is converted in your browser and never leaves your device.')],
}, 'zh': {
    'title': 'MP3 转 WAV — 免费在线转换，无需上传 | AudioTools.dev',
    'description': '在浏览器中把 MP3 转为 WAV（16 位 PCM），供需要 WAV 的编辑软件、采样器和应用使用。免费，无需上传，可单个或批量转换。',
    'keywords': 'MP3转WAV, MP3转WAV在线, MP3转WAV免费, MP3转换WAV, 16位WAV',
    'og_title': 'MP3 转 WAV — 免费在线转换，无需上传',
    'app': 'MP3 转 WAV 转换器',
    'h1': 'MP3 转 WAV',
    'lead': '把 MP3 转为无压缩的 WAV，供需要 WAV 的编辑软件、采样器和应用使用。免费，在浏览器中完成。',
    'steps_title': '如何把 MP3 转为 WAV',
    'steps': [('拖入 MP3', '一个文件或一次多个。'), ('保持选择 WAV', '本页已经为您选好。'), ('下载 WAV', '在您的设备上转换，绝不上传。')],
    'body': '''<h2>免费在线把 MP3 转为 WAV</h2>
            <p>要把 MP3 转为 WAV，只需把 MP3 拖到上方的框中，保持选择 WAV，然后点击“转换”。您会得到一个无压缩的 16 位 PCM WAV，采样率和声道与 MP3 相同。它在浏览器中生成，不上传任何内容。</p>
            <h3>为什么要把 MP3 转为 WAV？</h3>
            <ul>
                <li>更适合使用 WAV 的音频编辑器和 DAW</li>
                <li>只能载入 WAV 的采样器、鼓机和 DJ 设备</li>
                <li>要求 WAV 文件的应用、电话系统和游戏引擎</li>
                <li>编辑时不必每次保存都重新编码为 MP3</li>
            </ul>
            <h3>WAV 会更好听吗？</h3>
            <p>不会。MP3 是有损格式，编码时丢掉的部分无法恢复。WAV 只是完整保留 MP3 原有的声音，不会更好也不会更差。它的好处是之后再编辑、保存时不会继续损失。</p>
            <h3>WAV 会有多大？</h3>
            <p>CD 音质立体声（44.1 kHz、16 位）约每分钟 10.6 MB，大约是 MP3 的十倍。一首 4 分钟的歌约为 42 MB。</p>''',
    'faq_title': '常见问题',
    'faq': [('如何把 MP3 转为 WAV？', '把 MP3 拖到本页，保持选择 WAV，点击“转换”，然后下载 WAV。转换在您的浏览器中完成。'),
            ('MP3 转 WAV 能提高音质吗？', '不能。WAV 的声音与 MP3 完全相同，只是在之后编辑、保存时不会继续损失。'),
            ('WAV 的位深和采样率是多少？', '16 位 PCM，采样率和声道数与原 MP3 相同。'),
            ('可以一次把多个 MP3 转为 WAV 吗？', '可以。全部拖入即可，它们会依次转换，可以单独下载每个 WAV，也可以打包成 ZIP 下载。'),
            ('我的 MP3 会被上传吗？', '不会。文件在您的浏览器中转换，不会离开您的设备。')],
}},

'wav-to-mp3': {'format': 'mp3', 'en': {
    'title': 'WAV to MP3 Converter — Free, No Upload | AudioTools.dev',
    'description': 'Convert WAV to MP3 in your browser and make files about 10 times smaller. Choose 128–320 kbps, convert one file or a folder at once. Free, no upload.',
    'keywords': 'wav to mp3, wav to mp3 converter, convert wav to mp3, wav to mp3 free, wav to mp3 online, compress wav to mp3',
    'og_title': 'WAV to MP3 Converter — Free, No Upload',
    'app': 'WAV to MP3 Converter',
    'h1': 'WAV to MP3 Converter',
    'lead': 'Make big WAV files about ten times smaller as MP3. Choose the bitrate and convert in your browser.',
    'steps_title': 'How to convert WAV to MP3',
    'steps': [('Drop your WAV', 'One file or a whole folder of them.'),
              ('Choose a bitrate', '128 kbps for speech, 192 kbps for music.'),
              ('Download the MP3', 'Converted on your device, never uploaded.')],
    'body': '''<h2>Convert WAV to MP3 online, free</h2>
            <p>To convert WAV to MP3, drop the WAV on the box above, keep MP3 selected, choose a bitrate and click “Convert”. The MP3 is encoded in your browser with the LAME encoder compiled to WebAssembly; nothing is uploaded.</p>
            <h3>How much smaller will it be?</h3>
            <p>CD-quality WAV takes about 10.6 MB per minute. As MP3 it takes about 1 MB per minute at 128 kbps (11 times smaller), 1.4 MB at 192 kbps (7 times) and 2.4 MB at 320 kbps (4 times).</p>
            <h3>Which bitrate to choose</h3>
            <ul>
                <li>128 kbps — speech, voice recordings, podcasts</li>
                <li>192 kbps — music in high quality, the default</li>
                <li>320 kbps — maximum quality, for archiving music as MP3</li>
            </ul>
            <h3>Recordings from voice recorders and studios</h3>
            <p>Voice recorders, field recorders and DAWs save WAV, which is too big to send. Converting to MP3 makes recordings easy to email or share; drop a whole folder of them to get all the MP3s in one ZIP.</p>
            <p>To pick a size rather than a bitrate, use the <a href="/audio-compressor/">audio compressor</a>, which shows the estimated size before you start.</p>''',
    'faq_title': 'Frequently Asked Questions',
    'faq': [('How do I convert WAV to MP3?', 'Drop the WAV on this page, keep MP3 selected, choose a bitrate and click Convert, then download the MP3. The conversion happens in your browser.'),
            ('How much smaller will the MP3 be?', 'About 11 times smaller at 128 kbps, 7 times at 192 kbps and 4 times at 320 kbps, compared with CD-quality WAV.'),
            ('Which bitrate should I choose?', '128 kbps for speech, 192 kbps for music, 320 kbps if you want the best quality MP3 can give.'),
            ('Can I convert a whole folder of WAV files?', 'Yes. Select or drop all the files: they are converted one after another, and you can download all the MP3s as a ZIP.'),
            ('Is my WAV uploaded?', 'No. The file is converted in your browser and never leaves your device.')],
}, 'zh': {
    'title': 'WAV 转 MP3 — 免费在线转换，无需上传 | AudioTools.dev',
    'description': '在浏览器中把 WAV 转为 MP3，文件约小 10 倍。可选 128–320 kbps，可一次转换整个文件夹。免费，无需上传。',
    'keywords': 'WAV转MP3, WAV转MP3在线, WAV转MP3免费, WAV转换MP3, WAV压缩成MP3',
    'og_title': 'WAV 转 MP3 — 免费在线转换，无需上传',
    'app': 'WAV 转 MP3 转换器',
    'h1': 'WAV 转 MP3',
    'lead': '把体积很大的 WAV 转为 MP3，文件约小十倍。选择码率，在浏览器中完成转换。',
    'steps_title': '如何把 WAV 转为 MP3',
    'steps': [('拖入 WAV', '一个文件或整个文件夹。'), ('选择码率', '语音选 128 kbps，音乐选 192 kbps。'), ('下载 MP3', '在您的设备上转换，绝不上传。')],
    'body': '''<h2>免费在线把 WAV 转为 MP3</h2>
            <p>要把 WAV 转为 MP3，只需把 WAV 拖到上方的框中，保持选择 MP3，选择码率后点击“转换”。MP3 由编译为 WebAssembly 的 LAME 编码器在浏览器中编码，不上传任何内容。</p>
            <h3>会小多少？</h3>
            <p>CD 音质的 WAV 约每分钟 10.6 MB。转为 MP3 后，128 kbps 约每分钟 1 MB（小 11 倍），192 kbps 约 1.4 MB（小 7 倍），320 kbps 为 2.4 MB（小 4 倍）。</p>
            <h3>如何选择码率</h3>
            <ul>
                <li>128 kbps — 语音、录音、播客</li>
                <li>192 kbps — 高品质音乐，默认选项</li>
                <li>320 kbps — 最高品质，适合以 MP3 存档音乐</li>
            </ul>
            <h3>录音笔和录音室的录音</h3>
            <p>录音笔、外录设备和 DAW 保存的是 WAV，体积太大不便发送。转为 MP3 后，录音就能轻松通过邮件发送或分享；一次拖入整个文件夹，即可把所有 MP3 打包成一个 ZIP。</p>
            <p>如果想按文件大小而不是码率来选择，请使用<a href="/zh/audio-compressor/">音频压缩</a>，它会在开始前显示预计大小。</p>''',
    'faq_title': '常见问题',
    'faq': [('如何把 WAV 转为 MP3？', '把 WAV 拖到本页，保持选择 MP3，选择码率后点击“转换”，然后下载 MP3。转换在您的浏览器中完成。'),
            ('MP3 会小多少？', '与 CD 音质的 WAV 相比，128 kbps 约小 11 倍，192 kbps 约小 7 倍，320 kbps 约小 4 倍。'),
            ('应该选择什么码率？', '语音选 128 kbps，音乐选 192 kbps，想要 MP3 能达到的最佳音质就选 320 kbps。'),
            ('可以一次转换整个文件夹的 WAV 吗？', '可以。选择或拖入所有文件，它们会依次转换，可以把所有 MP3 打包成 ZIP 下载。'),
            ('我的 WAV 会被上传吗？', '不会。文件在您的浏览器中转换，不会离开您的设备。')],
}},
}

OTHER = {'en': ('Other conversions', 'All formats'), 'zh': ('其他转换', '全部格式')}
LABEL = {'mp4-to-mp3': ('MP4 to MP3', 'MP4 转 MP3'), 'video-to-mp3': ('Video to MP3', '视频转 MP3'),
         'mp3-to-wav': ('MP3 to WAV', 'MP3 转 WAV'), 'wav-to-mp3': ('WAV to MP3', 'WAV 转 MP3')}


def path(slug, lang):
    return f'/zh/{slug}/' if lang == 'zh' else f'/{slug}/'


def conversions_list(lang, current=None):
    """The format pages as links; used on each format page and on the converter pages."""
    i = 0 if lang == 'en' else 1
    items = [f'<li><a href="{path(s, lang)}">{LABEL[s][i]}</a></li>' for s in PAGES if s != current]
    if current:
        items.append(f'<li><a href="{"/zh/converter/" if lang == "zh" else "/converter/"}">{OTHER[lang][1]}</a></li>')
    return '<ul class="conversions">' + ''.join(items) + '</ul>'


def build(slug, lang):
    page, c = PAGES[slug], PAGES[slug][lang]
    base = ROOT / ('zh/converter' if lang == 'zh' else 'converter') / 'index.html'
    s = base.read_text(encoding='utf-8')
    url, en_url, zh_url = SITE + path(slug, lang), SITE + path(slug, 'en'), SITE + path(slug, 'zh')
    img = f'{SITE}/og/{"zh-" if lang == "zh" else ""}{slug}.png'
    e = lambda v: escape(v, quote=True)

    def sub(pattern, repl, count=1):
        nonlocal s
        s, n = re.subn(pattern, lambda m: repl, s, count=count, flags=re.S)
        assert n, f'{slug}/{lang}: no match for {pattern[:60]}'

    sub(r'<title>[^<]*</title>', f'<title>{escape(c["title"], quote=False)}</title>')
    sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{e(c["description"])}">')
    sub(r'<meta name="keywords" content="[^"]*">', f'<meta name="keywords" content="{e(c["keywords"])}">')
    s = re.sub(r'    <link rel="alternate" hreflang="[^"]+" href="[^"]+">\n', '', s)   # wherever the base page has them
    sub(r'<link rel="canonical" href="[^"]*">\n',
        f'<link rel="canonical" href="{url}">\n    <link rel="alternate" hreflang="en" href="{en_url}">\n'
        f'    <link rel="alternate" hreflang="zh" href="{zh_url}">\n    <link rel="alternate" hreflang="x-default" href="{en_url}">\n')
    for prop, val in [('og:url', url), ('og:title', c['og_title']), ('og:description', c['description']), ('og:image', img), ('og:image:alt', c['og_title'])]:
        sub(rf'<meta property="{prop}" content="[^"]*">', f'<meta property="{prop}" content="{e(val)}">')
    for name, val in [('twitter:title', c['og_title']), ('twitter:description', c['description']), ('twitter:image', img)]:
        sub(rf'<meta name="{name}" content="[^"]*">', f'<meta name="{name}" content="{e(val)}">')
    s = re.sub(r'("@type": "WebApplication",\s*"name": ")[^"]*(",\s*"description": ")[^"]*(",)',
               lambda m: m.group(1) + c['app'] + m.group(2) + c['description'].replace('"', '\\"') + m.group(3), s, count=1)
    sub(r'"url": "https://audiotools\.dev/(?:zh/)?converter/"', f'"url": "{url}"')
    sub(r'<body>', f'<body data-default-format="{page["format"]}">')
    # navigation: no current item; language switch to the other version of this page
    s = re.sub(r'(<a href="(?:/zh)?/converter/") aria-current="page"', r'\1', s)
    sub(r'<a href="[^"]*" class="at-lang"', f'<a href="{path(slug, "zh" if lang == "en" else "en")}" class="at-lang"')
    # heading and lead
    s = re.sub(r'(<section class="hero">.*?)<h1>[^<]*</h1>(\s*)<p>[^<]*</p>',
               lambda m: m.group(1) + f'<h1>{c["h1"]}</h1>' + m.group(2) + f'<p>{c["lead"]}</p>', s, count=1, flags=re.S)
    # everything under the panel
    steps = ''.join(f'''
                <div class="step">
                    <div class="step-num">{n}</div>
                    <div class="step-title">{t}</div>
                    <div class="step-desc">{d}</div>
                </div>''' for n, (t, d) in enumerate(c['steps'], 1))
    faq = ''.join(f'''
            <div class="faq-item">
                <div class="faq-q">{q}</div>
                <div class="faq-a">{a}</div>
            </div>''' for q, a in c['faq'])
    below = f'''        <section class="how-it-works">
            <h2>{c["steps_title"]}</h2>
            <div class="steps">{steps}
            </div>
        </section>

        <section class="seo-content">
            {c["body"]}
            <h3>{OTHER[lang][0]}</h3>
            {conversions_list(lang, slug)}
        </section>

        <section class="faq">
            <h2>{c["faq_title"]}</h2>{faq}
        </section>'''
    i, j = s.index('        <!-- HOW IT WORKS -->'), s.index('</section>', s.index('<section class="faq">')) + len('</section>')
    s = s[:i] + below + s[j:]
    out = ROOT / path(slug, lang).strip('/') / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(s, encoding='utf-8')
    print('built', out.relative_to(ROOT))


def link_from_converters():
    """'Popular conversions' on both converter pages, kept in step with PAGES (idempotent)."""
    for lang, rel, title in [('en', 'converter', 'Popular conversions'), ('zh', 'zh/converter', '常用转换')]:
        f = ROOT / rel / 'index.html'
        s = f.read_text(encoding='utf-8')
        block = (f'        <!-- CONVERSIONS (scripts/build_landing.py) -->\n        <section class="seo-content">\n            <h2>{title}</h2>\n'
                 f'            {conversions_list(lang)}\n        </section>\n        <!-- /CONVERSIONS -->\n\n')
        s = re.sub(r'        <!-- CONVERSIONS .*?<!-- /CONVERSIONS -->\n\n', '', s, flags=re.S)
        s = s.replace('        <!-- FAQ -->', block + '        <!-- FAQ -->', 1)
        f.write_text(s, encoding='utf-8')


def main():
    link_from_converters()
    for slug in PAGES:
        for lang in ('en', 'zh'):
            build(slug, lang)
    subprocess.run([sys.executable, str(ROOT / 'scripts' / 'seo_sync.py')], check=True)


if __name__ == '__main__':
    main()
