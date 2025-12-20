import io
import os
import requests
import tempfile
import replicate
import subprocess
from nicegui import ui
from pydub import AudioSegment
from pydub.effects import normalize
import sys
import io
import threading
# 强制设置环境编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- 🔴 配置区 ---
os.environ["REPLICATE_API_TOKEN"] = "r8_RoOgQCw7zJqO137NJNirAhsjYLl514Q12PpTB"

state = {
    'original_audio': None,      
    'processed_audio': None,     
    'is_playing_processed': True,
    'selected_model': 'resemble',  # 'resemble', 'playmore', or 'balance'
    # Resemble Enhance 参数
    'prior_temperature': 0.5,  # CFM Prior temperature (0-1)
    'nfe': 64,  # Number of function evaluations (1-128)
    # Playmore Speech Enhancer 参数
    'playmore_model': 'mossformer2_se_48k',  # model choice
    # Dynamic Balance 参数
    'balance_strength': 0.5,  # 平衡强度
    'is_processing': False,
    'processing_status': None  # 'success', 'error', or None
}

def handle_upload(e):
    # 增加错误检查
    try:
        state['original_audio'] = AudioSegment.from_file(io.BytesIO(e.content.read()))
        state['processed_audio'] = None
        ui.notify('上传成功', type='positive')
        main_ui.refresh()
    except Exception as ex:
        ui.notify(f'读取文件失败: {ex}', type='negative')

def start_over():
    """重置所有状态，重新开始"""
    state['original_audio'] = None
    state['processed_audio'] = None
    state['is_playing_processed'] = True
    state['selected_model'] = 'resemble'
    state['prior_temperature'] = 0.5
    state['nfe'] = 64
    state['playmore_model'] = 'mossformer2_se_48k'
    ui.notify('已重置，可以重新开始', type='positive')
    main_ui.refresh()

def run_ai_rescue():
    if not state['original_audio']:
        ui.notify('请先上传音频', type='warning')
        return

    if state['is_processing']:
        ui.notify('正在处理中，请稍候...', type='warning')
        return

    ui.notify('AI 正在全力处理中，请稍候...', type='ongoing', spinner=True, timeout=3000)
    state['processing_status'] = None

    def background_task():
        """纯后台运算，不在线程中调用 UI 操作"""
        try:
            state['is_processing'] = True
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_in:
                state['original_audio'].export(temp_in.name, format="wav")
                
                if state['selected_model'] == 'resemble':
                    print("🚀 后台：使用 Resemble Enhance 模型...")
                    output = replicate.run(
                        "resemble-ai/resemble-enhance:93266a7e7f5805fb79bcf213b1a4e0ef2e45aff3c06eefd96c59e850c87fd6a2",
                        input={
                            "input_audio": open(temp_in.name, "rb"),
                            "solver": "Midpoint",
                            "denoise_flag": True,
                            "prior_temperature": state['prior_temperature'],
                            "number_function_evaluations": state['nfe']
                        }
                    )
                    print("✅ 后台：Resemble AI 计算完成，读取音频中...")
                    target_item = output[1] if len(output) > 1 else output[0]
                    
                elif state['selected_model'] == 'playmore':
                    print("🚀 后台：使用 Playmore Speech Enhancer 模型...")
                    output = replicate.run(
                        "playmore/speech-enhancer:bda37cf8cb38f5b677514933634a281b263a04225f7b2bf62c1c1b8748d21ae6",
                        input={
                            "audio": open(temp_in.name, "rb"),
                            "model": state['playmore_model']
                        }
                    )
                    print("✅ 后台：Playmore 计算完成，读取音频中...")
                    target_item = output
                
                else:  # balance
                    print("🚀 后台：使用动态平衡处理 (FFmpeg Loudnorm)...")
                    # 使用专业的 FFmpeg loudnorm 滤镜
                    audio = state['original_audio']
                    processed_audio = process_dynamic_balance(audio)
                    
                    # 导出到内存
                    buffer = io.BytesIO()
                    processed_audio.export(buffer, format="wav")
                    buffer.seek(0)
                    target_item = buffer
                    
                    print("✅ 后台：动态平衡处理完成...")
            
                # 核心：只更新 state 里的数据
                state['processed_audio'] = AudioSegment.from_file(io.BytesIO(target_item.read()))
                state['processing_status'] = 'success'
                print("✨ 数据已就绪，刷新 UI...")
                
                # 刷新 UI 以显示下载按钮
                main_ui.refresh()

        except Exception as ex:
            print(f"❌ 后台错误: {ex}")
            state['processing_status'] = 'error'
            main_ui.refresh()
        finally:
            state['is_processing'] = False
            if 'temp_in' in locals() and os.path.exists(temp_in.name):
                os.remove(temp_in.name)

    threading.Thread(target=background_task, daemon=True).start()

def download_result():
    target = state['processed_audio'] if state['is_playing_processed'] else state['original_audio']
    buffer = io.BytesIO()
    target.export(buffer, format="mp3")
    ui.download(buffer.getvalue(), "rescued_audio.mp3")

def process_dynamic_balance(audio: AudioSegment) -> AudioSegment:
    """Dynamic Balance V3: The 'Broadcast Standard' (EBU R128 Loudnorm)
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

def select_model(model_name):
    """选择模型并刷新卡片和设置区域"""
    state['selected_model'] = model_name
    model_cards_ui.refresh()
    model_settings_ui.refresh()

@ui.refreshable
def model_cards_ui():
    """可刷新的模型卡片区域"""
    with ui.row().classes('w-full gap-4 items-stretch'):
        # 远程录制修复卡片
        card_class = 'flex-1 cursor-pointer transition-all min-h-36 model-card' + (' model-card-selected border-4 border-indigo-400' if state['selected_model'] == 'resemble' else '')
        with ui.card().classes(card_class).on('click', lambda: select_model('resemble')):
            with ui.column().classes('p-6 gap-3 items-center justify-center h-full'):
                with ui.element('div').classes('w-16 h-16 rounded-full gradient-card-blue flex items-center justify-center'):
                    ui.icon('video_call', size='xl').classes('text-white')
                ui.label('远程录制音质修复').classes('font-bold text-lg text-center text-gray-800')
                ui.label('修复腾讯会议、Zoom 等工具录音的音质问题').classes('text-xs text-gray-600 text-center')
        
        # 人声增强卡片
        card_class = 'flex-1 cursor-pointer transition-all min-h-36 model-card' + (' model-card-selected border-4 border-emerald-400' if state['selected_model'] == 'playmore' else '')
        with ui.card().classes(card_class).on('click', lambda: select_model('playmore')):
            with ui.column().classes('p-6 gap-3 items-center justify-center h-full'):
                with ui.element('div').classes('w-16 h-16 rounded-full gradient-card-cyan flex items-center justify-center'):
                    ui.icon('mic', size='xl').classes('text-white')
                ui.label('人声增强/降噪').classes('font-bold text-lg text-center text-gray-800')
                ui.label('消除爆破音和背景噪音，强化人声').classes('text-xs text-gray-600 text-center')
        
        # 动态平衡卡片
        card_class = 'flex-1 cursor-pointer transition-all min-h-36 model-card' + (' model-card-selected border-4 border-purple-400' if state['selected_model'] == 'balance' else '')
        with ui.card().classes(card_class).on('click', lambda: select_model('balance')):
            with ui.column().classes('p-6 gap-3 items-center justify-center h-full'):
                with ui.element('div').classes('w-16 h-16 rounded-full gradient-card-purple flex items-center justify-center'):
                    ui.icon('tune', size='xl').classes('text-gray-700')
                ui.label('动态平衡').classes('font-bold text-lg text-center text-gray-800')
                ui.label('平衡音频响度，让声音更均匀舒适').classes('text-xs text-gray-600 text-center')

@ui.refreshable
def model_settings_ui():
    """可刷新的模型设置区域"""
    ui.separator().classes('my-4')
    
    # Resemble Enhance 参数
    if state['selected_model'] == 'resemble':
        ui.label('高级参数调整（可选）').classes('font-bold text-md text-indigo-600')
        ui.label(f"修复强度: {state['prior_temperature']} (越低越保守，越高修复越激进)").classes('font-bold mt-2 text-sm')
        ui.slider(min=0, max=1, step=0.1).bind_value(state, 'prior_temperature')
        
        ui.label(f"处理质量: {state['nfe']} (越高质量越好，但处理时间更长)").classes('font-bold mt-4 text-sm')
        ui.slider(min=1, max=128, step=1).bind_value(state, 'nfe')
    
    # Dynamic Balance 参数
    elif state['selected_model'] == 'balance':
        ui.label('平衡参数调整（可选）').classes('font-bold text-md text-purple-600')
        ui.label(f"平衡强度: {state['balance_strength']} (调整音频动态范围)").classes('font-bold mt-2 text-sm')
        ui.slider(min=0, max=1, step=0.1).bind_value(state, 'balance_strength')

@ui.refreshable
def main_ui():
    # 添加自定义 CSS 样式
    ui.add_head_html('''
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4facfe 75%, #00f2fe 100%);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
            min-height: 100vh;
        }
        
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .glass-card {
            background: rgba(255, 255, 255, 0.25);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        }
        
        .gradient-card-blue {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
        }
        
        .gradient-card-pink {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border: none;
        }
        
        .gradient-card-cyan {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            border: none;
        }
        
        .gradient-card-purple {
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            border: none;
        }
        
        .gradient-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 12px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .gradient-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        
        .model-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            transition: all 0.3s ease;
        }
        
        .model-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }
        
        .model-card-selected {
            background: rgba(255, 255, 255, 1);
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        }
        
        /* 美化上传组件 */
        .q-uploader {
            background: transparent !important;
            box-shadow: none !important;
        }
        
        .q-uploader__header {
            background: rgba(255, 255, 255, 0.2) !important;
            border-radius: 12px !important;
            padding: 12px 20px !important;
        }
        
        .q-uploader__list {
            display: none !important;
        }
        
        .q-btn {
            background: rgba(255, 255, 255, 0.9) !important;
            color: #667eea !important;
            font-weight: 600 !important;
            border-radius: 12px !important;
            padding: 10px 24px !important;
            text-transform: none !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
            transition: all 0.3s ease !important;
        }
        
        .q-btn:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3) !important;
        }
    </style>
    ''')
    
    with ui.column().classes('w-full items-center p-8'):
        # 标题栏带重新开始按钮
        with ui.row().classes('w-full max-w-4xl items-center justify-between mb-8'):
            ui.label('🎙️ 播客音频修复工具').classes('text-5xl font-bold text-white drop-shadow-lg')
            if state['original_audio']:
                ui.button('🔄 重新开始', on_click=start_over).classes('px-6 py-3 rounded-full font-semibold transition-all shadow-lg').style('background: rgba(255, 255, 255, 0.95); color: #667eea; border: 2px solid white;')

        with ui.card().classes('w-full max-w-4xl p-8 glass-card'):
            # 美化的上传区域
            with ui.column().classes('w-full items-center p-12 rounded-2xl').style('border: 3px dashed rgba(255, 255, 255, 0.5); background: rgba(255, 255, 255, 0.1);'):
                # 云朵上传图标
                with ui.element('div').classes('w-24 h-24 rounded-full flex items-center justify-center mb-4').style('background: rgba(255, 255, 255, 0.3);'):
                    ui.icon('cloud_upload', size='3rem').classes('text-white')
                ui.label('拖拽文件到这里上传').classes('text-2xl font-bold text-white mb-2')
                ui.label('或点击下方按钮选择文件').classes('text-lg text-white opacity-80 mb-4')
                # 上传按钮 - 简化版本
                ui.upload(on_upload=handle_upload, auto_upload=True).classes('mt-4').props('accept="audio/*"')

            if state['original_audio']:
                ui.separator().classes('my-6')
                
                # 音频播放器
                ui.label('🎵 原始音频预览').classes('font-bold text-lg mb-3 text-gray-800')
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
                    state['original_audio'].export(temp_audio.name, format="mp3")
                    ui.audio(temp_audio.name).classes('w-full')
                
                ui.separator().classes('my-6')
                
                # 显示处理状态通知
                if state['processing_status'] == 'success':
                    ui.notify('✅ 处理完成！', type='positive')
                    state['processing_status'] = None
                elif state['processing_status'] == 'error':
                    ui.notify('❌ 处理失败，请重试', type='negative')
                    state['processing_status'] = None
                
                # 模型选择 - 更简洁的卡片式布局
                ui.label('选择处理模式').classes('font-bold text-2xl mb-4 text-gray-800')
                
                # 可刷新的模型卡片区域
                model_cards_ui()
                
                # 可刷新的模型设置区域
                model_settings_ui()

                # 确保按钮点击后调用函数
                ui.button('🚀 开始处理', on_click=run_ai_rescue).classes('w-full h-14 mt-6 gradient-button text-white text-lg font-bold rounded-2xl')

            if state['processed_audio']:
                ui.separator().classes('my-8')
                with ui.column().classes('w-full p-6 rounded-2xl').style('background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);'):
                    ui.label('🎉 处理完成！').classes('font-bold text-2xl mb-4 text-gray-800')
                    ui.switch('播放处理后版本', value=True).bind_value(state, 'is_playing_processed').classes('text-gray-800')
                    ui.button('📥 下载结果', on_click=download_result).classes('w-full mt-4 h-12 rounded-xl font-bold').style('background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;')

main_ui()
ui.run(title='播客音频修复工具', port=8082, reload=False)