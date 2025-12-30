"""
测试 assest_new.py 的示例脚本
演示如何通过 HTTP 请求调用动态智能体团队 API
"""

import requests
import json

# API 基础 URL
BASE_URL = "http://127.0.0.1:8080"

def test_health_check():
    """测试健康检查端点"""
    print("\n" + "=" * 60)
    print("🏥 测试健康检查")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.status_code == 200


def test_cvm_optimization():
    """测试 CVM 成本优化场景（与原始 assest.py 相同的场景）"""
    print("\n" + "=" * 60)
    print("💰 测试 CVM 成本优化场景")
    print("=" * 60)
    
    # 构建请求数据
    request_data = {
        "initial_task": """# CVM服务器成本优化分析任务
当前机型规格和价格：32核128G的IT5.8XLARGE128价格4694.4
目前CPU使用率:2.2%
目前CPU核数:32
目前MEM使用率: 44.27%
目前内存大小（GB）:128
变更的目标机型规格和价格列表：
16核64G的IT5.4XLARGE64价格2347.2
32核128G的IT5.8XLARGE128价格4694.4
64核256G的IT5.16XLARGE256价格9388.8
84核320G的IT5.21XLARGE320价格11541.6""",
        "modelManager": [
            {
                "model_name": "ProductManager",
                "system_message": """你是一名云服务器成本管理专家。根据用户提供的目前云服务器规格、目前真实的CPU和内存的使用情况，然后根据用户提供的机型列表，综合下面规格为用户找出推荐的机型，请用最少token去思考。

判断规则如下:
1：如果CPU的使用率在40%到70%之间,内存的使用率在40%到90%之间，则认为服务器规格是合适的，规格保持不变，其它情况则需考虑扩容或者缩容CPU或者内存。
2：CPU需求核数 = ceil(当前核数 × CPU使用率) 然后向上取整。
3：内存需求容量 = ceil(当前内存 × 内存使用率)然后向上取整。
4：推荐机型的CPU规格必须大于CPU需求核数。
5：推荐机型的内存规格必须大于内存需求容量。

如果收到审核反馈，请根据反馈调整推荐策略。
请根据这5个规则，在用户提供的变更的目标机型规格和价格列表中选择合适的规格，并判定变更是否合理,并计算新旧机型的差价增加或者减少的百分比。""",
                "id": 1,
                "result": {
                    "recommendation": "推荐原因和价格变化",
                    "recommended_instance": "推荐机型",
                    "recommended_operation": "建议扩容/缩容/保持原规格",
                    "cost_optimization_result": True
                }
            },
            {
                "model_name": "Engineer",
                "system_message": """你是一位资深的云服务器性能优化专家，擅长评估云服务器配置的稳定性。

你的技术专长包括：
1. 稳定性预测：基于配置变更预测系统运行稳定性

稳定性评估流程：
1. 分析新配置的性能容量是否满足业务需求

稳定性评估标准：
- 新配置应至少保留30%的资源余量应对突发负载""",
                "id": 2,
                "result": {
                    "stability_result": True,
                    "stability_reason": "稳定性评估原因"
                }
            },
            {
                "model_name": "CodeReviewer",
                "system_message": """你是一位资深的云服务器安全专家，专注于云服务器配置的安全性评估。

你的安全评估重点包括：
1. 合规性：确保配置符合安全最佳实践

安全评估流程：
1. 接收成本智能体推荐的新规格配置识别潜在的安全风险点

安全评估标准：
- 确保配置变更不会引入新的安全风险""",
                "id": 3,
                "result": {
                    "security_result": True,
                    "security_reason": "安全评估原因"
                }
            },
            {
                "model_name": "FinalDecisionAgent",
                "system_message": """你是最终决策智能体，负责汇总评估结果并做出最终决定。

你的职责：
1. 接收成本智能体的推荐
2. 接收稳定性智能体的评估结果（stability_result字段）
3. 接收安全智能体的评估结果（security_result字段）
4. 综合分析所有评估结果
5. 做出最终决策并输出结果

重要：如果 stability_result 和 security_result 都是 true，则 allow 返回 true，否则返回 false。""",
                "id": 4,
                "result": {
                    "result": "目前决策推荐的机型",
                    "reason": "目前决策理由",
                    "allow": True
                }
            }
        ],
        "max_iterations": 3,
        "max_turns_per_round": 10
    }
    
    # 发送请求
    print("\n📤 发送请求...")
    print(f"任务: {request_data['initial_task'][:100]}...")
    print(f"智能体数量: {len(request_data['modelManager'])}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/team/execute",
            json=request_data,
            timeout=300  # 5分钟超时
        )
        
        print(f"\n📥 收到响应")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n" + "=" * 60)
            print("📊 执行结果")
            print("=" * 60)
            print(f"✅ 成功: {result['success']}")
            print(f"✅ 全部通过: {result['all_passed']}")
            print(f"🔄 总轮次: {result['total_rounds']}")
            print(f"🕐 完成时间: {result['timestamp']}")
            
            print("\n" + "=" * 60)
            print("📋 各智能体最终输出")
            print("=" * 60)
            for agent_name, output in result['final_results'].items():
                print(f"\n🤖 {agent_name}:")
                print(json.dumps(output, indent=2, ensure_ascii=False))
            
            if result['failure_reasons']:
                print("\n" + "=" * 60)
                print("⚠️  失败原因")
                print("=" * 60)
                for i, reason in enumerate(result['failure_reasons'], 1):
                    print(f"{i}. {reason}")
            
            return True
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 请求出错: {e}")
        return False


def test_custom_scenario():
    """测试自定义场景"""
    print("\n" + "=" * 60)
    print("🎯 测试自定义场景 - 简单的三步审批流程")
    print("=" * 60)
    
    request_data = {
        "initial_task": """请评估以下项目申请：
项目名称：新产品开发
预算：100万元
周期：6个月
团队规模：10人

请按照以下流程评估：
1. 预算审核：评估预算是否合理
2. 技术评估：评估技术可行性
3. 最终决策：综合评估结果做出决定""",
        "modelManager": [
            {
                "model_name": "BudgetReviewer",
                "system_message": """你是预算审核专家。请评估项目预算是否合理。
评估标准：
- 预算应在50-200万之间
- 人均预算应合理（5-15万/人）
如果预算合理，budget_approved 返回 true，否则返回 false。""",
                "id": 1,
                "result": {
                    "budget_approved": True,
                    "budget_comment": "预算评估意见"
                }
            },
            {
                "model_name": "TechReviewer",
                "system_message": """你是技术评估专家。请评估项目技术可行性。
评估标准：
- 团队规模应合理（5-20人）
- 项目周期应合理（3-12个月）
如果技术可行，tech_approved 返回 true，否则返回 false。""",
                "id": 2,
                "result": {
                    "tech_approved": True,
                    "tech_comment": "技术评估意见"
                }
            },
            {
                "model_name": "FinalDecision",
                "system_message": """你是最终决策者。综合预算和技术评估结果做出决定。
如果 budget_approved 和 tech_approved 都是 true，则 final_approved 返回 true。""",
                "id": 3,
                "result": {
                    "final_approved": True,
                    "final_comment": "最终决策意见"
                }
            }
        ],
        "max_iterations": 2,
        "max_turns_per_round": 6
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/team/execute",
            json=request_data,
            timeout=180
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 执行成功")
            print(f"全部通过: {result['all_passed']}")
            print(f"总轮次: {result['total_rounds']}")
            print(f"\n最终结果:")
            print(json.dumps(result['final_results'], indent=2, ensure_ascii=False))
            return True
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求出错: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🧪 AutoGen 动态智能体团队 API 测试")
    print("=" * 60)
    
    # 测试健康检查
    if not test_health_check():
        print("\n❌ 健康检查失败，请确保服务已启动")
        print("启动命令: python assest_new.py")
        return
    
    print("\n✅ 健康检查通过，服务运行正常")
    
    # 测试 CVM 优化场景
    print("\n" + "=" * 60)
    print("开始测试场景")
    print("=" * 60)
    
    # 场景1：CVM 成本优化（与原始代码相同）
    test_cvm_optimization()
    
    # 场景2：自定义审批流程
    # test_custom_scenario()


if __name__ == "__main__":
    main()
