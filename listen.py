import whisper
import wave
import pyaudio
import numpy as np
import webrtcvad
import time

# 加载 Whisper 模型（首次运行时会自动下载模型）
model = whisper.load_model("small")  # 可选模型：tiny, base, small, medium, large

# 录音参数
FORMAT = pyaudio.paInt16  # 16位深度
CHANNELS = 1  # 单声道
RATE = 16000  # 采样率
# CHUNK = 1024  # 每个缓冲区的帧数 #调整chunk
FRAME_DURATION = 30 #ms
CHUNK = int(RATE * FRAME_DURATION / 1000)

# VAD 参数
VAD_AGGRESSIVENESS = 3  # VAD 灵敏度，0 (最低) 到 3 (最高)
SILENCE_DURATION = 2.5  # 静音时长阈值（秒）

def record_and_transcribe():
    """录音，检测静音并转录语音。"""

    # 初始化 PyAudio
    audio = pyaudio.PyAudio()

    # 初始化 VAD
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)

    # 开始录音
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

    print("倾听中...")
    frames = []
    last_voice_time = time.time()
    try:
        while True:
            data = stream.read(CHUNK)
            frames.append(data)

            # convert data to np array for vad
            audio_data = np.frombuffer(data, dtype=np.int16)
            # convert np array to bytes
            audio_bytes = audio_data.tobytes()

            is_speech = vad.is_speech(audio_bytes, RATE)

            if is_speech:
                last_voice_time = time.time()  # 更新最后检测到声音的时间
                print("说话中", end="\r")

            else:
                # 计算静音时长
                silence_duration = (time.time() - last_voice_time)
                print(f"静音时长 {silence_duration:.2f} 秒", end="\r")
                if silence_duration >= SILENCE_DURATION:
                    # print(f"检测到 {SILENCE_DURATION} 秒的静音，停止录音。")
                    break

    except KeyboardInterrupt:
        print("手动停止录音")

    finally:
        print("结束倾听")

        # 停止录音
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # 将录音数据保存为 WAV 文件
        filename = "output.wav"
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))

        # 使用 Whisper 识别语音
        result = model.transcribe(filename)
        # print("识别结果：", result["text"])
        return result["text"]