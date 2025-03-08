from call_ollama import chat_with_ollama, print_user_message, print_assistant_message
from listen import record_and_transcribe  # 假设您已经将录音和转录功能封装到了 listen.py 的 record_and_transcribe 函数中
import warnings
# Suppress all UserWarnings
warnings.filterwarnings("ignore", category=UserWarning)

def conversation_loop(model_name="qwq:32b"):
    """
    实现与 Ollama 模型的对话循环，用户说完后 Ollama 回答，然后等待用户的下一次提问。

    Args:
        model_name: Ollama 模型名称。
    """
    messages = []  # 初始化对话历史
    print("对话已开始，请开始提问 (按 Ctrl+C 结束对话).")

    try:
        while True:
            # 1. 录音并转录用户的语音
            user_prompt = record_and_transcribe()
            if not user_prompt:
                print("没有检测到语音输入，请重新尝试")
                continue

            print_user_message(user_prompt)
            messages.append({"role": "user", "content": user_prompt})

            # 2. 调用 Ollama 模型获取助手的回复
            print_assistant_message("")
            assistant_response = chat_with_ollama(model_name, messages)
            messages.append({"role": "assistant", "content": assistant_response})
            print("\n")

            #3 等待下一次输入
            k = input("按 Enter 继续...")
            while k != "":
                k = input("按 Enter 继续...")
    except KeyboardInterrupt:
        print("\n对话已结束。")


if __name__ == "__main__":
    conversation_loop()