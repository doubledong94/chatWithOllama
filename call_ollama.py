import requests
import json
import sys

def chat_with_ollama(model, messages):
    """
    使用 Ollama Chat API 进行对话，支持多轮对话历史。

    Args:
        model: Ollama 模型名称。
        messages: 消息列表，格式为 [{"role": "user", "content": "用户消息"}, {"role": "assistant", "content": "助手消息"}, ...]
            例如：
            [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好！"},
                {"role": "user", "content": "你叫什么名字?"}
            ]

    Returns:
        返回助手的新消息内容。
    """
    url = "http://localhost:11434/api/chat"
    data = {
        "model": model,
        "messages": messages,
        "stream": True  # 设置为 True 以启用流式响应
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, data=json.dumps(data), headers=headers, stream=True)
        response.raise_for_status()  # 检查请求是否成功

        assistant_message = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                json_data = json.loads(decoded_line)
                text_chunk = json_data.get("message", {}).get("content", "")
                # print(text_chunk, end="", flush=True)  # 实时打印每个文本块
                sys.stdout.write(text_chunk)
                sys.stdout.flush()
                assistant_message += text_chunk # 积累assistant的回答

                if json_data.get('done', False):  # 判断是否完成
                    print()
                    break

        return assistant_message
    except requests.exceptions.RequestException as e:
        print(f"请求出错：{e}")
        return ""
    except json.JSONDecodeError as e:
        print(f"JSON 解析出错: {e}")
        return ""

def print_user_message(message):
    """打印用户消息，使用绿色和粗体样式。"""
    print(f"\033[92m\033[1mUser: {message}\033[0m")

def print_assistant_message(message):
    """打印助手消息，使用蓝色和粗体样式。"""
    # print(f"\033[94m\033[1mAssistant: {message}\033[0m")
    print(f"\033[94m\033[1mAssistant: \033[0m", end="")


# # 示例用法
# model_name = "qwq:32b"  # 替换成你本地 Ollama 运行的模型名称
#
# # 初始化对话历史
# messages = []
#
# # 第一次提问
# user_prompt1 = "请问中国第一个朝代是什么？"
# print_user_message(user_prompt1)
# messages.append({"role": "user", "content": user_prompt1})
# print_assistant_message("")
# assistant_response1 = chat_with_ollama(model_name, messages)
# messages.append({"role": "assistant", "content": assistant_response1})
#
# # 第二次提问，带上历史
# user_prompt2 = "那第二个呢？"
# print_user_message(user_prompt2)
# messages.append({"role": "user", "content": user_prompt2})
# print_assistant_message("")
# assistant_response2 = chat_with_ollama(model_name, messages)
# messages.append({"role": "assistant", "content": assistant_response2})
#
# # 第三次提问，继续带上历史
# user_prompt3 = "第三个呢？"
# print_user_message(user_prompt3)
# messages.append({"role": "user", "content": user_prompt3})
# print_assistant_message("")
# assistant_response3 = chat_with_ollama(model_name, messages)
# messages.append({"role": "assistant", "content": assistant_response3})