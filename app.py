import streamlit as st
import streamlit.components.v1 as components
import base64

# Page configuration
st.set_page_config(
    page_title="Podcast Rescue",
    page_icon="🎙️",
    layout="wide"
)

# Initialize session state for file history
if 'file_history' not in st.session_state:
    st.session_state.file_history = []

if 'active_file_index' not in st.session_state:
    st.session_state.active_file_index = None

# Helper function: Create crossfader HTML component
def get_audio_html(original_data, enhanced_data):
    """Generate HTML/JS for seamless audio crossfader"""
    # Encode both audio files to base64
    original_b64 = base64.b64encode(original_data).decode()
    enhanced_b64 = base64.b64encode(enhanced_data).decode()
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: sans-serif;
                background-color: #0F172A;
                color: #E2E8F0;
                padding: 20px;
            }}
            .player-container {{
                max-width: 800px;
                margin: 0 auto;
                padding: 30px;
                background: #1E293B;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            }}
            .controls {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .play-button {{
                background: #818CF8;
                color: white;
                border: none;
                padding: 15px 40px;
                font-size: 18px;
                border-radius: 8px;
                cursor: pointer;
                transition: background 0.3s;
            }}
            .play-button:hover {{
                background: #6366F1;
            }}
            .toggle-container {{
                margin-top: 30px;
                text-align: center;
            }}
            .toggle-button {{
                background: #1E293B;
                color: white;
                border: 2px solid #818CF8;
                padding: 20px 60px;
                font-size: 20px;
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.3s;
                font-weight: bold;
            }}
            .toggle-button:hover {{
                background: #334155;
                transform: scale(1.05);
            }}
            .toggle-button.original {{
                border-color: #EF4444;
                box-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
            }}
            .toggle-button.enhanced {{
                border-color: #10B981;
                box-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
            }}
            .time-display {{
                text-align: center;
                margin-top: 20px;
                font-size: 16px;
                color: #94A3B8;
            }}
        </style>
    </head>
    <body>
        <div class="player-container">
            <div class="controls">
                <button id="playBtn" class="play-button">▶️ Play</button>
            </div>
            
            <div class="toggle-container">
                <button id="toggleBtn" class="toggle-button original">🔴 Original</button>
            </div>
            
            <div class="time-display" id="timeDisplay">0:00 / 0:00</div>
        </div>
        
        <!-- Hidden audio elements -->
        <audio id="originalAudio" preload="auto">
            <source src="data:audio/wav;base64,{original_b64}" type="audio/wav">
        </audio>
        <audio id="enhancedAudio" preload="auto">
            <source src="data:audio/wav;base64,{enhanced_b64}" type="audio/wav">
        </audio>
        
        <script>
            const playBtn = document.getElementById('playBtn');
            const toggleBtn = document.getElementById('toggleBtn');
            const originalAudio = document.getElementById('originalAudio');
            const enhancedAudio = document.getElementById('enhancedAudio');
            const timeDisplay = document.getElementById('timeDisplay');
            
            let isPlaying = false;
            let isOriginal = true;
            
            // Initialize volumes - start with Original
            originalAudio.volume = 1.0;
            enhancedAudio.volume = 0.0;
            
            // Play/Pause button
            playBtn.addEventListener('click', function() {{
                if (!isPlaying) {{
                    // Sync both audios and play
                    originalAudio.currentTime = enhancedAudio.currentTime;
                    originalAudio.play();
                    enhancedAudio.play();
                    playBtn.textContent = '⏸️ Pause';
                    isPlaying = true;
                }} else {{
                    originalAudio.pause();
                    enhancedAudio.pause();
                    playBtn.textContent = '▶️ Play';
                    isPlaying = false;
                }}
            }});
            
            // Toggle button - seamless switch without stopping audio
            toggleBtn.addEventListener('click', function() {{
                isOriginal = !isOriginal;
                
                if (isOriginal) {{
                    // Switch to Original
                    originalAudio.volume = 1.0;
                    enhancedAudio.volume = 0.0;
                    toggleBtn.textContent = '🔴 Original';
                    toggleBtn.className = 'toggle-button original';
                }} else {{
                    // Switch to Enhanced
                    originalAudio.volume = 0.0;
                    enhancedAudio.volume = 1.0;
                    toggleBtn.textContent = '🟢 Enhanced';
                    toggleBtn.className = 'toggle-button enhanced';
                }}
            }});
            
            // Time display update
            originalAudio.addEventListener('timeupdate', function() {{
                const current = formatTime(originalAudio.currentTime);
                const duration = formatTime(originalAudio.duration);
                timeDisplay.textContent = `${{current}} / ${{duration}}`;
            }});
            
            // Auto-pause when audio ends
            originalAudio.addEventListener('ended', function() {{
                playBtn.textContent = '▶️ Play';
                isPlaying = false;
            }});
            
            // Keep audios in sync
            originalAudio.addEventListener('play', function() {{
                if (Math.abs(originalAudio.currentTime - enhancedAudio.currentTime) > 0.1) {{
                    enhancedAudio.currentTime = originalAudio.currentTime;
                }}
            }});
            
            function formatTime(seconds) {{
                if (isNaN(seconds)) return '0:00';
                const mins = Math.floor(seconds / 60);
                const secs = Math.floor(seconds % 60);
                return `${{mins}}:${{secs.toString().padStart(2, '0')}}`;
            }}
        </script>
    </body>
    </html>
    """
    return html_code

# CSS Injection - Modern Dark Theme (Slate Blue/Indigo)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stApp {
        background-color: #0F172A;
    }
    
    .block-container {
        background-color: #0F172A;
    }
    
    h1, h2, h3 {
        color: #818CF8;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar - Simple Playlist Only
with st.sidebar:
    st.title("🎙️ Podcast Rescue")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Audio File",
        type=["mp3", "wav"],
        help="Upload your podcast audio file (MP3 or WAV)"
    )
    
    # Handle new file upload - add to history
    if uploaded_file is not None:
        # Check if file already exists in history
        file_exists = False
        for idx, file_obj in enumerate(st.session_state.file_history):
            if file_obj['name'] == uploaded_file.name:
                file_exists = True
                st.session_state.active_file_index = idx
                break
        
        # If new file, add to history
        if not file_exists:
            file_data = {
                'name': uploaded_file.name,
                'data': uploaded_file.getvalue(),
                'enhanced_audio': None,
                'waveform_original': None,
                'waveform_enhanced': None
            }
            st.session_state.file_history.append(file_data)
            st.session_state.active_file_index = len(st.session_state.file_history) - 1
    
    # File History / Playlist
    if len(st.session_state.file_history) > 0:
        st.markdown("---")
        st.subheader("📂 Your Projects")
        
        file_names = [f['name'] for f in st.session_state.file_history]
        
        selected_file = st.radio(
            "Select a file:",
            options=file_names,
            index=st.session_state.active_file_index if st.session_state.active_file_index is not None else 0,
            label_visibility="collapsed"
        )
        
        # Update active file index based on selection
        for idx, file_obj in enumerate(st.session_state.file_history):
            if file_obj['name'] == selected_file:
                st.session_state.active_file_index = idx
                break

# Main Area with Tabs
st.title("Podcast Rescue")

# Get active file from session state
active_file = None
if st.session_state.active_file_index is not None and len(st.session_state.file_history) > 0:
    active_file = st.session_state.file_history[st.session_state.active_file_index]

# Create 3 tabs
tab1, tab2, tab3 = st.tabs(["ℹ️ About", "🛠️ Rescue Sound", "⚖️ Dynamic Balance"])

# Tab 1: About
with tab1:
    st.header("Welcome to Podcast Rescue")
    st.markdown("""
    ### 🎙️ AI-Powered Audio Enhancement
    
    **Podcast Rescue** is your intelligent audio engineer that transforms noisy, unbalanced podcast recordings 
    into professional-quality audio.
    
    #### What We Do:
    - **🤖 AI Noise Reduction**: Advanced machine learning algorithms identify and remove background noise, 
      hum, hiss, and unwanted artifacts while preserving voice clarity.
    
    - **📊 FFmpeg Loudness Normalization**: Industry-standard audio processing ensures consistent volume 
      levels across your entire podcast, meeting broadcast standards (LUFS normalization).
    
    - **🎚️ Real-Time Comparison**: Instantly compare original and enhanced audio with our seamless toggle 
      player - no interruptions, no restarts.
    
    #### How It Works:
    1. Upload your audio file (MP3 or WAV)
    2. Adjust enhancement settings to your preference
    3. Click "Start Rescue" to process
    4. Compare results in real-time
    5. Download your professional-quality audio
    
    #### Perfect For:
    - Podcast creators and producers
    - Content creators and YouTubers
    - Remote interviews and recordings
    - Home studio recordings
    - Quick audio cleanup and enhancement
    
    ---
    
    **Get started by uploading an audio file from the sidebar!** 👈
    """)

# Tab 2: Rescue Sound (Main Tool)
with tab2:
    if active_file is not None:
        st.caption(f"📁 {active_file['name']}")
        
        # Check if enhanced audio is ready
        if active_file['enhanced_audio'] is not None:
            # Show the seamless toggle component
            st.subheader("🎚️ Real-Time Audio Comparison")
            st.info("Play the audio and click the toggle button to instantly switch between Original and Enhanced versions!")
            
            # Generate and display custom HTML player
            audio_html = get_audio_html(active_file['data'], active_file['enhanced_audio'])
            components.html(audio_html, height=300)
            
        else:
            # Show original audio
            st.subheader("🔴 Original Audio")
            st.audio(active_file['data'], format='audio/wav')
            
            st.markdown("---")
            
            # Advanced Settings in Expander
            with st.expander("⚙️ Advanced Settings"):
                denoise_strength = st.slider(
                    "Denoise Strength",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.1,
                    help="Adjust the strength of noise reduction. Higher values remove more noise but may affect voice quality."
                )
                
                st.info("💡 Tip: Start with 0.5 and adjust based on your audio quality needs.")
            
            # Start Rescue button
            start_button = st.button("🚀 Start Rescue", use_container_width=True, type="primary")
            
            # Process audio when button is clicked
            if start_button:
                with st.spinner("🔧 Rescuing your podcast..."):
                    # Simulate processing (replace with actual audio processing)
                    import time
                    time.sleep(1)
                    
                    # Store enhanced audio in session state (persists across file switches)
                    st.session_state.file_history[st.session_state.active_file_index]['enhanced_audio'] = active_file['data']
                    st.success("✅ Audio enhanced successfully!")
                    st.rerun()
    
    else:
        # No file selected
        st.info("👈 Upload an audio file from the sidebar to begin")

# Tab 3: Dynamic Balance
with tab3:
    st.header("Dynamic Balance & Loudness Normalization")
    
    if active_file is not None and active_file['enhanced_audio'] is not None:
        st.subheader("📊 Loudness Analysis")
        st.caption(f"📁 {active_file['name']}")
        
        # Placeholder for loudness analysis
        st.info("🔧 Loudness analysis and visualization coming soon!")
        
        st.markdown("""
        ### Features (Coming Soon):
        - **LUFS Measurement**: Integrated loudness measurement
        - **Peak Normalization**: Prevent clipping and distortion
        - **Dynamic Range Visualization**: See your audio's dynamic profile
        - **Broadcast Standards**: Meet podcast platform requirements
        - **Batch Processing**: Normalize multiple files at once
        """)
        
    else:
        st.info("📌 Dedicated Loudness Normalization Tool (Coming Soon)")
        st.markdown("""
        This tab will provide advanced loudness normalization features using FFmpeg:
        
        - Analyze audio loudness levels (LUFS)
        - Normalize to broadcast standards (-16 LUFS for podcasts)
        - Visualize dynamic range and peaks
        - Apply compression and limiting
        - Ensure consistent volume across episodes
        
        **Upload and process a file in the "Rescue Sound" tab to see analysis here.**
        """)
