import io
import os
import requests
import tempfile
import replicate
from nicegui import ui
from pydub import AudioSegment
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
    'rescue_strength': 0.5,
    'is_processing': False
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

def run_ai_rescue():
    if not state['original_audio']:
        ui.notify('请先上传音频', type='warning')
        return

    if state['is_processing']:
        ui.notify('正在处理中，请稍候...', type='warning')
        return

    ui.notify('AI 正在全力处理中，请稍候...', type='ongoing', spinner=True)

    def background_task():
        """纯后台运算，完全不触碰 ui.notify 或 ui.run_javascript，避免线程报错"""
        try:
            state['is_processing'] = True
            print("🚀 后台：开始导出并上传到 Resemble...")
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_in:
                state['original_audio'].export(temp_in.name, format="wav")
                
                output = replicate.run(
                    "resemble-ai/resemble-enhance:93266a7e7f5805fb79bcf213b1a4e0ef2e45aff3c06eefd96c59e850c87fd6a2",
                    input={
                        "input_audio": open(temp_in.name, "rb"),
                        "solver": "Midpoint",
                        "denoise_flag": True,
                        "lambd": state['rescue_strength']
                    }
                )

            print("✅ 后台：AI 计算完成，读取音频中...")
            target_item = output[1] if len(output) > 1 else output[0]
            
            # 核心：只更新 state 里的数据
            state['processed_audio'] = AudioSegment.from_file(io.BytesIO(target_item.read()))
            print("✨ 数据已就绪，刷新 UI...")
            
            # 刷新 UI 以显示下载按钮
            main_ui.refresh()

        except Exception as ex:
            print(f"❌ 后台错误: {ex}")
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

@ui.refreshable
def main_ui():
    with ui.column().classes('w-full items-center p-8'):
        ui.label('Podcast Sound Rescue').classes('text-4xl font-bold mb-8')

        with ui.card().classes('w-full max-w-xl p-6 shadow-lg rounded-xl'):
            ui.upload(on_upload=handle_upload, label='Upload Raw Audio', auto_upload=True).classes('w-full')

            if state['original_audio']:
                ui.separator().classes('my-6')
                
                ui.label(f"Rescue Strength: {state['rescue_strength']}").classes('font-bold')
                ui.slider(min=0, max=1, step=0.1).bind_value(state, 'rescue_strength')

                # 确保按钮点击后调用函数
                ui.button('🚀 START AI RESCUE', on_click=run_ai_rescue).classes('w-full h-12 mt-4 bg-indigo-600 text-white')

            if state['processed_audio']:
                ui.separator().classes('my-8')
                with ui.column().classes('w-full p-4 bg-blue-50 rounded-lg'):
                    ui.switch('Hear Rescued Version', value=True).bind_value(state, 'is_playing_processed')
                    ui.button('Download Result', on_click=download_result).classes('w-full mt-4 bg-emerald-500 text-white')

main_ui()
ui.run(title='Sound Rescue AI', port=8082, reload=False)