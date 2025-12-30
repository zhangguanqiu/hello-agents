#!/bin/bash

# AutoGen 动态智能体团队 API - cURL 测试脚本

# API 基础 URL
BASE_URL="http://127.0.0.1:8000"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印分隔线
print_separator() {
    echo ""
    echo "============================================================"
    echo "$1"
    echo "============================================================"
    echo ""
}

# 测试1: 健康检查
test_health_check() {
    print_separator "🏥 测试1: 健康检查"
    
    echo -e "${BLUE}📤 发送请求到: ${BASE_URL}/api/v1/health${NC}"
    echo ""
    
    response=$(curl -s -w "\n%{http_code}" "${BASE_URL}/api/v1/health")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    echo -e "${BLUE}📥 响应状态码:${NC} $http_code"
    echo -e "${BLUE}📋 响应内容:${NC}"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    
    if [ "$http_code" = "200" ]; then
        echo -e "\n${GREEN}✅ 健康检查通过${NC}"
        return 0
    else
        echo -e "\n${RED}❌ 健康检查失败${NC}"
        return 1
    fi
}

# 测试2: CVM 成本优化场景
test_cvm_optimization() {
    print_separator "💰 测试2: CVM 成本优化场景"
    
    echo -e "${BLUE}📤 发送请求到: ${BASE_URL}/api/v1/team/execute${NC}"
    echo -e "${YELLOW}⏳ 请稍候，这可能需要几分钟...${NC}"
    echo ""
    
    # 构建 JSON 请求体
    curl -X POST "${BASE_URL}/api/v1/team/execute" \
        -H "Content-Type: application/json" \
        -w "\n\n📊 HTTP 状态码: %{http_code}\n⏱️  总耗时: %{time_total}s\n" \
        -d '{
  "initial_task": "# CVM服务器成本优化分析任务\n当前机型规格和价格：32核128G的IT5.8XLARGE128价格4694.4\n目前CPU使用率:2.2%\n目前CPU核数:32\n目前MEM使用率: 44.27%\n目前内存大小（GB）:128\n变更的目标机型规格和价格列表：\n16核64G的IT5.4XLARGE64价格2347.2\n32核128G的IT5.8XLARGE128价格4694.4\n64核256G的IT5.16XLARGE256价格9388.8\n84核320G的IT5.21XLARGE320价格11541.6",
  "modelManager": [
    {
      "model_name": "ProductManager",
      "system_message": "你是一名云服务器成本管理专家。根据用户提供的目前云服务器规格、目前真实的CPU和内存的使用情况，然后根据用户提供的机型列表，综合下面规格为用户找出推荐的机型，请用最少token去思考。\n\n判断规则如下:\n1：如果CPU的使用率在40%到70%之间,内存的使用率在40%到90%之间，则认为服务器规格是合适的，规格保持不变，其它情况则需考虑扩容或者缩容CPU或者内存。\n2：CPU需求核数 = ceil(当前核数 × CPU使用率) 然后向上取整。\n3：内存需求容量 = ceil(当前内存 × 内存使用率)然后向上取整。\n4：推荐机型的CPU规格必须大于CPU需求核数。\n5：推荐机型的内存规格必须大于内存需求容量。\n\n如果收到审核反馈，请根据反馈调整推荐策略。\n请根据这5个规则，在用户提供的变更的目标机型规格和价格列表中选择合适的规格，并判定变更是否合理,并计算新旧机型的差价增加或者减少的百分比。",
      "id": 1,
      "result": {
        "recommendation": "推荐原因和价格变化",
        "recommended_instance": "推荐机型",
        "recommended_operation": "建议扩容/缩容/保持原规格",
        "cost_result": true
      }
    },
    {
      "model_name": "Engineer",
      "system_message": "你是一位资深的云服务器性能优化专家，擅长评估云服务器配置的稳定性。\n\n你的技术专长包括：\n1. 稳定性预测：基于配置变更预测系统运行稳定性\n\n稳定性评估流程：\n1. 分析新配置的性能容量是否满足业务需求\n\n稳定性评估标准：\n- 新配置应至少保留30%的资源余量应对突发负载",
      "id": 2,
      "result": {
        "stability_result": true,
        "stability_reason": "稳定性评估原因"
      }
    },
    {
      "model_name": "CodeReviewer",
      "system_message": "你是一位资深的云服务器安全专家，专注于云服务器配置的安全性评估。\n\n你的安全评估重点包括：\n1. 合规性：确保配置符合安全最佳实践\n\n安全评估流程：\n1. 接收成本智能体推荐的新规格配置识别潜在的安全风险点\n\n安全评估标准：\n- 确保配置变更不会引入新的安全风险",
      "id": 3,
      "result": {
        "security_result": true,
        "security_reason": "安全评估原因"
      }
    },
    {
      "model_name": "FinalDecisionAgent",
      "system_message": "你是最终决策智能体，负责汇总评估结果并做出最终决定。\n\n你的职责：\n1. 接收成本智能体的推荐\n2. 接收稳定性智能体的评估结果（stability_result字段）\n3. 接收安全智能体的评估结果（security_result字段）\n4. 综合分析所有评估结果\n5. 做出最终决策并输出结果\n\n重要：如果 stability_result 和 security_result 都是 true，则 allow 返回 true，否则返回 false。",
      "id": 4,
      "result": {
        "result": "目前决策推荐的机型",
        "reason": "目前决策理由",
        "allow": true
      }
    }
  ],
  "max_iterations": 3,
  "max_turns_per_round": 10
}' | jq '.'
    
    echo ""
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ CVM 成本优化测试完成${NC}"
    else
        echo -e "${RED}❌ CVM 成本优化测试失败${NC}"
    fi
}

# 测试3: 简单审批流程
test_custom_scenario() {
    print_separator "🎯 测试3: 简单的三步审批流程"
    
    echo -e "${BLUE}📤 发送请求到: ${BASE_URL}/api/v1/team/execute${NC}"
    echo -e "${YELLOW}⏳ 请稍候...${NC}"
    echo ""
    
    curl -X POST "${BASE_URL}/api/v1/team/execute" \
        -H "Content-Type: application/json" \
        -w "\n\n📊 HTTP 状态码: %{http_code}\n⏱️  总耗时: %{time_total}s\n" \
        -d '{
  "initial_task": "请评估以下项目申请：\n项目名称：新产品开发\n预算：100万元\n周期：6个月\n团队规模：10人\n\n请按照以下流程评估：\n1. 预算审核：评估预算是否合理\n2. 技术评估：评估技术可行性\n3. 最终决策：综合评估结果做出决定",
  "modelManager": [
    {
      "model_name": "BudgetReviewer",
      "system_message": "你是预算审核专家。请评估项目预算是否合理。\n评估标准：\n- 预算应在50-200万之间\n- 人均预算应合理（5-15万/人）\n如果预算合理，budget_approved 返回 true，否则返回 false。",
      "id": 1,
      "result": {
        "budget_approved": true,
        "budget_comment": "预算评估意见"
      }
    },
    {
      "model_name": "TechReviewer",
      "system_message": "你是技术评估专家。请评估项目技术可行性。\n评估标准：\n- 团队规模应合理（5-20人）\n- 项目周期应合理（3-12个月）\n如果技术可行，tech_approved 返回 true，否则返回 false。",
      "id": 2,
      "result": {
        "tech_approved": true,
        "tech_comment": "技术评估意见"
      }
    },
    {
      "model_name": "FinalDecision",
      "system_message": "你是最终决策者。综合预算和技术评估结果做出决定。\n如果 budget_approved 和 tech_approved 都是 true，则 final_approved 返回 true。",
      "id": 3,
      "result": {
        "final_approved": true,
        "final_comment": "最终决策意见"
      }
    }
  ],
  "max_iterations": 2,
  "max_turns_per_round": 6
}' | jq '.'
    
    echo ""
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 审批流程测试完成${NC}"
    else
        echo -e "${RED}❌ 审批流程测试失败${NC}"
    fi
}

# 主函数
main() {
    print_separator "🧪 AutoGen 动态智能体团队 API - cURL 测试"
    
    # 检查 jq 是否安装
    if ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}⚠️  警告: 未安装 jq，JSON 输出可能不美观${NC}"
        echo -e "${YELLOW}   安装方法: brew install jq (macOS) 或 apt-get install jq (Linux)${NC}"
        echo ""
    fi
    
    # 检查 curl 是否安装
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}❌ 错误: 未安装 curl${NC}"
        exit 1
    fi
    
    # 测试健康检查
    if ! test_health_check; then
        echo -e "\n${RED}❌ 健康检查失败，请确保服务已启动${NC}"
        echo -e "${YELLOW}启动命令: python assest_new.py${NC}"
        exit 1
    fi
    
    echo -e "\n${GREEN}✅ 健康检查通过，服务运行正常${NC}"
    
    # 询问用户要运行哪个测试
    echo ""
    echo "请选择要运行的测试："
    echo "  1) CVM 成本优化场景"
    echo "  2) 简单审批流程"
    echo "  3) 运行所有测试"
    echo "  q) 退出"
    echo ""
    read -p "请输入选项 (1/2/3/q): " choice
    
    case $choice in
        1)
            test_cvm_optimization
            ;;
        2)
            test_custom_scenario
            ;;
        3)
            test_cvm_optimization
            test_custom_scenario
            ;;
        q|Q)
            echo -e "\n${BLUE}👋 退出测试${NC}"
            exit 0
            ;;
        *)
            echo -e "\n${RED}❌ 无效选项${NC}"
            exit 1
            ;;
    esac
    
    print_separator "🎉 测试完成"
}

# 运行主函数
main
