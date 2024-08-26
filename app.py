import streamlit as st
import edge_tts
from streamlit import runtime
import streamlit.components.v1 as components
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit_js_eval import streamlit_js_eval
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.runtime import get_instance
import secrets
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx
import asyncio
import re, os, shutil

from pedalboard import Pedalboard, Reverb, Gain, Phaser
from pedalboard.io import AudioFile

# Make a Pedalboard object, containing multiple audio plugins:
board = Pedalboard([Gain(gain_db=1), Reverb(room_size=0.01)])


VOICE3 = "en-US-JennyNeural"
VOICE1 = "ja-JP-NanamiNeural" # female voice
VOICE2 = "ja-JP-KeitaNeural" # male voice
VOICE5 = 'en-US-AvaNeural'
VOICE6 = 'en-US-AndrewNeural'
VOICE8 = 'en-IE-EmilyNeural'
#VOICE = "ko-KR-SunHiNeural"
VOICE7 = "en-GB-SoniaNeural"
VOICE4 = 'fr-FR-VivienneMultilingualNeural'
# colab side make dir
def my_makedirs(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def heart_beat():
    """
    Heartbeat function to track whether the session is alive
    """
    thread = threading.Timer(interval=60, function=heart_beat)

    # insert context to the current thread, needed for
    # getting session specific attributes like st.session_state

    add_script_run_ctx(thread)

    # context is required to get session_id of the calling
    # thread (which would be the script thread)
    ctx = get_script_run_ctx()

    # this is the main runtime, contains all the sessions
    runtime = get_instance()

    if runtime.is_active_session(session_id=ctx.session_id):
        #logging.info(f"{ctx.session_id} is alive.")
        thread.start()
    else:
        if 'uniq' in st.session_state:
            if os.path.isdir(f"removefolder/{st.session_state.uniq}"):
                shutil.rmtree(f"removefolder/{st.session_state.uniq}")
                #logging.info(f"{ctx.session_id} is gone.")
        return

# JavaScript to detect browser exit
EXIT_JS = """
<script>
    window.addEventListener('beforeunload', function (event) {
        fetch('/close_session', {method: 'POST'}).then(response => {
            return response.text();
        }).then(data => {
            console.log(data);
        });
    });
</script>
"""

# Embed the JavaScript in the Streamlit app
#components.html(EXIT_JS)

streamlit_js_eval(js_expressions = EXIT_JS)


def main():

    if 'gcount' not in st.session_state:
        st.session_state.gcount = 0

    if 'uniq' not in st.session_state:
        st.session_state.uniq = secrets.token_urlsafe()

    temp_dir = st.session_state.uniq
    language = st.selectbox(
        "Select language",
        ['Japanese', 'English'],
        index=0
        )

    stopword = ','
    voice = ""
    if language:
        if language == "Japanese":
            stopword = '。'
            voice = st.selectbox(
                "声の性別を選択してください",
                ["女性","男性"],
                index = 0
                )
        elif language == "English":
            stopword = ','
            voice = st.selectbox(
                "Select",
                ["1","2","3","4","5","6","7"],
                index = 0
                )

    all_text = st.text_area('speech text:',
                            value='',
                            height=500,
                            max_chars=40000)

    text = st.empty()

    if 'temp' not in st.session_state:
        st.session_state.temp = ''


    if voice == "女性" and language == 'Japanese':
        VOICE = VOICE1
    elif voice == "1" and language == "English":
        VOICE = VOICE3
    elif voice == "男性" and language == "Japanese":
        VOICE = VOICE2
    elif voice == "2" and language == "English":
        VOICE = VOICE4
    elif voice == "3" and language == "English":
        VOICE = VOICE5
    elif voice == "4" and language == "English":
        VOICE = VOICE6
    elif voice == "5" and language == "English":
        VOICE = VOICE6
    elif voice == "6" and language == "English":
        VOICE = VOICE7
    elif voice == "7" and language == "English":
        VOICE = VOICE8

    if "voice" not in st.session_state:
        st.session_state.voice = VOICE

    async def tts(work):
        seg, save_filepath = work

        try:
            result = edge_tts.Communicate(
                    seg,
                    VOICE,
                    rate='-16%',
                    pitch='-9Hz'
                    )
            await result.save(f"{save_filepath}")

        except Exception as err:
            print(err)

    if all_text:
        alltext = all_text.replace(f"{stopword}", f"{stopword}𓃠")
        if os.path.isdir(f"removefolder/{temp_dir}"):
            if st.session_state.temp != all_text:
                shutil.rmtree(f"removefolder/{temp_dir}")
        my_makedirs(f"removefolder/{temp_dir}/sound")
        count = 0
        for segment_line in alltext.splitlines():
            #if segment_line.strip() == "":
            #    continue
            text.write(segment_line.replace("𓃠", ""))
            match segment_line.strip():
                case '':
                    continue
                case '.':
                    continue
                case _:
                    pass

            for segment_text in segment_line.split('𓃠'):
                print(segment_text)

                if segment_text.strip() != "":
                    count += 1
                    save_filename_ = str(f"{count:06}_")
                    save_filename = save_filename_ + '.mp3'
                    save_filepath = f"removefolder/{temp_dir}/sound/{save_filename}"
                    seg = segment_text.strip()
                    # async function loop
                    asyncio.run(tts([seg, save_filepath]))

        text.empty()

        import glob
        from pydub import AudioSegment
        from pydub import effects
        import pydub.scipy_effects
        from pydub.generators import WhiteNoise

        def add_echo(sound, delay, num_echos, decay):
            echo = sound.fade_out(duration=decay)
            for i in range(num_echos):
                echo_delay = delay * (i + 1)
                echo_decay = decay * (num_echos - i)
                delayed_echo = AudioSegment.silent(duration=echo_delay) + echo.fade_out(duration=echo_decay)
                sound = sound.overlay(delayed_echo)
            return sound

        files = glob.glob(f'removefolder/{temp_dir}/sound/*.mp3')
        files.sort()
        song = AudioSegment.silent(duration=300)
        filter_band_stop = pydub.scipy_effects._mk_butter_filter(
            [5800,9800], 'bandstop', order=8
            )
        progressbar0 = st.empty()
        my_bar0 = progressbar0.progress(0)
        count = 0
        my_makedirs(f"removefolder/{temp_dir}/sound2")
        my_makedirs(f"removefolder/{temp_dir}/sound3")
        for i,x in enumerate(files):
            print(x)
            try:
                new = AudioSegment.from_mp3(x)
                print(len(new))
                # echo efx
                song = song.append(new, crossfade=150)
                song = song.append(AudioSegment.silent(duration=150))
            except Exception as err:
                print(err)
                continue

            if (i+1) % 10 == 0 or i == len(files) -1:
                count += 1
                if len(song) > 1026:
                    song = song.speedup(
                        playback_speed=1.15,
                        chunk_size=120,
                        crossfade=20
                        )
        #        noise = WhiteNoise().to_audio_segment(duration=len(song))
        #        noise = noise - 35
        #        noise = noise.low_pass_filter(2500)
        #        combined = song.overlay(noise)
        #        combined.export(f"i_{count:05}.mp3", format="mp3")
                song.export(f"removefolder/{temp_dir}/sound2/unit_{count:05}.mp3", format="mp3")
                
                song = AudioSegment.silent(duration=200)

            my_bar0.progress(int((i + 1) / len(files) * 100), text="loading...")

        my_bar0.empty()

        files2 = glob.glob(f"removefolder/{temp_dir}/sound2/unit_*.mp3")
        shutil.rmtree(f"removefolder/{temp_dir}/sound")
#        shutil.rmtree(f"removefolder/{temp_dir}/sound2")
#        files2 = glob.glob(f"removefolder/{temp_dir}/sound3/unit_*.mp3")
        files2.sort()
        song = AudioSegment.silent(duration=120)
        #filter_band_stop = pydub.scipy_effects._mk_butter_filter([4000,9800], 'bandstop', order=5)

        progressbar1 = st.empty()
        my_bar1 = progressbar1.progress(0)
        for i,x in enumerate(files2):
            print(x)
            my_bar1.progress(int(((i + 1) / len(files2)) * 100), text="progress...")

            new = AudioSegment.from_mp3(x)
            if (i +1) == len(files2):
                new = new + AudioSegment.silent(duration=2000)
                
            new = new.append(AudioSegment.silent(duration=150))
            """
            noise = WhiteNoise().to_audio_segment(duration=len(new))
            noise = noise - 30
            noise = noise.low_pass_filter(3000)
            noise.export(f"removefolder/{temp_dir}/sound3/{i:05}.mp3", format="mp3")
            # Open an audio file for reading, just like a regular file:
            with AudioFile(f"removefolder/{temp_dir}/sound3/{i:05}.mp3") as f:
                # Open an audio file to write to:
                with AudioFile(f"removefolder/{temp_dir}/sound3/effect_{i:05}.mp3",
                                 'w',
                                 f.samplerate,
                                 f.num_channels) as o:
                    # Read one second of audio at a time, until the file is empty:
                    while f.tell() < f.frames:
                        chunk = f.read(f.samplerate)
                        # Run the audio through our pedalboard:
                        effected = board(chunk, f.samplerate, reset=False)
                        # Write the output to our output file:
                        o.write(effected)

            
            new = add_echo(new, delay=1, num_echos=1, decay=100)
            effected_noise = AudioSegment.from_mp3(f"removefolder/{temp_dir}/sound3/effect_{i:05}.mp3")
            """
            new = new.apply_mono_filter_to_each_channel(filter_band_stop)
            new = new.low_pass_filter(8000)
            new = new.high_pass_filter(220)
            #combined = new.overlay(effected_noise)
            combined = new
            #combined = new.overlay(noise)
            #print(new.duration_seconds)
            #new = new.speedup(playback_speed=1.05, chunk_size=150, crossfade=25)
            song = song.append(combined, crossfade=25)
#            song = song.append(new, crossfade=25)
            song = song.append(AudioSegment.silent(duration=100))

        my_bar1.empty()

#        my_makedirs(f"removefolder/{temp_dir}")
        file_path = f"removefolder/{temp_dir}/all.mp3"
        song.export(file_path, format="mp3")
        del song
        shutil.rmtree(f"removefolder/{temp_dir}/sound3")

        def load_audio(f_path):
            with open(f_path, 'rb') as file:
                audio_data = file.read()

            return audio_data

        if os.path.isfile(file_path):

            mp3_bytes = load_audio(file_path)

            #st.audio(mp3_bytes, format="audio/mpeg", autoplay="true")
            st.audio(mp3_bytes, format="audio/mpeg")
            st.download_button(
                label = 'Download mp3 file',
                data = mp3_bytes,
                file_name = 'audio.mp3',
                mime = 'audio/mpeg')


        if st.session_state.temp != all_text:
            st.session_state.temp = all_text

if __name__ == "__main__":
    heart_beat()
    main()
