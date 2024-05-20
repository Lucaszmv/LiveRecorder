import subprocess
import os
import threading
import time
from colorama import init, Fore, Style
import signal

init()  # Inicializa colorama para suporte a cores no Windows

def print_elapsed_time(elapsed_times):
    """Função para imprimir o tempo decorrido das gravações em tempo real."""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("============================================")
        print("                  GRAVANDO")
        print("============================================")
        for channel_name, elapsed_time in elapsed_times.items():
            if elapsed_time == -1:
                print(f"{Fore.BLUE}Obtendo URL do stream para {channel_name}...{Style.RESET_ALL}")
            elif elapsed_time is None:
                print(f"{Fore.RED}{channel_name}: OFFLINE{Style.RESET_ALL}")
            else:
                minutes = elapsed_time // 60
                seconds = elapsed_time % 60
                print(f"{Fore.MAGENTA}{channel_name}:{Style.RESET_ALL} {Fore.GREEN}{minutes} Minutos {seconds} Segundos{Style.RESET_ALL}")
        print("============================================")
        print(f"{Fore.YELLOW}Pressione CTRL + C para encerrar a gravação!{Style.RESET_ALL}")
        time.sleep(5)  # Atraso em segundos entre as atualizações
        for channel_name in elapsed_times:
            if elapsed_times[channel_name] is not None and elapsed_times[channel_name] != -1:
                elapsed_times[channel_name] += 5  # Aumenta o tempo decorrido em segundos

def get_stream_url(url, channel_name):
    """Função para obter a URL do stream usando yt-dlp."""
    yt_dlp_command = ["yt-dlp", "-g", url]
    try:
        stream_url = subprocess.check_output(yt_dlp_command, stderr=subprocess.STDOUT).strip().decode('utf-8')
        return stream_url
    except subprocess.CalledProcessError as e:
        pass  # Ignorar o erro e continuar sem imprimir a mensagem de erro
    except FileNotFoundError:
        print(f"{Fore.RED}yt-dlp não encontrado. Verifique se está instalado e no PATH.{Style.RESET_ALL}")
    return None

def record_live(url, channel_name, elapsed_times):
    """Função para gravar uma live."""
    if not os.path.exists("Videos"):
        os.makedirs("Videos")

    elapsed_times[channel_name] = -1  # Indica que está tentando obter a URL do stream

    retries = 2 # Número de tentativas
    for attempt in range(retries):
        stream_url = get_stream_url(url, channel_name)
        if stream_url:
            break
        time.sleep(2)  # Espera em segundos antes de tentar novamente
    else:
        elapsed_times[channel_name] = None
        return

    elapsed_times[channel_name] = 0  # Inicia o contador de tempo decorrido

    video_number = 1
    while True:
        video_filename = f"Videos/{channel_name}_{video_number}.mp4"
        if not os.path.exists(video_filename):
            break
        video_number += 1

    ffmpeg_log_file = f"Videos/{channel_name}_{video_number}_ffmpeg.log"

    ffmpeg_command = [
        "ffmpeg",
        "-i", stream_url,
        "-s", "1280x720",
        "-c:v", "libx265",
        "-preset", "veryfast",
        "-crf", "27",
        "-c:a", "copy",
        "-bsf:a", "aac_adtstoasc",
        video_filename
    ]

    try:
        print(f"{Fore.BLUE}Iniciando gravação para {channel_name}...{Style.RESET_ALL}")
        with open(ffmpeg_log_file, 'w') as log_file:
            ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=log_file, stderr=log_file)
            ffmpeg_process.communicate()
        print(f"{Fore.GREEN}Gravação finalizada para {channel_name}.{Style.RESET_ALL}")
    except FileNotFoundError:
        print(f"{Fore.RED}ffmpeg não encontrado. Verifique se está instalado e no PATH.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Erro ao gravar {channel_name}: {e}{Style.RESET_ALL}")
    finally:
        elapsed_times[channel_name] = None

def signal_handler(sig, frame):
    """Manipulador de sinal para interromper as gravações e encerrar o programa."""
    print(f"\n{Fore.CYAN}Gravação encerrada!{Style.RESET_ALL}")
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)

live_urls = [
    {"url": "https://www.twitch.tv/canalname1", "name": "canalname1"},
    {"url": "https://www.youtube.com/channelname2", "name": "channelname2"},
]

elapsed_times = {live_info["name"]: -1 for live_info in live_urls}  # Inicializa com -1 para indicar a obtenção da URL

elapsed_time_thread = threading.Thread(target=print_elapsed_time, args=(elapsed_times,))
elapsed_time_thread.daemon = True
elapsed_time_thread.start()

# Limita o número de threads
max_threads = 4
threads = []
for live_info in live_urls:
    url = live_info["url"]
    channel_name = live_info["name"]
    while threading.active_count() >= max_threads:
        time.sleep(5)  # Aguarda até que haja espaço disponível para outra thread
    thread = threading.Thread(target=record_live, args=(url, channel_name, elapsed_times))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()
