import streamlit as st
from story_generation.story_generator import StoryGenerator
from voice_generation.voice_generator import VoiceGenerator
from video_generation.video_generator import VideoGenerator
from moviepy.editor import VideoFileClip
import tempfile
import os
from pydub.utils import mediainfo
from dotenv import load_dotenv
path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), '.env')
load_dotenv(path)

@st.cache_data(show_spinner=False)
def create_story_generator(api_key):
    return StoryGenerator(api_key=api_key)

@st.cache_data(show_spinner=False)
def create_voice_generator(api_key):
    return VoiceGenerator(api_key=api_key)

@st.cache_data(show_spinner=False)
def create_video_generator(openai_api_key = None, stable_diff_api_key = None):
    return VideoGenerator(openai_api_key=openai_api_key,
                          stable_diff_api_key=stable_diff_api_key)

@st.cache_data(show_spinner=False)
def generate_story(_generator, story_summary):
    return _generator.generate_story(story_summary)

@st.cache_data(show_spinner=False)
def generate_voice(_voice_generator, text, voice, model):
    return _voice_generator.generate_story_audio(text, voice, model)

@st.cache_data(show_spinner=False)
def generate_static_video(_video_generator, audio_file, static_image):
    return _video_generator.generate_video_static(audio_file, static_image)

@st.cache_data(show_spinner=False)
def create_list_of_voices(_voice_generator):
    return _voice_generator.get_list_of_voices()

def main():
    st.title("Welcome to VoiceUp!")
    st.header("This is a platform for creators to create short clips based on their own content.")
    with st.expander("About the App"):
            st.write("AI Video Genereration app with Video's Summary and voice cloned feature")

    # Instantiate some variables in the session state
    if "story" not in st.session_state:
        st.session_state.story = ""
    
    if "voice_generator" not in st.session_state:
        st.session_state.voice_generator = None
    
    # Create an instance of StoryGenerator
    openai_api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
    elevenlabs_api_key = st.sidebar.text_input("Enter your ElvenLabs API Key", type="password")


    if openai_api_key:  # only instantiate StoryGenerator after API key is entered
        generator = create_story_generator(api_key=openai_api_key)

    if elevenlabs_api_key:
        voice_generator = create_voice_generator(api_key=elevenlabs_api_key)
    
    # Video generator for default properties doesn't need an apy key
    # TODO: Update this when image generation is integrated
    video_generator = create_video_generator()

    # User can select to provide full story or generate it
    story_option = st.selectbox("Choose an option:", ["Upload your own story", "Generate story using AI"])

    if story_option == "Upload your own story":
        
        with st.form(key="story_upload_option"):
    
            uploaded_file = st.file_uploader("Upload your story file", type=["txt"])
            
            if uploaded_file is not None:
                try:
                # Read the contents of the uploaded file
                    user_story = uploaded_file.read().decode("utf-8")
                    
                    # Display the uploaded story
                    st.text_area("Your uploaded story:", value=user_story, key="user_story", height=200)
                    
                except Exception as e:
                    st.error(f"Error reading the file: {e}")

            submit_button = st.form_submit_button(label="Generate")
            if submit_button:
                if user_story in ("", "None", None):
                    st.error("Make sure you enter your story above..")
                st.session_state.story = user_story


    elif story_option == "Generate story using AI":
            with st.form(key="story_gen_option"):

                # story_summary = st.text_input("Enter a short summary for your story")
                story_genre = st.selectbox("Select Story Genre:", ["Fairy Tale", "Mystery", "Adventure", "Science Fiction"])
                age_group = st.selectbox("Age Group:", ["Children", "Teenagers", "Adults"])
                language = st.selectbox("Language:", ["English", "Spanish", "French", "German"])
                additional_text = st.text_area("Enter additional text (optional):", "")
        
                submit_button = st.form_submit_button(label='Generate Story')

                if submit_button:
            
                    try:
                        # Create a more descriptive prompt for generating the story
                        if additional_text:
                            story_summary = f"Generate a {age_group} {story_genre} story in {language} language. Additional Information about the story: {additional_text}"
                        else:
                            story_summary = f"Generate a {age_group} {story_genre} story in {language} language."

                        with st.spinner('Generating your story...'):
                            # Generate story (replace this with your AI-based story generation logic)
                            generated_story = generate_story(generator, story_summary)
                            st.session_state.story = generated_story.lstrip()

                        st.text_area("AI Generated Story:", value=st.session_state.story)
                    except UnboundLocalError:  # Catch the specific error you're interested in
                        st.error("Please enter your OpenAI API Key to generate a story.")
        
    
    audio_option = st.selectbox("Generate audio:", ["Use default voices", "Custom voice!"])
    if audio_option == "Use default voices":
        with st.form(key="voice_form"):
            try:
                voice = st.selectbox("Choose a voice:", create_list_of_voices(voice_generator))
            except UnboundLocalError as e:
                voice = st.selectbox("Choose a voice:", ["Arnold"])
            model = st.selectbox("Choose a model:", ["eleven_multilingual_v1"])

            voice_submit_button = st.form_submit_button(label="Generate Audio")
            if voice_submit_button:
                try:
                    with st.spinner("Generating your audio..."):
                        # Generate audio
                        audio = generate_voice(
                            voice_generator,
                            text=st.session_state.story,
                            voice=voice,
                            model=model
                        )
                        
                        print(audio)
                        st.audio(audio, format="audio/mp3")
                except UnboundLocalError:  # Catch the specific error you're interested in
                    st.error("Please enter your ElevenLabs API Key to generate a story.")

    elif audio_option == "Custom voice!":
        with st.form(key="clone_form"):
            
            voice_name = st.text_input("Voice name:", key="voice_name")
            voice_description = st.text_input(
                label="Voice description:",
                key="voice_description",
                placeholder="An old American male voice with a slight hoarseness in his throat. Perfect for news"
                )
            
            voice_file = st.file_uploader("Upload a voice sample for the custom voice", type=['mp3', 'wav'])

            clone_submit_button = st.form_submit_button(label="Generate Audio")

            if clone_submit_button and voice_file is not None:
                print(voice_file)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
                    # Write the uploaded audio bytes to temp file
                    tmpfile.write(voice_file.getvalue())
                    tmp_filename = tmpfile.name
                # Add validation for maximum length of the audio file
                audio_info = mediainfo(tmp_filename)
                if float(audio_info["duration"]) > 120:
                    st.error("Uploaded audio is too long. Please upload an audio of maximum 2 minutes.")

                try:
                    with st.spinner("Creating the story audio with custom voice..."):
                        custom_audio = voice_generator.generate_story_with_new_voice(
                            text=st.session_state.story,
                            name=st.session_state.voice_name,
                            description=st.session_state.voice_description,
                            files=[tmp_filename]
                        )
                        print(custom_audio)
                        st.audio(custom_audio, format="audio/mp3")
                except Exception as e:
                    print(e)
                    st.error("Cloning went wrong...")
                finally:
                    os.remove(tmp_filename)
    

    video_option = st.selectbox("Generate a video:", ["Upload my own photos", "Generate new photos!"])
    
    if video_option == "Upload my own photos":

        with st.form(key="video_custom_image_form"):

            image_option = st.selectbox("What images would you like?", ["Upload my own photos", "Use static default image"])

            if image_option == "Upload my own photos":
                st.session_state.images = st.file_uploader("Upload files", [".png", ".jpg"])
            elif image_option == "Use static default image":
                st.session_state.image = None # This will default to black_image.png

            video_submitt_button = st.form_submit_button("Generate Video")

            if video_submitt_button:
                try:
                    with st.spinner("Generating your video..."):

                        video_generator.generate_video_static(static_image = st.session_state.image)
                        # TODO: Naming of these videos
                        file_location = os.path.join(video_generator.video_path, "test.mp4")
                        print(file_location)
                        with open(file_location, 'rb') as f:
                                video_bytes = f.read()
                        st.video(video_bytes, format="video/mp4")
                            
                except Exception as e:
                    print(e)






if __name__ == "__main__":
    main()
