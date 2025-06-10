import os
import openai
import sys


API_KEY = "sk-lismnbjyqkujzycyjwucvttjdxgatrhysmnrfvdmowchsbot"

# 配置OpenAI客户端
openai.api_key = API_KEY
openai.api_base = "https://api.siliconflow.cn/v1"


def test_api():
    try:
        print("开始测试 API连接...")

        # 发送一个简单的测试请求
        response = openai.ChatCompletion.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的财务信息提取助手，精通中文财务语言处理，擅长从自然语言中识别记账意图并提取关键财务实体。",
                },
                {"role": "user", "content": "你好，我今天买水花了6块钱"},
            ],
        )

        # 打印API响应
        print("\n成功连接到API！")
        print("\n响应内容:")
        print(response.choices[0].message.content)

        # 打印完整响应对象（可选，用于调试）
        print("\n完整响应对象:")
        print(response)

        return True

    except Exception as e:
        print("\nAPI测试失败，错误信息:")
        print(e)
        return False


if __name__ == "__main__":
    success = test_api()
    if success:
        print("\n测试成功！您的API配置正确。")
    else:
        print("\n测试失败！请检查API密钥和配置。")
