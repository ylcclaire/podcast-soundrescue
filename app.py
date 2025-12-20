from nicegui import ui, app as nicegui_app
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import matplotlib.pyplot as plt
import numpy as np
import io
import os
from pathlib import Path

# State management
state = {
    'projects': {},  # {project_name: {'file_path': str, 'rescued': bool}}
    'current_page': 'sound_rescue',
    'current_audio': None,
    'upload_folder': 'uploads',
    'output_folder': 'rescued'
}

# Ensure folders exist
Path(state['upload_folder']).mkdir(exist_ok=True)
Path(state['output_folder']).mkdir(exist_ok=True)


def generate_waveform(audio_path):
    """Generate waveform visualization using matplotlib"""
    audio = AudioSegment.from_file(audio_path)
    samples = np.array(audio.get_array_of_samples())
    
    # Downsample for visualization
    step = max(1, len(samples) // 2000)
    samples = samples[::step]
    
    fig, ax = plt.subplots(figsize=(12, 3), facecolor='none')
    ax.plot(samples, color='#ec4899', linewidth=0.5)
    ax.set_facecolor('none')
    ax.set_xlim(0, len(samples))
    ax.set_ylim(samples.min(), samples.max())
    ax.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True, bbox_inches='tight', dpi=100)
    plt.close(fig)
    buf.seek(0)
    
    return buf


def rescue_audio(input_path, output_path, low_switch=0.5, high_switch=0.5, enhancement='normal'):
    """Process audio with rescue settings"""
    audio = AudioSegment.from_file(input_path)
    
    # Apply normalization
    audio = normalize(audio)
    
    # Apply compression based on settings
    threshold = -20 + (low_switch * 10)
    ratio = 2 + (high_switch * 2)
    audio = compress_dynamic_range(audio, threshold=threshold, ratio=ratio)
    
    # Enhancement modes
    if enhancement == 'enhanced':
        audio = audio + 2  # Slight boost
    
    audio.export(output_path, format='mp3')
    return output_path


# UI Components
def create_navbar():
    """Create top navigation bar"""
    with ui.row().classes('w-full h-16 bg-white/60 backdrop-blur-md shadow-sm fixed top-0 z-50 items-center px-6 justify-between'):
        with ui.row().classes('gap-6 items-center'):
            ui.label('🎙️ Podcast Rescue').classes('text-xl font-bold text-gray-800')
            
            nav_items = [
                ('Sound Rescue', 'sound_rescue'),
                ('About', 'about'),
                ('Dynamic Balance', 'dynamic_balance'),
                ('Create Video', 'create_video')
            ]
            
            for label, page in nav_items:
                btn = ui.button(label, on_click=lambda p=page: switch_page(p))
                btn.props('flat')
                if state['current_page'] == page:
                    btn.classes('text-pink-500 font-semibold')
                else:
                    btn.classes('text-gray-600')


def create_sidebar():
    """Create left sidebar with upload and project list"""
    with ui.left_drawer(value=True).classes('bg-white/50 backdrop-blur-lg') as drawer:
        drawer.style('width: 280px')
        
        with ui.column().classes('p-4 gap-4 w-full'):
            ui.label('Upload').classes('text-lg font-semibold text-gray-700')
            
            upload = ui.upload(
                on_upload=handle_upload,
                auto_upload=True,
                multiple=False
            ).classes('w-full')
            upload.props('accept="audio/*"')
            
            ui.separator().classes('my-4')
            
            ui.label('Projects').classes('text-lg font-semibold text-gray-700')
            
            global project_list_container
            project_list_container = ui.column().classes('gap-2 w-full')
            update_project_list()


def update_project_list():
    """Update the project list in sidebar"""
    project_list_container.clear()
    
    with project_list_container:
        if not state['projects']:
            ui.label('No projects yet').classes('text-gray-400 text-sm')
        else:
            for name, data in state['projects'].items():
                with ui.card().classes('w-full p-3 cursor-pointer hover:bg-pink-50/50 transition-colors'):
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.column().classes('gap-1'):
                            ui.label(name).classes('text-sm font-medium text-gray-700')
                            status = '✅ Rescued' if data.get('rescued') else '📁 Original'
                            ui.label(status).classes('text-xs text-gray-500')
                        
                        ui.button(icon='play_arrow', on_click=lambda p=data['file_path']: play_audio(p)).props('flat dense round size=sm')


def handle_upload(e):
    """Handle file upload"""
    file_name = e.name
    file_path = os.path.join(state['upload_folder'], file_name)
    
    with open(file_path, 'wb') as f:
        f.write(e.content.read())
    
    # Add to projects
    project_name = Path(file_name).stem
    state['projects'][project_name] = {
        'file_path': file_path,
        'rescued': False,
        'original_name': file_name
    }
    
    state['current_audio'] = file_path
    update_project_list()
    switch_page('sound_rescue')
    ui.notify(f'Uploaded: {file_name}', type='positive')


def play_audio(file_path):
    """Play audio file"""
    state['current_audio'] = file_path
    switch_page('sound_rescue')


def switch_page(page_name):
    """Switch between different pages"""
    state['current_page'] = page_name
    main_content.clear()
    
    with main_content:
        if page_name == 'sound_rescue':
            show_sound_rescue_page()
        elif page_name == 'about':
            show_about_page()
        elif page_name == 'dynamic_balance':
            show_dynamic_balance_page()
        elif page_name == 'create_video':
            show_create_video_page()


def show_sound_rescue_page():
    """Show Sound Rescue page with waveform and controls"""
    with ui.column().classes('gap-6 w-full max-w-5xl mx-auto'):
        ui.label('Sound Rescue').classes('text-3xl font-bold text-gray-800')
        
        if state['current_audio'] and os.path.exists(state['current_audio']):
            # Waveform visualization
            with ui.card().classes('w-full p-6 bg-white/60 backdrop-blur-lg rounded-2xl shadow-lg'):
                ui.label('Sound Wave').classes('text-lg font-semibold text-gray-700 mb-4')
                
                waveform_buf = generate_waveform(state['current_audio'])
                ui.image(waveform_buf).classes('w-full')
            
            # Advanced Settings
            with ui.card().classes('w-full p-6 bg-white/60 backdrop-blur-lg rounded-2xl shadow-lg'):
                ui.label('Advanced Settings').classes('text-lg font-semibold text-gray-700 mb-4')
                
                with ui.row().classes('gap-8 items-center w-full'):
                    with ui.column().classes('flex-1'):
                        ui.label('Low Switch').classes('text-sm text-gray-600')
                        low_slider = ui.slider(min=0, max=1, step=0.1, value=0.5).classes('w-full')
                        ui.label().bind_text_from(low_slider, 'value', lambda v: f'{v:.1f}').classes('text-xs text-gray-500')
                    
                    with ui.column().classes('flex-1'):
                        ui.label('High Switch').classes('text-sm text-gray-600')
                        high_slider = ui.slider(min=0, max=1, step=0.1, value=0.5).classes('w-full')
                        ui.label().bind_text_from(high_slider, 'value', lambda v: f'{v:.1f}').classes('text-xs text-gray-500')
                    
                    with ui.column().classes('flex-1'):
                        ui.label('Enhancement').classes('text-sm text-gray-600')
                        enhancement = ui.select(['normal', 'enhanced'], value='normal').classes('w-full')
                
                ui.button('RESCUE', on_click=lambda: perform_rescue(low_slider.value, high_slider.value, enhancement.value)).classes('mt-4 bg-pink-500 text-white px-8 py-2 rounded-lg hover:bg-pink-600')
            
            # Audio Player
            with ui.card().classes('w-full p-6 bg-white/60 backdrop-blur-lg rounded-2xl shadow-lg'):
                ui.label('Audio Player').classes('text-lg font-semibold text-gray-700 mb-4')
                ui.audio(state['current_audio']).classes('w-full')
        
        else:
            with ui.card().classes('w-full p-12 bg-white/60 backdrop-blur-lg rounded-2xl shadow-lg text-center'):
                ui.label('📁 No audio file selected').classes('text-xl text-gray-400')
                ui.label('Upload a file from the sidebar to get started').classes('text-sm text-gray-500 mt-2')


def perform_rescue(low, high, enhancement):
    """Perform audio rescue operation"""
    if not state['current_audio']:
        ui.notify('No audio file selected', type='warning')
        return
    
    try:
        # Generate output filename
        original_name = Path(state['current_audio']).stem
        output_path = os.path.join(state['output_folder'], f'{original_name}_rescued.mp3')
        
        # Process audio
        rescue_audio(state['current_audio'], output_path, low, high, enhancement)
        
        # Update project state
        rescued_name = f'{original_name}_rescued'
        state['projects'][rescued_name] = {
            'file_path': output_path,
            'rescued': True,
            'original_name': f'{original_name}_rescued.mp3'
        }
        
        # Mark original as rescued
        for name, data in state['projects'].items():
            if data['file_path'] == state['current_audio']:
                data['rescued'] = True
        
        state['current_audio'] = output_path
        update_project_list()
        switch_page('sound_rescue')
        
        ui.notify('✅ Audio rescued successfully!', type='positive')
    
    except Exception as e:
        ui.notify(f'Error: {str(e)}', type='negative')


def show_about_page():
    """Show About page"""
    with ui.column().classes('gap-6 w-full max-w-3xl mx-auto'):
        with ui.card().classes('w-full p-8 bg-white/60 backdrop-blur-lg rounded-2xl shadow-lg'):
            ui.label('About Podcast Rescue').classes('text-3xl font-bold text-gray-800 mb-4')
            ui.label('Rescue your podcast audio with advanced processing tools.').classes('text-lg text-gray-600 mb-4')
            ui.label('Features:').classes('text-xl font-semibold text-gray-700 mt-6 mb-2')
            ui.label('• Audio normalization and compression').classes('text-gray-600')
            ui.label('• Waveform visualization').classes('text-gray-600')
            ui.label('• Advanced audio enhancement').classes('text-gray-600')
            ui.label('• Project management').classes('text-gray-600')


def show_dynamic_balance_page():
    """Show Dynamic Balance page"""
    with ui.column().classes('gap-6 w-full max-w-3xl mx-auto'):
        with ui.card().classes('w-full p-8 bg-white/60 backdrop-blur-lg rounded-2xl shadow-lg text-center'):
            ui.label('Dynamic Balance').classes('text-3xl font-bold text-gray-800 mb-4')
            ui.label('Coming soon...').classes('text-lg text-gray-400')


def show_create_video_page():
    """Show Create Video page"""
    with ui.column().classes('gap-6 w-full max-w-3xl mx-auto'):
        with ui.card().classes('w-full p-8 bg-white/60 backdrop-blur-lg rounded-2xl shadow-lg text-center'):
            ui.label('Create Video').classes('text-3xl font-bold text-gray-800 mb-4')
            ui.label('Coming soon...').classes('text-lg text-gray-400')


# Main App
@ui.page('/')
def main():
    # Set background gradient
    ui.query('body').style('''
        background: linear-gradient(135deg, #fce7f3 0%, #ddd6fe 50%, #e0f2fe 100%);
        background-attachment: fixed;
    ''')
    
    # Create navbar
    create_navbar()
    
    # Create sidebar
    create_sidebar()
    
    # Main content area
    global main_content
    with ui.column().classes('mt-20 p-8 w-full') as main_content:
        show_sound_rescue_page()


# Run the app
ui.run(title='Podcast Rescue', port=8080, reload=False)
