from autogen_ext.models.openai import OpenAIChatCompletionClient
import os      
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console
import asyncio
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from typing import Dict, Any, Optional
import json

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
        "json_output": True,
        "function_calling": False,
        "vision": False,
        "family": "deepseek",
        "structured_output": False,
        "temperature":0,
    }
    return OpenAIChatCompletionClient(model=model,api_key=apiKey,base_url=baseUrl, model_info=model_info)

##构建智能体
def create_product_manager(model_client):
    """创建cvm成本评估智能体"""
    system_message = """#你是一名云服务器成本管理专家。根据用户提供的目前云服务器规格、目前真实的CPU和内存的使用情况，然后根据用户提供的机型列表，综合下面规格为用户找出推荐的机型,，请用最少token去思考。
#判断规则如下:
1：如果CPU的使用率在40%到70%之间,内存的使用率在40%到90%之间，则认为服务器规格是合适的，规格保持不变，其它情况则需考虑扩容或者缩容CPU或者内存。
2：CPU需求核数 = ceil(当前核数 × CPU使用率) 然后向上取整。
3：内存需求容量 = ceil(当前内存 × 内存使用率)然后向上取整。
4：推荐机型的CPU规格必须大于CPU需求核数。
5：推荐机型的内存规格必须大于内存需求容量。
#如果收到审核反馈，请根据反馈调整推荐策略
#请根据这5个规则，在用户提供的变更的目标机型规格和价格列表中选择合适的规格，并判定变更是否合理,并计算新旧机型的差价增加或者减少的百分比。
#请严格按照json格式输出以下信息：
{
    "recommendation": "这里填写推荐原因和价格变化",
    "recommended_instance": "这里填写推荐机型",
    "recommended_operation": "这里填写建议扩容/缩容/保持原规格"
}
"""
    return AssistantAgent(
        name="ProductManager", 
        model_client=model_client, 
        system_message=system_message,
        model_client_stream=True,
    )


def create_engineer(model_client):
    """创建cvm稳定性智能体"""
    system_message = """你是一位资深的云服务器性能优化专家，擅长评估云服务器配置的稳定性。

你的技术专长包括：
1. **稳定性预测**：基于配置变更预测系统运行稳定性


稳定性评估流程：
1. 分析新配置的性能容量是否满足业务需求

稳定性评估标准：
- 新配置应至少保留20%的资源余量应对突发负载

#请严格按照json格式输出以下信息：
{
    "stability_result": true/false,
    "stability_reason": "这里填写稳定性评估原因"
}"""
    
    return AssistantAgent(
        name="Engineer",
        model_client=model_client,
        system_message=system_message,
        model_client_stream=True,
    )

def create_code_reviewer(model_client):
    """创建cvm安全审核智能体"""
    system_message = """你是一位资深的云服务器安全专家，专注于云服务器配置的安全性评估。

你的安全评估重点包括：
1. **合规性**：确保配置符合安全最佳实践

安全评估流程：
1. 接收成本智能体推荐的新规格配置识别潜在的安全风险点

安全评估标准：
- 确保配置变更不会引入新的安全风险

#请严格按照json格式输出以下信息：
{
    "security_result": true/false,
    "security_reason": "这里填写安全评估原因"
}"""
    
    return AssistantAgent(
        name="CodeReviewer",
        model_client=model_client,
        system_message=system_message,
        model_client_stream=True,
    )


def create_final_decision_agent(model_client):
    """创建最终决策智能体"""
    system_message = """你是最终决策智能体，负责汇总评估结果并做出最终决定。

你的职责：
1. 接收成本智能体的推荐
2. 接收稳定性智能体的评估结果（stability_result字段）
3. 接收安全智能体的评估结果（security_result字段）
4. 综合分析所有评估结果
5. 做出最终决策并输出结果

输出格式（必须严格遵守）：
{
   "result": "目前决策推荐的机型",
   "reason": "目前决策理由",
   "allow": true或false（布尔值，如果stability_result和security_result都是true，则返回true，否则返回false）
}

重要：输出JSON后，必须在最后一行输出 FINAL_DECISION 标记表示决策完成。
"""
    
    return AssistantAgent(
        name="FinalDecisionAgent",
        model_client=model_client,
        system_message=system_message,
        model_client_stream=True,
    )


class CostOptimizationTeam:
    def __init__(self, model_client):
        self.model_client = model_client
        self.product_manager = create_product_manager(model_client)
        self.engineer = create_engineer(model_client)
        self.code_reviewer = create_code_reviewer(model_client)
        self.final_decision_agent = create_final_decision_agent(model_client)
        
    async def run_auto_gen_team_chat(self, task: str, max_iterations: int = 3):
        """使用AutoGen的团队聊天功能运行优化流程"""
        print(f"\n开始AutoGen团队协作，最多进行{max_iterations}轮评估...")
        
        iteration = 1
        all_passed = False
        final_result = None
        failure_reasons = []
        
        while iteration <= max_iterations and not all_passed:
            print(f"\n{'='*60}")
            print(f"第 {iteration} 轮团队协作")
            print(f"{'='*60}")
            
            # 构建本轮任务
            if iteration == 1:
                current_task = task + """
                
## 评估流程
1. **成本智能体**：根据当前使用情况和规则分析，推荐最合适的机型
2. **稳定性智能体**：评估推荐机型的性能容量和稳定性风险
3. **安全智能体**：评估推荐机型是否会造成安全性影响
请严格按照流程执行。"""
            else:
                # 添加反馈信息
                feedback_section = ""
                if failure_reasons:
                    feedback_section = "\n## 上一轮评估反馈\n" + "\n".join(failure_reasons[-2:]) + "\n"
                
                current_task = task + f"""
                
## 第 {iteration} 轮评估（重新评估）
由于上一轮评估未完全通过，请重新进行评估。{feedback_section}

评估流程：
1. **成本智能体**：请根据上述反馈重新选择更合适的机型
2. **稳定性智能体**：评估新推荐机型的性能容量
3. **安全智能体**：评估新推荐机型的安全性
4. **成本智能体**：根据评估结果输出最终建议"""
            
            # 创建团队聊天 - 使用自定义终止条件
            # 当最终决策智能体输出 FINAL_DECISION 时终止
            termination = TextMentionTermination("FINAL_DECISION")
            team_chat = RoundRobinGroupChat(
                participants=[self.product_manager, self.engineer, self.code_reviewer, self.final_decision_agent],
                termination_condition=termination,
                max_turns=10,  # 减少轮次，因为不需要用户代理
            )
            
            # 运行团队协作
            print(f"启动团队对话...")
            result = await Console(team_chat.run_stream(task=current_task))
            
            # 检查评估结果 - 直接从消息中提取JSON
            engineer_approved = False
            code_reviewer_approved = False
            final_decision_allow = False
            stability_reason = ""
            security_reason = ""
            
            # 从result对象中提取消息
            import re
            
            def extract_json_from_message(content):
                """从消息内容中提取JSON对象"""
                # 匹配JSON对象（支持嵌套）
                json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                matches = re.findall(json_pattern, content)
                
                for json_str in matches:
                    try:
                        data = json.loads(json_str)
                        return data
                    except json.JSONDecodeError:
                        continue
                return None
            
            # 遍历所有消息，提取各智能体的输出
            engineer_outputs = []
            reviewer_outputs = []
            decision_outputs = []
            
            if hasattr(result, 'messages'):
                for msg in result.messages:
                    if hasattr(msg, 'source') and hasattr(msg, 'content'):
                        source = msg.source
                        content = msg.content
                        
                        print(f"\n[调试] 处理消息 - 来源: {source}")
                        print(f"[调试] 内容前100字符: {content[:100] if len(content) > 100 else content}")
                        
                        # 提取JSON
                        json_data = extract_json_from_message(content)
                        
                        if json_data:
                            print(f"[调试] 提取到JSON: {json_data}")
                            
                            if source == 'Engineer':
                                engineer_outputs.append(json_data)
                            elif source == 'CodeReviewer':
                                reviewer_outputs.append(json_data)
                            elif source == 'FinalDecisionAgent':
                                decision_outputs.append(json_data)
            
            print(f"\n[调试] Engineer输出数量: {len(engineer_outputs)}")
            print(f"[调试] CodeReviewer输出数量: {len(reviewer_outputs)}")
            print(f"[调试] FinalDecisionAgent输出数量: {len(decision_outputs)}")
            
            # 解析Engineer的输出（取最后一个有效的）
            for output in reversed(engineer_outputs):
                if 'stability_result' in output:
                    # 处理可能的字符串或布尔值
                    result_value = output['stability_result']
                    if isinstance(result_value, bool):
                        engineer_approved = result_value
                    elif isinstance(result_value, str):
                        engineer_approved = result_value.lower() == 'true'
                    stability_reason = output.get('stability_reason', '')
                    print(f"[调试] Engineer评估: {engineer_approved}, 原因: {stability_reason}")
                    break
            
            # 解析CodeReviewer的输出（取最后一个有效的）
            for output in reversed(reviewer_outputs):
                if 'security_result' in output:
                    # 处理可能的字符串或布尔值
                    result_value = output['security_result']
                    if isinstance(result_value, bool):
                        code_reviewer_approved = result_value
                    elif isinstance(result_value, str):
                        code_reviewer_approved = result_value.lower() == 'true'
                    security_reason = output.get('security_reason', '')
                    print(f"[调试] CodeReviewer评估: {code_reviewer_approved}, 原因: {security_reason}")
                    break
            
            # 解析FinalDecisionAgent的输出（取最后一个有效的）
            for output in reversed(decision_outputs):
                if 'allow' in output:
                    # 处理可能的字符串或布尔值
                    allow_value = output['allow']
                    if isinstance(allow_value, bool):
                        final_decision_allow = allow_value
                    elif isinstance(allow_value, str):
                        final_decision_allow = allow_value.lower() == 'true'
                    print(f"[调试] FinalDecisionAgent决策: allow={final_decision_allow}")
                    print(f"[调试] 完整决策输出: {output}")
                    break
            
            # 提取推荐信息（从ProductManager的消息中）
            recommendation_lines = []
            if hasattr(result, 'messages'):
                for msg in result.messages:
                    if hasattr(msg, 'source') and msg.source == 'ProductManager':
                        content = msg.content
                        # 尝试从JSON中提取推荐信息
                        json_data = extract_json_from_message(content)
                        if json_data:
                            if 'recommended_instance' in json_data:
                                recommendation_lines.append(f"推荐机型: {json_data['recommended_instance']}")
                            if 'recommendation' in json_data:
                                recommendation_lines.append(f"推荐原因: {json_data['recommendation']}")
                            if 'recommended_operation' in json_data:
                                recommendation_lines.append(f"推荐操作: {json_data['recommended_operation']}")
            
            # 记录失败原因（只在本轮新增失败时记录）
            current_failures = []
            if not engineer_approved:
                current_failures.append(f"稳定性评估不通过: {stability_reason}")
            
            if not code_reviewer_approved:
                current_failures.append(f"安全评估不通过: {security_reason}")
            
            # 只添加新的失败原因
            if current_failures:
                failure_reasons.extend(current_failures)
            
            print(f"\n第 {iteration} 轮评估结果:")
            print(f"  稳定性评估: {'通过' if engineer_approved else '不通过'}")
            print(f"  安全评估: {'通过' if code_reviewer_approved else '不通过'}")
            print(f"  最终决策allow: {'通过' if final_decision_allow else '不通过'}")
            
            if recommendation_lines:
                print(f"  推荐结果:")
                for rec_line in recommendation_lines:
                    print(f"    {rec_line}")
                
                # 保存最终结果
                final_result = "\n".join(recommendation_lines)
            
            # 检查最终决策是否允许通过
            if final_decision_allow:
                all_passed = True
                print(f"\n🎉 第 {iteration} 轮评估全部通过！")
                break
            else:
                iteration += 1
                if iteration <= max_iterations:
                    print(f"\n⚠️  准备第 {iteration} 轮评估...")
                else:
                    print(f"\n⚠️  已达到最大评估轮次（{max_iterations}轮）")
                    # 即使未完全通过，也要记录最后一次尝试的结果
                    if not final_result and recommendation_lines:
                        final_result = "\n".join(recommendation_lines)
        
        # 返回最终结果
        return {
            'all_passed': all_passed,
            'final_result': final_result,
            'total_rounds': iteration - 1 if not all_passed else iteration,
            'failure_reasons': failure_reasons
        }


async def run_optimized_software_development_team():
    """运行优化后的软件开发团队协作"""
    
    print("正在初始化模型客户端...")
    model_client = create_openai_model_client()
    
    print("正在创建智能体团队...")
    team = CostOptimizationTeam(model_client)

    initial_task = """# CVM服务器成本优化分析任务
当前机型规格和价格：32核128G的IT5.8XLARGE128价格4694.4
目前CPU使用率:2.2%
目前CPU核数:32
目前MEM使用率: 75.27%
目前内存大小（GB）:128
变更的目标机型规格和价格列表：
16核64G的IT5.4XLARGE64价格2347.2
32核128G的IT5.8XLARGE128价格4694.4
64核256G的IT5.16XLARGE256价格9388.8
84核320G的IT5.21XLARGE320价格11541.6"""
    
    # 启动优化后的团队协作
    print("启动优化的AutoGen智能体协作...")
    print("=" * 60)
    print("使用真正的AutoGen团队聊天功能")
    print("=" * 60)
    
    result = await team.run_auto_gen_team_chat(initial_task, max_iterations=3)
    
    print("\n" + "=" * 60)
    print("智能体协作完成！")
    
    # 输出最终报告
    print(f"\n{'='*60}")
    print("最终评估报告")
    print(f"{'='*60}")
    
    if result['all_passed']:
        print("✅ 评估结果：所有评估通过")
        print("\n最终推荐方案:")
        print(result['final_result'])
    else:
        print("⚠️  评估结果：未完全通过")
        print("\n最终推荐方案（存在未通过的评估）:")
        print(result['final_result'])
        
        if result['failure_reasons']:
            print("\n未通过的原因:")
            for reason in result['failure_reasons']:
                print(f"  • {reason}")
        
        print("\n建议:")
        print("  1. 考虑调整业务需求或负载")
        print("  2. 咨询专业技术团队")
        print("  3. 评估其他配置方案")
    
    print(f"\n评估统计:")
    print(f"  总评估轮次: {result['total_rounds']}")
    print(f"  最终状态: {'全部通过' if result['all_passed'] else '未完全通过'}")
    
    return result


if __name__ == "__main__":
    try:
        # 运行异步协作流程
        result = asyncio.run(run_optimized_software_development_team())

        print(f"\n协作结果摘要：")
        print(f"- 任务完成状态：{'成功' if result else '需要进一步处理'}")
    except ValueError as e:
        print(f"配置错误：{e}")
        print("请检查 .env 文件中的配置是否正确")
    except Exception as e:
        print(f"运行错误：{e}")
        import traceback
        traceback.print_exc()