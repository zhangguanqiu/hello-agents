from autogen_ext.models.openai import OpenAIChatCompletionClient
import os          
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console
import asyncio
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from typing import Dict, Any, List, Optional
import json
import re
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, validator
import uvicorn
from datetime import datetime

# 加载 .env 文件中的环境变量
load_dotenv()

# ==================== FastAPI 应用初始化 ====================
app = FastAPI(
    title="AutoGen 动态智能体团队 API",
    description="动态创建智能体团队并执行任务的 HTTP 接口",
    version="1.0.0"
)

# ==================== 数据模型定义 ====================
class AgentResultSchema(BaseModel):
    """智能体输出结果的 schema 定义"""
    class Config:
        extra = "allow"  # 允许额外字段
    
    def dict(self, *args, **kwargs):
        """重写 dict 方法以支持动态字段"""
        return super().dict(*args, **kwargs)


class AgentConfig(BaseModel):
    """单个智能体配置"""
    model_name: str = Field(..., description="智能体名称")
    system_message: str = Field(..., description="智能体系统提示词")
    id: int = Field(..., description="智能体执行顺序ID，从1开始")
    result: Dict[str, Any] = Field(..., description="期望的输出结果schema，必须包含判断字段")
    
    @validator('id')
    def validate_id(cls, v):
        if v < 1:
            raise ValueError('id 必须大于等于 1')
        return v
    
    @validator('result')
    def validate_result(cls, v):
        # 检查是否至少有一个布尔类型的判断字段
        has_bool_field = any(
            isinstance(value, bool) or 
            (isinstance(value, str) and value.lower() in ['true', 'false'])
            for value in v.values()
        )
        if not has_bool_field:
            raise ValueError('result 必须包含至少一个布尔类型的判断字段')
        return v


class TeamTaskRequest(BaseModel):
    """团队任务请求"""
    initial_task: str = Field(..., description="初始任务描述")
    modelManager: List[AgentConfig] = Field(..., description="智能体配置列表")
    max_iterations: int = Field(default=3, ge=1, le=10, description="最大迭代次数")
    max_turns_per_round: int = Field(default=10, ge=1, le=50, description="每轮最大对话轮次")
    
    @validator('modelManager')
    def validate_model_manager(cls, v):
        if not v:
            raise ValueError('modelManager 不能为空')
        
        # 检查 ID 是否连续且从1开始
        ids = sorted([agent.id for agent in v])
        if ids[0] != 1:
            raise ValueError('智能体 ID 必须从 1 开始')
        
        for i in range(len(ids) - 1):
            if ids[i + 1] - ids[i] != 1:
                raise ValueError(f'智能体 ID 必须连续，发现断层: {ids[i]} -> {ids[i+1]}')
        
        # 检查是否有重复的 ID
        if len(ids) != len(set(ids)):
            raise ValueError('智能体 ID 不能重复')
        
        return v


class TeamTaskResponse(BaseModel):
    """团队任务响应"""
    success: bool = Field(..., description="任务是否成功完成")
    all_passed: bool = Field(..., description="所有判断字段是否都通过")
    total_rounds: int = Field(..., description="总执行轮次")
    final_results: Dict[str, Any] = Field(..., description="各智能体的最终输出结果")
    execution_log: List[Dict[str, Any]] = Field(..., description="执行日志")
    failure_reasons: List[str] = Field(default_factory=list, description="失败原因列表")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="完成时间")


# ==================== OpenAI 模型客户端 ====================
def create_openai_model_client():
    """创建 OpenAI 模型客户端"""
    model = os.getenv("LLM_MODEL_ID")
    apiKey = os.getenv("LLM_API_KEY")
    baseUrl = os.getenv("LLM_BASE_URL")
    timeout = int(os.getenv("LLM_TIMEOUT", 60))
    
    if not all([model, apiKey, baseUrl]):
        raise ValueError("缺少必要的环境变量: LLM_MODEL_ID, LLM_API_KEY, LLM_BASE_URL")
    
    model_info = {
        "function_calling": True,
        "max_tokens": 20480,
        "json_output": True,
        "vision": False,
        "family": "deepseek",
        "structured_output": False,
        "temperature": 0,
    }
    
    return OpenAIChatCompletionClient(
        model=model,
        api_key=apiKey,
        base_url=baseUrl,
        model_info=model_info,
        timeout=timeout
    )


# ==================== 动态智能体创建 ====================
def create_dynamic_agent(model_client, agent_config: AgentConfig, is_final: bool = False):
    """动态创建智能体"""
    
    # 构建结果schema的JSON示例
    result_schema_example = json.dumps(agent_config.result, ensure_ascii=False, indent=2)
    
    # 提取判断字段（布尔类型的字段）
    judge_fields = [
        key for key, value in agent_config.result.items()
        if isinstance(value, bool) or (isinstance(value, str) and value.lower() in ['true', 'false'])
    ]
    
    # 构建系统消息
    enhanced_system_message = f"""{agent_config.system_message}

## 输出要求
你必须严格按照以下 JSON 格式输出结果：

{result_schema_example}

## 重要说明
1. 输出必须是有效的 JSON 格式
2. 所有字段都必须填写
3. 判断字段 ({', '.join(judge_fields)}) 必须是布尔值 (true/false)
4. 请基于你的专业分析给出准确的判断结果
"""
    
    # 如果是最终决策智能体，添加终止标记要求
    if is_final:
        enhanced_system_message += "\n5. 输出JSON后，必须在最后一行输出 FINAL_DECISION 标记表示决策完成。"
    
    return AssistantAgent(
        name=agent_config.model_name,
        model_client=model_client,
        system_message=enhanced_system_message,
        model_client_stream=True,
    )


# ==================== JSON 提取工具 ====================
def extract_json_from_message(content: str) -> Optional[Dict[str, Any]]:
    """从消息内容中提取 JSON 对象"""
    if not content:
        return None
    
    # 方法1: 匹配标准JSON对象
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, content, re.DOTALL)
    
    for json_str in matches:
        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue
    
    # 方法2: 尝试提取代码块中的JSON
    code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    code_matches = re.findall(code_block_pattern, content, re.DOTALL)
    
    for json_str in code_matches:
        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue
    
    return None


def parse_boolean_value(value: Any) -> bool:
    """解析布尔值（支持字符串和布尔类型）"""
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        return value.lower() == 'true'
    else:
        return bool(value)


# ==================== 动态团队类 ====================
class DynamicAgentTeam:
    """动态智能体团队"""
    
    def __init__(self, model_client, agent_configs: List[AgentConfig]):
        self.model_client = model_client
        self.agent_configs = sorted(agent_configs, key=lambda x: x.id)  # 按ID排序
        self.agents = []
        
        # 创建所有智能体
        for i, config in enumerate(self.agent_configs):
            is_final = (i == len(self.agent_configs) - 1)  # 最后一个是最终决策智能体
            agent = create_dynamic_agent(model_client, config, is_final)
            self.agents.append(agent)
    
    def get_judge_fields(self, agent_config: AgentConfig) -> List[str]:
        """获取智能体的判断字段"""
        return [
            key for key, value in agent_config.result.items()
            if isinstance(value, bool) or (isinstance(value, str) and value.lower() in ['true', 'false'])
        ]
    
    async def run_team_evaluation(
        self, 
        task: str, 
        max_iterations: int = 3,
        max_turns_per_round: int = 10
    ) -> Dict[str, Any]:
        """运行团队评估流程"""
        
        print(f"\n💼 评估策略：最多进行 {max_iterations} 轮迭代评估")
        print(f"   智能体数量: {len(self.agents)}")
        print(f"   执行顺序: {' → '.join([agent.name for agent in self.agents])}")
        print(f"   每轮最大对话轮次: {max_turns_per_round}\n")
        
        iteration = 1
        all_passed = False
        final_results = {}
        failure_reasons = []
        execution_log = []
        
        while iteration <= max_iterations and not all_passed:
            print(f"\n{'='*60}")
            print(f"🔄 第 {iteration} 轮评估")
            print(f"{'='*60}")
            
            round_log = {
                "round": iteration,
                "timestamp": datetime.now().isoformat(),
                "agents_output": {},
                "passed": False
            }
            
            # 构建本轮任务
            if iteration == 1:
                current_task = task + "\n\n## 评估流程\n请严格按照智能体顺序执行评估。"
            else:
                feedback_section = ""
                if failure_reasons:
                    feedback_section = "\n## 上一轮评估反馈\n" + "\n".join(failure_reasons[-len(self.agents):]) + "\n"
                
                current_task = task + f"""

## 第 {iteration} 轮评估（重新评估）
由于上一轮评估未完全通过，请重新进行评估。{feedback_section}

请第一个智能体根据反馈重新分析，其他智能体依次评估。"""
            
            # 创建团队聊天
            termination = TextMentionTermination("FINAL_DECISION")
            team_chat = RoundRobinGroupChat(
                participants=self.agents,
                termination_condition=termination,
                max_turns=max_turns_per_round,
            )
            
            # 运行团队协作
            print(f"\n🎬 启动智能体对话...")
            try:
                result = await Console(team_chat.run_stream(task=current_task))
            except Exception as e:
                print(f"❌ 团队对话执行出错: {e}")
                round_log["error"] = str(e)
                execution_log.append(round_log)
                break
            
            # 提取各智能体的输出
            agents_outputs = {config.model_name: [] for config in self.agent_configs}
            
            if hasattr(result, 'messages'):
                for msg in result.messages:
                    if hasattr(msg, 'source') and hasattr(msg, 'content'):
                        source = msg.source
                        content = msg.content
                        
                        json_data = extract_json_from_message(content)
                        if json_data and source in agents_outputs:
                            agents_outputs[source].append(json_data)
            
            # 解析各智能体的输出（取最后一个有效的）
            current_round_results = {}
            all_judges_passed = True
            current_failures = []
            
            for config in self.agent_configs:
                agent_name = config.model_name
                judge_fields = self.get_judge_fields(config)
                
                # 获取该智能体的最后一个有效输出
                agent_output = None
                for output in reversed(agents_outputs[agent_name]):
                    # 检查输出是否包含所有必需字段
                    if all(field in output for field in config.result.keys()):
                        agent_output = output
                        break
                
                if agent_output:
                    current_round_results[agent_name] = agent_output
                    
                    # 检查判断字段
                    agent_passed = True
                    for judge_field in judge_fields:
                        if judge_field in agent_output:
                            field_value = parse_boolean_value(agent_output[judge_field])
                            if not field_value:
                                agent_passed = False
                                # 查找原因字段（通常是 xxx_reason）
                                reason_field = f"{judge_field.replace('_result', '_reason')}"
                                reason = agent_output.get(reason_field, "未提供具体原因")
                                current_failures.append(
                                    f"{agent_name} - {judge_field} 未通过: {reason}"
                                )
                    
                    if not agent_passed:
                        all_judges_passed = False
                    
                    # 打印智能体输出摘要
                    status = "✅ 通过" if agent_passed else "❌ 不通过"
                    print(f"\n🤖 {agent_name}: {status}")
                    
                    # 打印关键信息（非判断字段）
                    for key, value in agent_output.items():
                        if key not in judge_fields:
                            value_str = str(value)
                            if len(value_str) > 100:
                                value_str = value_str[:100] + "..."
                            print(f"   {key}: {value_str}")
                else:
                    # 智能体没有输出有效结果
                    all_judges_passed = False
                    current_failures.append(f"{agent_name} 未输出有效的结果")
                    print(f"\n🤖 {agent_name}: ⚠️  未输出有效结果")
            
            # 记录本轮结果
            round_log["agents_output"] = current_round_results
            round_log["passed"] = all_judges_passed
            round_log["failures"] = current_failures
            execution_log.append(round_log)
            
            # 更新失败原因
            if current_failures:
                failure_reasons.extend(current_failures)
            
            # 更新最终结果
            final_results = current_round_results
            
            # 检查是否全部通过
            if all_judges_passed:
                all_passed = True
                print(f"\n{'='*60}")
                print(f"🎉 第 {iteration} 轮评估全部通过！")
                print(f"{'='*60}")
                break
            else:
                iteration += 1
                if iteration <= max_iterations:
                    print(f"\n{'='*60}")
                    print(f"⚠️  第 {iteration-1} 轮评估未通过，准备第 {iteration} 轮重新评估...")
                    if current_failures:
                        print(f"\n📋 需要改进的问题:")
                        for i, failure in enumerate(current_failures, 1):
                            print(f"   {i}. {failure}")
                    print(f"{'='*60}")
                else:
                    print(f"\n{'='*60}")
                    print(f"⚠️  已达到最大评估轮次（{max_iterations}轮），评估结束")
                    print(f"{'='*60}")
        
        return {
            'all_passed': all_passed,
            'final_results': final_results,
            'total_rounds': iteration if all_passed else iteration - 1,
            'failure_reasons': failure_reasons,
            'execution_log': execution_log
        }


# ==================== HTTP API 端点 ====================
@app.post("/api/v1/team/execute", response_model=TeamTaskResponse)
async def execute_team_task(request: TeamTaskRequest):
    """
    执行智能体团队任务
    
    - **initial_task**: 任务描述
    - **modelManager**: 智能体配置列表
    - **max_iterations**: 最大迭代次数（默认3次）
    - **max_turns_per_round**: 每轮最大对话轮次（默认10次）
    """
    try:
        print("\n" + "=" * 60)
        print("🚀 动态智能体团队任务执行")
        print("=" * 60)
        
        # 创建模型客户端
        print("\n📌 正在初始化...")
        model_client = create_openai_model_client()
        print("✓ 模型客户端初始化完成")
        
        # 创建动态团队
        team = DynamicAgentTeam(model_client, request.modelManager)
        print("✓ 智能体团队创建完成")
        for agent_config in request.modelManager:
            print(f"   - {agent_config.model_name} (ID: {agent_config.id})")
        
        # 执行任务
        print("\n" + "=" * 60)
        print("🔄 开始智能体协作评估")
        print("=" * 60)
        
        result = await team.run_team_evaluation(
            task=request.initial_task,
            max_iterations=request.max_iterations,
            max_turns_per_round=request.max_turns_per_round
        )
        
        print("\n" + "=" * 60)
        print("🎯 智能体协作完成！")
        print("=" * 60)
        
        # 构建响应
        response = TeamTaskResponse(
            success=True,
            all_passed=result['all_passed'],
            total_rounds=result['total_rounds'],
            final_results=result['final_results'],
            execution_log=result['execution_log'],
            failure_reasons=result['failure_reasons']
        )
        
        # 打印最终报告
        print(f"\n{'='*60}")
        print("📋 最终评估报告")
        print(f"{'='*60}")
        print(f"\n✅ 评估结果：{'所有评估通过' if response.all_passed else '未完全通过'}")
        print(f"📊 总评估轮次: {response.total_rounds}")
        print(f"🕐 完成时间: {response.timestamp}")
        
        return response
        
    except ValueError as e:
        print(f"❌ 配置错误：{e}")
        raise HTTPException(status_code=400, detail=f"配置错误: {str(e)}")
    except Exception as e:
        print(f"❌ 运行错误：{e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@app.get("/api/v1/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AutoGen Dynamic Agent Team API"
    }


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AutoGen 动态智能体团队 API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# ==================== 主函数 ====================
def main():
    """启动 FastAPI 服务器"""
    print("\n" + "=" * 60)
    print("🚀 启动 AutoGen 动态智能体团队 API 服务")
    print("=" * 60)
    print("\n📌 服务信息:")
    print("   - 地址: http://0.0.0.0:8000")
    print("   - API 文档: http://0.0.0.0:8000/docs")
    print("   - 健康检查: http://0.0.0.0:8000/api/v1/health")
    print("\n" + "=" * 60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
