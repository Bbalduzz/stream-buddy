import requests
import os, re
import ffmpeg
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
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

    def merge_ts_to_mp4(self, ts_files, output_file):
        with open('src/file_list.txt', 'w') as f:
            for ts_file in ts_files:
                f.write(f"file '{ts_file}'\n")
        (
            ffmpeg
            .input('file_list.txt', format='concat', safe=0)
            .output(output_file, c="copy")
            .run()
        )
        os.remove('file_list.txt')  # Cleanup

    def download_and_decrypt(self, input_url):

        # Folder for decrypt ts file
        os.makedirs("dec_temp_ts", exist_ok=True)

        response = requests.get(input_url)
        if response.status_code != 200: raise Exception(f"Failed to download {input_url}")
        output_filename = input_url.split('/')[-1]
        temp_filename = f"temp_{output_filename}"
        with open(temp_filename, 'wb') as temp_file:
            temp_file.write(response.content)
        self.video_decoder.decrypt_ts_file(temp_filename, f"dec_temp_ts/{output_filename}")
        os.remove(temp_filename)
        return f"dec_temp_ts/{output_filename}"

    def download(self, options):
        url = options["track"]
        media_infos = options["track_infos"]
        if options["subtitles"] != "": subtitles = options["subtitles"]

        m3u8_content = requests.get(url).text
        m3u_info_header = m3u8_content[:200].split("\n")
        x_key = next(line for line in m3u_info_header if line.startswith("#EXT-X-KEY:"))
        enc_method, raw_iv, _ = re.findall(self.ENCRYPTION_INFOS_REGEX, x_key)[0]
    
        if enc_method == "AES-128":
            key = self.get_enc_key(media_infos.internal_id)
            iv = bytes.fromhex(raw_iv.replace("0x", ""))
            self.video_decoder = VideoDecoder(key, iv)

            urls = [line for line in m3u8_content.split('\n') if line.startswith("http://") or line.startswith("https://")]
            del urls[0]

            with ThreadPoolExecutor(max_workers=30) as executor:
                ts_files = list(tqdm(executor.map(self.download_and_decrypt, urls), total=len(urls)))

            self.merge_ts_to_mp4(ts_files, f'{media_infos.title.replace(" ", "_").replace(":", "")}.mp4')

            for file in ts_files: os.remove(file)