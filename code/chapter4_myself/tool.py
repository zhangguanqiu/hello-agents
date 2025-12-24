from serpapi import SerpApiClient
from typing import List,Dict,Any
import os 
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()
#定义一个搜索工具
def search(query: str) -> str:
    """
    一个基于SerpApi的实战网页搜索引擎工具。
    它会智能地解析搜索结果,优先返回直接答案或知识图谱信息。
    """

    print(f"正在执行 [SerpApi] 网页搜索: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "SERPAPI_API_KEY 未设置，请在 .env 文件中提供该密钥。"
        
        parasm = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",
            "hl": "zh-CN",
        }

        client = SerpApiClient(parasm)
        results = client.get_dict()

        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            snippets = [
                f"[{i+1} {res.get('title', '')}\n{res.get('snippet', '')}]" for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)
            
        return "未找到相关搜索结果。"
    except Exception as e:
        return f"搜索时出错: {e}"

# 定义一个工具执行器类
class ToolExecutor:
    """
    一个工具执行器,负责管理和执行工具
    """

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self,name: str, description: str, func: callable):
        """
        向工具箱中注册一个工具
        """
        if name in self.tools:
            print(f"工具 {name} 已存在,将被覆盖。")
        self.tools[name] = {
            "description": description,
            "function": func
        }
        print(f"工具 {name} 注册成功。")
    
    def getTool(self,name: str) -> callable:
        """
        根据名称获取一个工具的执行函数
        """
        return self.tools.get(name, {}).get("function")
    

    def getAvailableTools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串
        """
        return "\n".join([
            f"- {name}: {info['description']}" for name, info in self.tools.items()
        ])
        

# --- 工具初始化与使用示例 ---
if __name__ == '__main__':
    # 1. 初始化工具执行器
    toolExecutor = ToolExecutor()

    # 2. 注册我们的实战搜索工具
    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    toolExecutor.registerTool("Search", search_description, search)
    
    # 3. 打印可用的工具
    print("\n--- 可用的工具 ---")
    print(toolExecutor.getAvailableTools())

    # 4. 智能体的Action调用，这次我们问一个实时性的问题
    print("\n--- 执行 Action: Search['英伟达最新的GPU型号是什么'] ---")
    tool_name = "Search"
    tool_input = "英伟达最新的GPU型号是什么"

    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("--- 观察 (Observation) ---")
        print(observation)
    else:
        print(f"错误：未找到名为 '{tool_name}' 的工具。")