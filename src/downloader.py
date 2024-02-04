import inspect
from itertools import repeat
import requests
import os, re, shutil
import ffmpeg
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class VideoDecoder(object):
    def __init__(self, key, iv):
        self.key = key
        self.iv = iv

    def decrypt_ts_file(self, input_filename, output_filename):
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend()).decryptor()
        with open(input_filename, 'rb') as infile, open(output_filename, 'wb') as outfile:
            for chunk in iter(lambda: infile.read(1024 * 16), b''):
                outfile.write(cipher.update(chunk))
            outfile.write(cipher.finalize())

class VideoDownloader():
    ENCRYPTION_INFOS_REGEX = r'METHOD=(.*?),.*?IV=(.*?)(,|$)'

    def __init__(self):
        self.video_decoder: VideoDecoder

    def get_enc_key(self, internal_id):
        r = requests.get('https://vixcloud.co/storage/enc.key', headers={'Referer': f'https://vixcloud.co/embed/{internal_id}'})
        return r.content

    def create_file_list(self, input_folder, file_list_name='dec_temp_ts/filelist.txt'):
        with open(file_list_name, 'w') as file:
            for filename in sorted(os.listdir(input_folder)):
                if filename.endswith('.ts'):
                    # Use absolute paths to avoid confusion
                    file_path = os.path.abspath(os.path.join(input_folder, filename))
                    file.write(f"file '{file_path}'\n")


    def merge_audio_video(self, video_folder, audio_folder, output_folder):
        # Ensure output folder exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Get the list of video files
        video_files = sorted(os.listdir(video_folder))
        audio_files = sorted(os.listdir(audio_folder))

        for video_file, audio_file in zip(video_files, audio_files):
            video_path = os.path.join(video_folder, video_file)
            audio_path = os.path.join(audio_folder, audio_file)
            final_output = os.path.join(output_folder, video_file)  # Change the extension if needed

            # Merge process
            input_video = ffmpeg.input(video_path)
            input_audio = ffmpeg.input(audio_path)
            (
                ffmpeg
                .output(input_video, input_audio, final_output, vcodec='copy', acodec='copy')
                .run(overwrite_output=True)
            )

            # Optionally delete the original files
            os.remove(video_path)
            os.remove(audio_path)

    def concatenate_to_mp4(self, file_list, output_file):
        (
            ffmpeg
            .input(file_list, format='concat', safe=0)
            .output(output_file, loglevel="quiet", codec='copy')
            .run()
        )
        shutil.rmtree(f"{file_list.split('/')[0]}/output")


    def download_and_decrypt(self, input_url, type):
        response = requests.get(input_url)
        if response.status_code != 200: raise Exception(f"Failed to download {input_url}")
        output_filename = input_url.split('/')[-1]
        temp_filename = f"temp_{output_filename}"
        with open(temp_filename, 'wb') as temp_file:
            temp_file.write(response.content)
        self.decoder.decrypt_ts_file(temp_filename, f"dec_temp_ts/{type}/{output_filename}")
        os.remove(temp_filename)
        return f"dec_temp_ts/{type}/{output_filename}"

    def simple_download(self, input_url):
        response = requests.get(input_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download {input_url}")
        output_filename = input_url.split('/')[-1]
        with open(f"dec_temp_ts/{output_filename}", 'wb') as file:
            file.write(response.content)
        return f"dec_temp_ts/{output_filename}"

    def download(self, options):
        if not os.path.exists("dec_temp_ts"):
            os.makedirs("dec_temp_ts/video")
            os.makedirs("dec_temp_ts/audio")
            os.makedirs("dec_temp_ts/output")
        video_ts_files, audio_ts_files = [], []

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_segment = {
                executor.submit(self.process_segment, options["track"], options["track_infos"], "video"): "video",
                executor.submit(self.process_segment, options["audio"], options["track_infos"], "audio"): "audio",
            }

            for future in as_completed(future_to_segment):
                segment_type = future_to_segment[future]
                ts_files = future.result()  # Retrieve the actual result from the future here
                if segment_type == "video":
                    video_ts_files = ts_files
                elif segment_type == "audio":
                    audio_ts_files = ts_files

        # File names
        base_filename = f'{options["track_infos"]["title"].replace(" ", "_").replace(":", "")}'
        final_output = f"{base_filename}.mp4"

        # Merge section: vidio ts + audio ts -> ts -> merge ts -> mp4
        self.merge_audio_video('dec_temp_ts/video', 'dec_temp_ts/audio', 'dec_temp_ts/output')
        self.create_file_list('dec_temp_ts/output')
        self.concatenate_to_mp4('dec_temp_ts/filelist.txt', final_output)
        shutil.rmtree("dec_temp_ts")

    def process_segment(self, m3u8_url, media_infos, segment_type):
        m3u8_content = requests.get(m3u8_url).text
        is_encrypted = "#EXT-X-KEY" in m3u8_content

        if is_encrypted:
            x_key = next(line for line in m3u8_content.split('\n') if line.startswith("#EXT-X-KEY:"))
            enc_method, raw_iv, _ = re.findall(self.ENCRYPTION_INFOS_REGEX, x_key)[0]

            if enc_method == "AES-128":
                key = self.get_enc_key(media_infos["id"])
                iv = bytes.fromhex(raw_iv.replace("0x", ""))
                self.decoder = VideoDecoder(key, iv)

        urls = [line for line in m3u8_content.split('\n') if line.startswith("http://") or line.startswith("https://")]
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = []
            if is_encrypted:
                futures.extend([executor.submit(self.download_and_decrypt, url, segment_type) for url in urls])
            else:
                futures.extend([executor.submit(self.simple_download, url, segment_type) for url in urls])
            progress = tqdm(total=len(futures), unit="bytes", unit_scale=True, desc=f'Downloading {segment_type}')

            ts_files = []
            for future in as_completed(futures):
                progress.update(1)
                try:
                    result = future.result()
                    ts_files.append(result)
                except Exception as e:
                    print(f"A task in the thread pool raised an exception: {e}")
            progress.close()

        return ts_files
