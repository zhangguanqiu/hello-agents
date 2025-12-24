AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 可用工具:
- `get_weather(city: str)`: 获取指定城市的实时天气。
- `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点。

# 行动格式:
你的回答必须严格遵循以下格式。首先是你的思考过程，然后是你要执行具体的行动。
Thought: [这里是你的思考过程和下一步计划]
Action: [这里是你要调用的工具，格式为 function_name(arg_name="arg_value")]

# 任务完成:
当你收集到足够的信息，能够回答用户的最终问题时，你必须在`Action:`字段后使用 `finish(answer="...")` 来输出最终答案。

请开始吧！
"""

import requests
from tavily import TavilyClient
import os
from openai import OpenAI
import re

def get_weather(city: str) -> str:
    """
    通过调用 wttr.in API 获取城市的实时天气信息。
    """
    # API端点,我们请求JSON格式的数据
    url = f"https://wttr.in/{city}?format=j1"

    try:
        # 发起网络请求
        response = requests.get(url)
        # 检查响应状态码是否为200 (成功)
        response.raise_for_status()
        # 解析返回的JSON数据
        data = response.json()

        # 提取当前天气状况
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']

        # 格式化成自然语言返回
        return f"{city}当前天气：{weather_desc}，气温{temp_c}摄氏度"
    except requests.exceptions.RequestException as e:
        # 处理网络错误
        return f"错误：查询天气时遇到网络问题 - {e}"
    


def get_attraction(city: str, weather: str) -> str:
    """
    使用 Tavily API 搜索指定城市的景点。
    """
    #1、从环境变量中读取API密钥
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "错误：未配置TAVILY_API_KEY。"

    #2、创建 Tavily 客户端实例
    tavily = TavilyClient(api_key=api_key)

    #3、构造一个精确的查询
    query = f"'{city}'在'{weather}'天气下最值得去的旅游景点推荐及理由"

    try:
        # 4、调用API,include_answer=True会返回一个综合性的回答
        response = tavily.search(query,search_depth="basic",include_answer=True)

        # 5、 Tavily返回的结果已经非常干净，可以直接使用
        # results['answer'] 是一个基于所有搜索结果的总结性回答
        if response.get("answer"):
            return response["answer"]
        
        # 如果没有综合性回答，则格式化原始结果
        formatted_results = []
        for result in response.get("results", []):
            title = result.get("title", "无标题")
            snippet = result.get("snippet", "无内容")
            formatted_results.append(f"标题: {title}\n内容: {snippet}\n")
        
        if not formatted_results:
             return "抱歉，没有找到相关的旅游景点推荐。"
        
        return "根据搜索结果，以下是一些推荐的旅游景点：\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"错误：执行Tavily搜索时出现问题 - {e}"
    

available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}


class OpenAICompatibleClient:
    """
    一个用于调用任何兼容OpenAI接口的LLM服务的客户端
    """

    def __init__(self,model: str,api_key: str,base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key,base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """调用LLM API来生成回应。"""
        print("正在调用大语言模型...")
        try:
            messages = [
                {'role':'system','content':system_prompt},
                {'role':'user','content':prompt}
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                #temperature=0.7,
                #max_tokens=1024,
                #top_p=1,
                #frequency_penalty=0,
                #presence_penalty=0,
                #stop=None
                stream=False
            )

            answer = response.choices[0].message.content
            print("大语言模型响应成功。")
            return answer
        except Exception as e:
            print(f"调用LLM API时发生错误: {e}")
            return "错误：调用语言模型服务时出错。"




def getLLM(city: str):
    #1、配置LLM客户端
    LLM_API_KEY =  os.environ.get("guijiliudong_API_KEY")   
    BASE_URL  = "https://api.siliconflow.cn"
    MODEL_ID  = "deepseek-ai/DeepSeek-V3.2"

    llm = OpenAICompatibleClient(
        model=MODEL_ID,
        api_key=LLM_API_KEY,
        base_url=BASE_URL
    )

    #2、初始化
    user_prompt = "你好,请帮我查询一下今天" + city +"的天气,然后根据天气推荐一个合适的旅游景点。"
    prompt_history = [f"用户请求: {user_prompt}"]

    print(f"用户输入: {user_prompt}\n" + "="*40)

    #3、运行主循环
    for i in range(5): #设置最大循环次数
        print(f"--- 循环 {i+1} ---\n")

        #3.1 构建prompt
        full_prompt = "\n".join(prompt_history)

        #3.2 调用LLM进行思考
        llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)
        print(f"模型输出:\n{llm_output}\n")
        prompt_history.append(f"模型输出:\n{llm_output}")

        #3.3 解析并执行行动
        action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)
        if not action_match:
            print("解析错误:模型输出中未找到Action。")
            break

        action_str = action_match.group(1).strip()

        if action_str.startswith("finish"):
            final_answer = re.search(r'finish\(answer="(.*)"\)', action_str)
            print(f"任务完成，最终答案: {final_answer}")
            break
    
        tool_name = re.search(r"(\w+)\(", action_str).group(1)
        args_str = re.search(r"\((.*)\)", action_str).group(1)
        kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))

        # 调用相应的工具
        if tool_name in available_tools:
            observation = available_tools[tool_name](**kwargs)
        else:
            observation = f"错误：未知工具 '{tool_name}'。" 

        
        # 3.4 记录观察结果
        observation_str = f"Observation: {observation}"
        print(f"{observation_str}\n"+"="*40)
        prompt_history.append(observation_str)




if __name__ == "__main__":
    getLLM("惠州")
    #res = get_weather("北京")
    #print(res)
    