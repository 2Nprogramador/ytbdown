import streamlit as st
from pytube import YouTube
import os
from moviepy.editor import VideoFileClip, AudioFileClip
from threading import Thread


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
def combine_audio_video(video_path, audio_path):
    try:
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        final_video = video.set_audio(audio)
        output_path = video_path.replace(".mp4", "_final.mp4")
        final_video.write_videofile(output_path, codec="libx264", fps=45, threads=4,  preset="ultrafast")
        # Processamento paralelo
        return output_path
    except Exception as e:
        st.error(f"Erro ao combinar áudio e vídeo: {e}")
        return None


# Configurar a interface do Streamlit
st.title("YouTube Video Downloader")
st.write("Baixe vídeos do YouTube em até 4K combinados como vídeo e áudio.")

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

        if st.button("Baixar"):
            with st.spinner("Baixando e combinando vídeo e áudio..."):
                video_path, audio_path = download_video(video_url, resolution)
                if video_path and audio_path:
                    st.success(f"Vídeo e áudio baixados com sucesso na resolução {resolution}!")
                    final_video_path = combine_audio_video(video_path, audio_path)
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
