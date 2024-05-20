import subprocess
import os
import threading
import time
from colorama import init, Fore, Style
import signal

init()  # Inicializa colorama para suporte a cores no Windows

def print_elapsed_time(stdscr, elapsed_times):
    """Função para imprimir o tempo decorrido das gravações em tempo real."""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("============================================")
        print("                  GRAVANDO")
        print("============================================")
        for channel_name, elapsed_time in elapsed_times.items():
            if elapsed_time is None:
                print(f"{Fore.RED}{channel_name}: OFFLINE{Style.RESET_ALL}")
            else:
                minutes = elapsed_time // 60
                seconds = elapsed_time % 60
                print(f"{Fore.MAGENTA}{channel_name}:{Style.RESET_ALL} {Fore.GREEN}{minutes} Minutos {seconds} Segundos{Style.RESET_ALL}")
        print("============================================")
        print(f"{Fore.YELLOW}Pressione CTRL + C para encerrar a gravação!{Style.RESET_ALL}")
        time.sleep(5)  # Atraso de 15 segundos entre as atualizações
        for channel_name in elapsed_times:
            if elapsed_times[channel_name] is not None:
                elapsed_times[channel_name] += 5  # Aumenta o tempo decorrido em 15 segundos

def record_live(url, channel_name, elapsed_times):
    """Função para gravar uma live."""
    # Criar a pasta "Videos" se não existir
    if not os.path.exists("Videos"):
        os.makedirs("Videos")
    
    # Comando do youtube-dl para obter a URL do stream
    youtube_dl_command = ["youtube-dl", "-g", url]

    # Executa o comando youtube-dl para obter a URL do stream
    try:
        stream_url = subprocess.check_output(youtube_dl_command, stderr=subprocess.DEVNULL).strip().decode('utf-8')
    except subprocess.CalledProcessError:
        elapsed_times[channel_name] = None
        return

    # Comando do ffmpeg para gravar e comprimir o stream em 720p
    ffmpeg_command = [
        "ffmpeg",
        "-i", stream_url,
        "-s", "1280x720",  # Resolução 720p
        "-c:v", "libx264",  # Compressão de vídeo usando o codec x264
        "-preset", "fast",  # Preset de compressão rápida
        "-crf", "23",  # Qualidade de vídeo (0 - 51). Quanto menor, melhor qualidade
        "-c:a", "copy",  # Copia o áudio sem re-encoding
        "-bsf:a", "aac_adtstoasc",  # Converte o áudio AAC para formato compatível com MP4
        f"Videos/{channel_name}.mp4"  # Salva o vídeo na pasta "Videos"
    ]

    # Executa o comando ffmpeg em um subprocesso
    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Aguarda até que o processo ffmpeg termine
    ffmpeg_process.communicate()  # Espera até que o processo ffmpeg termine

    # Define o tempo decorrido como None após a conclusão da gravação
    elapsed_times[channel_name] = None

def signal_handler(sig, frame):
    """Manipulador de sinal para interromper as gravações e encerrar o programa."""
    print(f"\n{Fore.RED}Gravação encerrada!{Style.RESET_ALL}")
    os._exit(0)  # Encerra o programa imediatamente sem executar os handlers de sinal

# Adiciona o manipulador de sinal para SIGINT (Ctrl + C)
signal.signal(signal.SIGINT, signal_handler)

# Lista de URLs das lives e nomes dos canais
live_urls = [
    {"url": "https://chaturbate.com/_lovelylove_/", "name": "_lovelylove_"},
    {"url": "https://chaturbate.com/daien_halpert/", "name": "daien_halpert"},
    {"url": "https://chaturbate.com/artseduction/", "name": "artseduction"},
    # Adicione mais URLs e nomes de canais conforme necessário
]

# Dicionário para armazenar os tempos decorridos de cada canal
elapsed_times = {live_info["name"]: 0 for live_info in live_urls}

# Inicia a thread para imprimir o tempo decorrido
elapsed_time_thread = threading.Thread(target=print_elapsed_time, args=(None, elapsed_times))
elapsed_time_thread.daemon = True
elapsed_time_thread.start()

# Inicia a gravação para cada live em uma thread separada
threads = []
for live_info in live_urls:
    url = live_info["url"]
    channel_name = live_info["name"]
    thread = threading.Thread(target=record_live, args=(url, channel_name, elapsed_times))
    thread.start()
    threads.append(thread)

# Espera que todas as threads terminem
for thread in threads:
    thread.join()
