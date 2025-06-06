import os
import openai
import sys

# 将API密钥和URL直接写在脚本中进行测试，稍后可以移动到环境变量中
# 请在此处填入您的API密钥
API_KEY = "在这里填入您的Deepseek API密钥"

# 配置OpenAI客户端
openai.api_key = API_KEY
# 如果Deepseek API有特定的API基础URL，请在这里设置，否则请注释掉这行
openai.api_base = "https://api.deepseek.com/v1/chat/completions"


def test_api():
    try:
        print("开始测试Deepseek API连接...")

        # 发送一个简单的测试请求
        response = openai.ChatCompletion.create(
            # 如果Deepseek API需要指定模型，请取消注释下一行并填入正确的模型名称
            # model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个AI助手。"},
                {"role": "user", "content": "你好，请问今天天气怎么样？"},
            ]
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
