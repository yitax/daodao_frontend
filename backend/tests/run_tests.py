"""
叨叨记账应用后端测试运行脚本
运行方法：从backend目录下执行 python -m tests.run_tests
"""

import os
import sys
import pytest

# 确保当前目录是backend文件夹
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# 打印测试环境信息
print("=" * 50)
print("叨叨记账应用后端单元测试")
print("=" * 50)
print(f"Python版本: {sys.version}")
print(f"pytest版本: {pytest.__version__}")
print(f"工作目录: {os.getcwd()}")
print(f"后端目录: {backend_dir}")
print(f"测试目录: {current_dir}")
print("=" * 50)


def run_tests():
    """运行所有测试"""
    # 设置测试选项
    args = [
        # 测试文件目录
        current_dir,
        # 显示详细输出
        "-v",
        # 生成测试报告
        "--html=test_report.html",
        # 在测试过程中显示prints内容
        "-s",
        # 生成覆盖率报告
        "--cov=app",
        # 覆盖率报告格式
        "--cov-report=html",
        # 覆盖率报告目录
        "--cov-report=term",
    ]

    # 执行测试
    print("开始执行测试...")
    return_code = pytest.main(args)

    # 显示测试结果
    if return_code == 0:
        print("\n✅ 所有测试通过!")
    else:
        print(f"\n❌ 测试失败! 返回代码: {return_code}")

    # 显示测试报告路径
    report_path = os.path.join(os.getcwd(), "test_report.html")
    coverage_path = os.path.join(os.getcwd(), "htmlcov", "index.html")
    print(f"\n测试报告: {report_path}")
    print(f"覆盖率报告: {coverage_path}")

    return return_code


if __name__ == "__main__":
    # 运行测试
    exit_code = run_tests()
    # 使用适当的退出码
    sys.exit(exit_code)
