from autogen_ext.models.openai import OpenAIChatCompletionClient
import os
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console
import asyncio
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent

# 加载 .env 文件中的环境变量
load_dotenv()
##创建 OpenAI 模型客户端用于测试
def create_openai_model_client():
    """创建 OpenAI 模型客户端用于测试"""
    model = os.getenv("LLM_MODEL_ID")
    apiKey = os.getenv("LLM_API_KEY")
    baseUrl = os.getenv("LLM_BASE_URL")
    timeout = int(os.getenv("LLM_TIMEOUT",60))

    model_info={
        "funcation_calling": True,
        "max_tokens":20480,
        "json_output": False,
        "function_calling": False,
        "vision": False,
        "family": "deepseek",
        "structured_output": True,
    }
    return OpenAIChatCompletionClient(model=model,api_key=apiKey,base_url=baseUrl, model_info=model_info)

##构建智能体
def create_product_manager(model_client):
    """创建产品经理智能体"""
    system_message = """你是一位经验丰富的产品经理，专门负责软件产品的需求分析和项目规划。

你的核心职责包括：
1. **需求分析**：深入理解用户需求，识别核心功能和边界条件
2. **技术规划**：基于需求制定清晰的技术实现路径
3. **风险评估**：识别潜在的技术风险和用户体验问题
4. **协调沟通**：与工程师和其他团队成员进行有效沟通

当接到开发任务时，请按以下结构进行分析：
1. 需求理解与分析
2. 功能模块划分
3. 技术选型建议
4. 实现优先级排序
5. 验收标准定义

请简洁明了地回应，并在分析完成后说"请工程师开始实现"。"""
    return AssistantAgent(
        name="ProductManager", 
        model_client=model_client, 
        system_message=system_message,
        model_client_stream=True,
        )


def create_engineer(model_client):
    """创建软件工程师智能体"""
    system_message = """你是一位资深的软件工程师，擅长 Python 开发和 Web 应用构建。

你的技术专长包括：
1. **Python 编程**：熟练掌握 Python 语法和最佳实践
2. **Web 开发**：精通 Streamlit、Flask、Django 等框架
3. **API 集成**：有丰富的第三方 API 集成经验
4. **错误处理**：注重代码的健壮性和异常处理

当收到开发任务时，请：
1. 仔细分析技术需求
2. 选择合适的技术方案
3. 编写完整的代码实现
4. 添加必要的注释和说明
5. 考虑边界情况和异常处理

请提供完整的可运行代码，并在完成后说"请代码审查员检查"。"""

    return AssistantAgent(
        name="Engineer",
        model_client=model_client,
        system_message=system_message,
        model_client_stream=True,
    )

def create_code_reviewer(model_client):
    """创建代码审查员智能体"""
    system_message = """你是一位经验丰富的代码审查专家，专注于代码质量和最佳实践。

你的审查重点包括：
1. **代码质量**：检查代码的可读性、可维护性和性能
2. **安全性**：识别潜在的安全漏洞和风险点
3. **最佳实践**：确保代码遵循行业标准和最佳实践
4. **错误处理**：验证异常处理的完整性和合理性

审查流程：
1. 仔细阅读和理解代码逻辑
2. 检查代码规范和最佳实践
3. 识别潜在问题和改进点
4. 提供具体的修改建议
5. 评估代码的整体质量

请提供具体的审查意见，完成后说"代码审查完成，请用户代理测试"。"""

    return AssistantAgent(
        name="CodeReviewer",
        model_client=model_client,
        system_message=system_message,
        model_client_stream=True,
    )


def create_user_proxy():
    """创建用户代理智能体"""
    return UserProxyAgent(
        name="UserProxy",
        description="""用户代理，负责以下职责：
1. 代表用户提出开发需求
2. 执行最终的代码实现
3. 验证功能是否符合预期
4. 提供用户反馈和建议

完成测试后请回复 TERMINATE。""",
    )



## 定义团队聊天和协作规则


async def run_software_development_team():
    """运行软件开发团队协作"""
    
    print("正在初始化模型客户端...")
    model_client = create_openai_model_client()
    
    print("正在创建产品经理智能体...")
    product_manager = create_product_manager(model_client)
    
    print("正在创建软件工程师智能体...")
    engineer = create_engineer(model_client)
    
    print("正在创建代码审查员智能体...")
    code_reviewer = create_code_reviewer(model_client)
    
    print("正在创建用户代理智能体...")
    user_proxy = create_user_proxy()

    # 定义终止条件
    termination = TextMentionTermination("TERMINATE")
    
    print("正在组建软件开发团队...")
    team_chat = RoundRobinGroupChat(
        participants=[product_manager, engineer, code_reviewer, user_proxy],
        termination_condition=termination,
        max_turns=20,
    )

    task = """我们需要开发爬虫应用，具体要求如下：

核心功能：
- 能够根据输入的 URL 抓取网页内容
- 解析并提取指定的数据字段
- 将提取的数据保存为 CSV 文件

技术要求：
- 使用 Python 语言开发
- 使用 requests 库进行网页请求
- 使用 BeautifulSoup 库进行 HTML 解析
- 使用 pandas 库保存数据为 CSV 格式


请团队协作完成这个任务，从需求分析到最终实现。"""
    
    # 启动团队协作
    print("启动AutoGen软件开发团队协作...")
    print("=" * 60)

    # 使用 Console 来显示对话过程
    result = await Console(team_chat.run_stream(task=task))
    print("\n" + "=" * 60)
    print("团队协作完成！")
    return result


if __name__ == "__main__":
    try:
        # 运行异步协作流程
        result = asyncio.run(run_software_development_team())

        print(f"\n协作结果摘要：")
        print(f"- 参与智能体数量：4个")
        print(f"- 任务完成状态：{'成功' if result else '需要进一步处理'}")
    except ValueError as e:
        print(f"配置错误：{e}")
        print("请检查 .env 文件中的配置是否正确")
    except Exception as e:
        print(f"运行错误：{e}")
        import traceback
        traceback.print_exc()

