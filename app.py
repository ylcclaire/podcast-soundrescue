#!/usr/bin/env python3
"""
Audio Processing App - Zen Mode (Final Fix)
"""
from nicegui import ui, app
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import io
import base64
from pathlib import Path
import asyncio
import subprocess
import tempfile
import os

# Global state
state = {
    'original_file': None,
    'original_filename': None,
    'processed_file': None,
    'processed_filename': None,
    'main_card': None
}

def download_bytes(data: bytes, filename: str):
    """Helper: Download in-memory bytes using JavaScript"""
    b64 = base64.b64encode(data).decode()
    ui.run_javascript(f'''
        const link = document.createElement("a");
        link.href = "data:audio/mpeg;base64,{b64}";
        link.download = "{filename}";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    ''')

def process_sound_rescue(audio: AudioSegment) -> AudioSegment:
    audio = normalize(audio, headroom=0.1)
    return compress_dynamic_range(audio, threshold=-20.0, ratio=3.0, attack=5.0, release=50.0)

def process_dynamic_balance(audio: AudioSegment) -> AudioSegment:
    """
    Dynamic Balance V3: The 'Broadcast Standard' (EBU R128 Loudnorm)
    Uses FFmpeg's specialized filter for perceived loudness normalization.
    Target: -16 LUFS (Podcast Standard)
    """
    # 1. 创建临时文件来中转数据
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_in, \
         tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_out:
        
        input_path = temp_in.name
        output_path = temp_out.name
        
        # 2. 把当前音频导出到临时文件
        audio.export(input_path, format="wav")
        
        # 3. 调用 FFmpeg 的核武器：loudnorm 滤镜
        # I=-16:   目标响度 -16 LUFS (播客黄金标准)
        # LRA=11:  响度范围 11 LU (人声对话的标准动态范围)
        # TP=-1.5: 真峰值 -1.5 dBTP (防止爆音)
        command = [
            "ffmpeg",
            "-y",                     # 覆盖输出文件
            "-i", input_path,         # 输入
            "-af", "loudnorm=I=-16:LRA=11:TP=-1.5",  # 核心滤镜
            "-ar", "44100",           # 统一采样率
            output_path               # 输出
        ]
        
        try:
            # 执行命令（不显示繁杂的日志）
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 4. 把处理好的音频读回来
            processed_audio = AudioSegment.from_wav(output_path)
            
        except subprocess.CalledProcessError as e:
            print("FFmpeg error:", e)
            # 如果失败了，就返回原音频（或者做一个简单的归一化作为保底）
            processed_audio = normalize(audio)
            
        finally:
            # 5. 清理战场：删除临时文件
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
                
    return processed_audio

def go_to_stage_1():
    state['original_file'] = None
    with state['main_card']:
        state['main_card'].clear()
        with ui.column().classes('w-full items-center gap-8 p-12'):
            ui.label('🎵 Audio Processor').classes('text-5xl font-light text-gray-800')
            ui.label('Upload audio to begin').classes('text-xl text-gray-600 font-light')
            ui.upload(on_upload=handle_upload, auto_upload=True, max_files=1).props('accept="audio/*"').classes('w-full max-w-md')

def handle_upload(event):
    state['original_file'] = event.content.read() # CRITICAL FIX
    state['original_filename'] = event.name
    ui.notify(f"Uploaded: {event.name}")
    go_to_stage_2()

def go_to_stage_2():
    with state['main_card']:
        state['main_card'].clear()
        with ui.column().classes('w-full items-center gap-8 p-12'):
            ui.label('Select Tool').classes('text-4xl font-light text-gray-800')
            if state['original_file']:
                b64 = base64.b64encode(state['original_file']).decode()
                ui.html(f'<audio controls src="data:audio/mp3;base64,{b64}" class="w-full max-w-md mb-8"></audio>')
            with ui.row().classes('gap-6'):
                ui.button('🛠️ Sound Rescue', on_click=lambda: process_audio('rescue')).classes('text-xl px-12 py-8 rounded-2xl shadow-lg').style('background: #667eea; color: white;')
                ui.button('⚖️ Dynamic Balance', on_click=lambda: process_audio('balance')).classes('text-xl px-12 py-8 rounded-2xl shadow-lg').style('background: #f093fb; color: white;')

async def process_audio(tool_type: str):
    notification = ui.notification('Processing...', type='ongoing', spinner=True)
    try:
        loop = asyncio.get_running_loop()
        def run_pydub():
            audio = AudioSegment.from_file(io.BytesIO(state['original_file']))
            processed = process_sound_rescue(audio) if tool_type == 'rescue' else process_dynamic_balance(audio)
            buffer = io.BytesIO()
            processed.export(buffer, format="mp3")
            buffer.seek(0)
            return buffer.read()
        
        state['processed_file'] = await loop.run_in_executor(None, run_pydub)
        state['processed_filename'] = f"processed_{state['original_filename']}"
        notification.dismiss()
        go_to_stage_3()
    except Exception as e:
        notification.dismiss()
        ui.notify(f'Error: {str(e)}', type='negative')

def go_to_stage_3():
    with state['main_card']:
        state['main_card'].clear()
        with ui.column().classes('w-full items-center gap-8 p-12'):
            ui.label('✨ Ready').classes('text-4xl font-light text-gray-800')
            b64 = base64.b64encode(state['processed_file']).decode()
            ui.html(f'<audio controls src="data:audio/mp3;base64,{b64}" class="w-full max-w-md mb-8"></audio>')
            ui.button('⬇️ Download', on_click=lambda: download_bytes(state['processed_file'], state['processed_filename'])).classes('text-2xl px-16 py-8 rounded-2xl shadow-xl').style('background: #11998e; color: white;')
            ui.button('🔄 Start Over', on_click=go_to_stage_1).classes('flat')

@ui.page('/')
def main_page():
    ui.query('body').style('background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center;')
    with ui.card().classes('backdrop-blur-xl bg-white/70 rounded-3xl shadow-2xl').style('width: 900px; min-height: 600px;') as main_card:
        state['main_card'] = main_card
        go_to_stage_1()

ui.run(title='Audio Processor', port=8082, reload=False)