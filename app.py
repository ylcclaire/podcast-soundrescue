import streamlit as st

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

# Sidebar
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
    
    # Settings
    st.markdown("---")
    st.subheader("⚙️ Settings")
    denoise_strength = st.slider(
        "Denoise Strength",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1,
        help="Adjust the strength of noise reduction"
    )

# Main Area
st.title("Podcast Rescue: Cyberpunk Audio Engineer")

# Get active file from session state
active_file = None
if st.session_state.active_file_index is not None and len(st.session_state.file_history) > 0:
    active_file = st.session_state.file_history[st.session_state.active_file_index]

# Create 2 columns
col1, col2 = st.columns(2)

# Left Column - Original Input
with col1:
    st.markdown("### 🔴 Original Input")
    
    # Display active file's original audio
    if active_file is not None:
        st.audio(active_file['data'], format='audio/wav')
        st.caption(f"📁 {active_file['name']}")
    else:
        st.info("Upload an audio file to begin")
    
    # Start Rescue button
    st.markdown("<br>", unsafe_allow_html=True)
    start_button = st.button("🚀 Start Rescue", use_container_width=True, type="primary")
    
    # Process audio when button is clicked
    if start_button and active_file is not None:
        with st.spinner("🔧 Rescuing your podcast..."):
            # Simulate processing (replace with actual audio processing)
            import time
            time.sleep(1)
            
            # Store enhanced audio in session state
            st.session_state.file_history[st.session_state.active_file_index]['enhanced_audio'] = active_file['data']
            st.success("✅ Audio enhanced successfully!")
            st.rerun()

# Right Column - AI Enhanced
with col2:
    st.markdown("### 🟢 AI Enhanced")
    
    # Display enhanced audio if available
    if active_file is not None and active_file['enhanced_audio'] is not None:
        st.audio(active_file['enhanced_audio'], format='audio/wav')
        st.caption(f"✨ Enhanced: {active_file['name']}")
        st.success("Processing complete! Your audio has been enhanced.")
    elif active_file is not None:
        st.info("Click 'Start Rescue' to process this audio file")
    else:
        st.info("Upload an audio file and click 'Start Rescue'")
