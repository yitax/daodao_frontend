import requests
import json
import os
from datetime import datetime

# 配置参数
BASE_URL = "http://localhost:8000"  # 后端服务器地址
USERNAME = "test"  # 测试用户名
PASSWORD = "password"  # 测试密码


def log(message):
    """打印带时间戳的日志"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def test_backend():
    log("开始测试后端API...")

    # 1. 测试服务器是否在线
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            log("✅ 服务器在线，可以访问API文档")
        else:
            log(f"❌ 服务器响应异常: {response.status_code}")
            return
    except Exception as e:
        log(f"❌ 无法连接到服务器: {e}")
        log("请确保后端服务器已启动，并在正确的端口上运行")
        return

    # 2. 尝试用户登录
    try:
        log("尝试用户登录...")
        login_response = requests.post(
            f"{BASE_URL}/users/token", data={"username": USERNAME, "password": PASSWORD}
        )

        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            if token:
                log("✅ 登录成功，获取到令牌")
                headers = {"Authorization": f"Bearer {token}"}
            else:
                log("❌ 登录响应异常，未获取到令牌")
                return
        else:
            log(f"❌ 登录失败: {login_response.status_code} - {login_response.text}")
            log("请确认用户名和密码是否正确，或检查用户是否存在")
            return
    except Exception as e:
        log(f"❌ 登录请求异常: {e}")
        return

    # 3. 测试聊天API
    try:
        log("测试聊天API...")
        chat_response = requests.post(
            f"{BASE_URL}/chat",
            headers=headers,
            json={"content": "今天午饭花了35元", "personality_id": 1},
        )

        if chat_response.status_code == 200:
            chat_data = chat_response.json()
            log("✅ 聊天API响应成功")
            log(f"AI回复: {chat_data.get('message', {}).get('content', '无内容')}")

            # 检查是否提取到财务信息
            if chat_data.get("needs_confirmation"):
                log("✅ 成功提取财务信息")
                extracted_info = chat_data.get("extracted_info", {})
                log(
                    f"提取信息: {json.dumps(extracted_info, ensure_ascii=False, indent=2)}"
                )

                # 4. 测试交易确认API
                message_id = chat_data.get("message", {}).get("id")
                if message_id:
                    log("测试交易确认API...")
                    confirm_response = requests.post(
                        f"{BASE_URL}/chat/confirm-transaction",
                        headers=headers,
                        json={
                            "message_id": message_id,
                            "confirm": True,
                            "type": extracted_info.get("type", "expense"),
                            "amount": float(extracted_info.get("amount", 35)),
                            "description": extracted_info.get("description", "午饭"),
                            "category": extracted_info.get("category", "餐饮美食"),
                            "date": extracted_info.get(
                                "date", datetime.now().strftime("%Y-%m-%d")
                            ),
                        },
                    )

                    if confirm_response.status_code == 200:
                        confirm_data = confirm_response.json()
                        log("✅ 交易确认API响应成功")
                        log(
                            f"交易确认结果: {json.dumps(confirm_data, ensure_ascii=False, indent=2)}"
                        )
                    else:
                        log(
                            f"❌ 交易确认失败: {confirm_response.status_code} - {confirm_response.text}"
                        )
                else:
                    log("❌ 无法获取消息ID，跳过交易确认测试")
            else:
                log("⚠️ 未提取到财务信息，跳过交易确认测试")
        else:
            log(
                f"❌ 聊天API请求失败: {chat_response.status_code} - {chat_response.text}"
            )
    except Exception as e:
        log(f"❌ 聊天API请求异常: {e}")

    log("后端API测试完成")


if __name__ == "__main__":
    test_backend()
