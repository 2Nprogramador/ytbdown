import streamlit as st
from pytube import YouTube
import os
from moviepy.editor import VideoFileClip, AudioFileClip
from threading import Thread


# Função para converter tempo em minutos e segundos para segundos
def time_to_seconds(minutes, seconds):
    return minutes * 60 + seconds


# Função para converter segundos para minutos e segundos
def seconds_to_time(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return minutes, seconds


# Função para baixar o vídeo do YouTube em alta resolução
def download_video(url, resolution):
    try:
        yt = YouTube(url)
        video_stream = yt.streams.filter(res=resolution, file_extension='mp4', only_video=True).first()
        audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').first()
        if video_stream and audio_stream:
            video_path = f"downloads/video_{resolution}.mp4"
            audio_path = "downloads/audio.mp4"

            # Download do vídeo e do áudio em paralelo
            t1 = Thread(target=video_stream.download, args=("downloads", f"video_{resolution}.mp4"))
            t2 = Thread(target=audio_stream.download, args=("downloads", "audio.mp4"))
            t1.start()
            t2.start()
            t1.join()
            t2.join()

            return video_path, audio_path
        else:
            st.error(f"Resolução {resolution} não disponível.")
            return None, None
    except Exception as e:
        st.error(f"Erro ao baixar o vídeo: {e}")
        return None, None


# Função para combinar áudio e vídeo
def combine_audio_video(video_path, audio_path, start_time=None, end_time=None):
    try:
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        final_video = video.set_audio(audio)

        # Aplicar corte se os tempos forem fornecidos
        if start_time is not None and end_time is not None:
            final_video = final_video.subclip(start_time, end_time)

        output_path = video_path.replace(".mp4", "_final.mp4")
        final_video.write_videofile(output_path, codec="libx264", fps=60, threads=4, preset="fast")

        return output_path
    except Exception as e:
        st.error(f"Erro ao combinar áudio e vídeo: {e}")
        return None


# Configurar a interface do Streamlit
st.title("YouTube Video Downloader")
st.write("Baixe vídeos do YouTube em ALTA DEFINIÇÃO, faça cortes e poste nas Redes Sociais!")

# Input do URL do vídeo do YouTube
video_url = st.text_input("Insira a URL do vídeo do YouTube:")

if video_url:
    try:
        yt = YouTube(video_url)
        video_id = yt.video_id
        video_embed_url = f"https://www.youtube.com/embed/{video_id}"

        # Exibir o vídeo usando um iframe
        st.video(video_embed_url)

        resolutions = [stream.resolution for stream in
                       yt.streams.filter(only_video=True, file_extension='mp4').order_by('resolution')]
        resolution = st.selectbox("Selecione a resolução para download:", resolutions)

        # Opção para baixar o vídeo completo ou cortado
        download_option = st.radio("Você quer baixar o vídeo completo ou cortar o vídeo final?",
                                   ("Completo", "Cortado"))

        start_time = None
        end_time = None

        if download_option == "Cortado":
            duration = yt.length
            st.write(f"Duração total do vídeo: {duration // 60} minutos e {duration % 60} segundos")

            # Slider de início do corte
            start_minutes = st.slider("Minutos de início do corte:", 0, duration // 60, 0)
            start_seconds = st.slider("Segundos de início do corte:", 0, 59, 0)
            start_time = time_to_seconds(start_minutes, start_seconds)

            # Slider de término do corte
            end_minutes = st.slider("Minutos de término do corte:", 0, duration // 60, duration // 60)
            end_seconds = st.slider("Segundos de término do corte:", 0, 59, duration % 60)
            end_time = time_to_seconds(end_minutes, end_seconds)

            if end_time <= start_time:
                st.error("O tempo final deve ser maior que o tempo inicial.")

        if st.button("Baixar"):
            with st.spinner("Baixando e combinando vídeo e áudio..."):
                video_path, audio_path = download_video(video_url, resolution)
                if video_path and audio_path:
                    st.success(f"Vídeo e áudio baixados com sucesso na resolução {resolution}!")
                    final_video_path = combine_audio_video(video_path, audio_path, start_time, end_time)
                    st.success(f"Vídeo e áudio combinados com sucesso na resolução {resolution}!")

                    # Disponibilizar download do arquivo combinado
                    with open(final_video_path, "rb") as file:
                        st.download_button(
                            label="Clique aqui para baixar o vídeo combinado",
                            data=file,
                            file_name=os.path.basename(final_video_path),
                            mime="video/mp4"
                        )

                    # Remover arquivos temporários
                    os.remove(video_path)
                    os.remove(audio_path)
    except Exception as e:
        st.error(f"Erro ao processar o vídeo: {e}")

# Criar diretório de downloads, se não existir
if not os.path.exists('downloads'):
    os.makedirs('downloads')
