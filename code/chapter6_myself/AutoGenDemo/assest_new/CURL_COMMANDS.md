# cURL 命令参考手册

本文档包含所有 API 端点的 cURL 命令示例，可以直接复制使用。

## 📋 目录

1. [健康检查](#1-健康检查)
2. [根路径](#2-根路径)
3. [CVM 成本优化场景](#3-cvm-成本优化场景)
4. [简单审批流程](#4-简单审批流程)

---

## 1. 健康检查

检查服务是否正常运行。

### 命令

```bash
curl -X GET http://127.0.0.1:8080/api/v1/health
```

### 美化输出（需要安装 jq）

```bash
curl -X GET http://127.0.0.1:8080/api/v1/health | jq '.'
```

### 预期响应

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000000",
  "service": "AutoGen Dynamic Agent Team API"
}
```

---

## 2. 根路径

获取服务基本信息。

### 命令

```bash
curl -X GET http://127.0.0.1:8080/
```

### 美化输出

```bash
curl -X GET http://127.0.0.1:8080/ | jq '.'
```

### 预期响应

```json
{
  "message": "AutoGen 动态智能体团队 API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/api/v1/health"
}
```

---

## 3. CVM 成本优化场景

执行 CVM 服务器成本优化分析任务（与原始 assest.py 相同的场景）。

### 完整命令（单行）

```bash
curl -X POST http://127.0.0.1:8080/api/v1/team/execute -H "Content-Type: application/json" -d '{"initial_task":"# CVM服务器成本优化分析任务\n当前机型规格和价格：32核128G的IT5.8XLARGE128价格4694.4\n目前CPU使用率:2.2%\n目前CPU核数:32\n目前MEM使用率: 44.27%\n目前内存大小（GB）:128\n变更的目标机型规格和价格列表：\n16核64G的IT5.4XLARGE64价格2347.2\n32核128G的IT5.8XLARGE128价格4694.4\n64核256G的IT5.16XLARGE256价格9388.8\n84核320G的IT5.21XLARGE320价格11541.6","modelManager":[{"model_name":"ProductManager","system_message":"你是一名云服务器成本管理专家。根据用户提供的目前云服务器规格、目前真实的CPU和内存的使用情况，然后根据用户提供的机型列表，综合下面规格为用户找出推荐的机型，请用最少token去思考。\n\n判断规则如下:\n1：如果CPU的使用率在40%到70%之间,内存的使用率在40%到90%之间，则认为服务器规格是合适的，规格保持不变，其它情况则需考虑扩容或者缩容CPU或者内存。\n2：CPU需求核数 = ceil(当前核数 × CPU使用率) 然后向上取整。\n3：内存需求容量 = ceil(当前内存 × 内存使用率)然后向上取整。\n4：推荐机型的CPU规格必须大于CPU需求核数。\n5：推荐机型的内存规格必须大于内存需求容量。\n\n如果收到审核反馈，请根据反馈调整推荐策略。\n请根据这5个规则，在用户提供的变更的目标机型规格和价格列表中选择合适的规格，并判定变更是否合理,并计算新旧机型的差价增加或者减少的百分比。","id":1,"result":{"recommendation":"推荐原因和价格变化","recommended_instance":"推荐机型","recommended_operation":"建议扩容/缩容/保持原规格","cost_optimization_result":true}},{"model_name":"Engineer","system_message":"你是一位资深的云服务器性能优化专家，擅长评估云服务器配置的稳定性。\n\n你的技术专长包括：\n1. 稳定性预测：基于配置变更预测系统运行稳定性\n\n稳定性评估流程：\n1. 分析新配置的性能容量是否满足业务需求\n\n稳定性评估标准：\n- 新配置应至少保留30%的资源余量应对突发负载","id":2,"result":{"stability_result":true,"stability_reason":"稳定性评估原因"}},{"model_name":"CodeReviewer","system_message":"你是一位资深的云服务器安全专家，专注于云服务器配置的安全性评估。\n\n你的安全评估重点包括：\n1. 合规性：确保配置符合安全最佳实践\n\n安全评估流程：\n1. 接收成本智能体推荐的新规格配置识别潜在的安全风险点\n\n安全评估标准：\n- 确保配置变更不会引入新的安全风险","id":3,"result":{"security_result":true,"security_reason":"安全评估原因"}},{"model_name":"FinalDecisionAgent","system_message":"你是最终决策智能体，负责汇总评估结果并做出最终决定。\n\n你的职责：\n1. 接收成本智能体的推荐\n2. 接收稳定性智能体的评估结果（stability_result字段）\n3. 接收安全智能体的评估结果（security_result字段）\n4. 综合分析所有评估结果\n5. 做出最终决策并输出结果\n\n重要：如果 stability_result 和 security_result 都是 true，则 allow 返回 true，否则返回 false。","id":4,"result":{"result":"目前决策推荐的机型","reason":"目前决策理由","allow":true}}],"max_iterations":3,"max_turns_per_round":10}'
```

### 完整命令（多行格式，推荐）

```bash
curl -X POST http://127.0.0.1:8080/api/v1/team/execute \
  -H "Content-Type: application/json" \
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
        "cost_optimization_result": true
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
}'
```

### 使用文件作为请求体

首先创建 JSON 文件 `cvm_request.json`：

```json
{
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
        "cost_optimization_result": true
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
}
```

然后使用命令：

```bash
curl -X POST http://127.0.0.1:8080/api/v1/team/execute \
  -H "Content-Type: application/json" \
  -d @cvm_request.json
```

### 美化输出并保存到文件

```bash
curl -X POST http://127.0.0.1:8080/api/v1/team/execute \
  -H "Content-Type: application/json" \
  -d @cvm_request.json \
  | jq '.' | tee cvm_response.json
```

### 显示详细信息（包括响应时间）

```bash
curl -X POST http://127.0.0.1:8080/api/v1/team/execute \
  -H "Content-Type: application/json" \
  -d @cvm_request.json \
  -w "\n\n状态码: %{http_code}\n总耗时: %{time_total}s\n" \
  | jq '.'
```

---

## 4. 简单审批流程

执行一个简单的三步审批流程示例。

### 完整命令（多行格式）

```bash
curl -X POST http://127.0.0.1:8080/api/v1/team/execute \
  -H "Content-Type: application/json" \
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
}'
```

### 使用文件作为请求体

创建 `approval_request.json`：

```json
{
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
}
```

然后执行：

```bash
curl -X POST http://127.0.0.1:8080/api/v1/team/execute \
  -H "Content-Type: application/json" \
  -d @approval_request.json \
  | jq '.'
```

---

## 🛠️ 常用 cURL 选项说明

| 选项 | 说明 |
|------|------|
| `-X POST` | 指定 HTTP 方法为 POST |
| `-H "Content-Type: application/json"` | 设置请求头，指定内容类型为 JSON |
| `-d '{...}'` | 发送 JSON 数据 |
| `-d @file.json` | 从文件读取 JSON 数据 |
| `-w "\n状态码: %{http_code}\n"` | 显示 HTTP 状态码 |
| `-w "耗时: %{time_total}s\n"` | 显示总耗时 |
| `-s` | 静默模式，不显示进度条 |
| `-v` | 详细模式，显示请求和响应头 |
| `\| jq '.'` | 使用 jq 美化 JSON 输出 |
| `\| tee file.json` | 同时输出到终端和文件 |

---

## 📝 响应字段说明

### 成功响应示例

```json
{
  "success": true,
  "all_passed": true,
  "total_rounds": 2,
  "final_results": {
    "ProductManager": {
      "recommendation": "...",
      "recommended_instance": "IT5.4XLARGE64",
      "recommended_operation": "缩容",
      "cost_optimization_result": true
    },
    "Engineer": {
      "stability_result": true,
      "stability_reason": "..."
    },
    "CodeReviewer": {
      "security_result": true,
      "security_reason": "..."
    },
    "FinalDecisionAgent": {
      "result": "IT5.4XLARGE64",
      "reason": "...",
      "allow": true
    }
  },
  "execution_log": [...],
  "failure_reasons": [],
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

### 字段说明

- `success`: 任务是否成功执行
- `all_passed`: 所有判断字段是否都通过
- `total_rounds`: 总执行轮次
- `final_results`: 各智能体的最终输出结果
- `execution_log`: 详细的执行日志
- `failure_reasons`: 失败原因列表（如果有）
- `timestamp`: 完成时间

---

## 🔧 故障排查

### 1. 连接被拒绝

```bash
curl: (7) Failed to connect to 127.0.0.1 port 8080: Connection refused
```

**解决方法**：确保服务已启动

```bash
python assest_new.py
```

### 2. 超时

```bash
curl: (28) Operation timed out
```

**解决方法**：增加超时时间

```bash
curl -X POST http://127.0.0.1:8080/api/v1/team/execute \
  --max-time 600 \
  -H "Content-Type: application/json" \
  -d @request.json
```

### 3. JSON 格式错误

```bash
{"detail":"JSON decode error"}
```

**解决方法**：检查 JSON 格式是否正确

```bash
# 使用 jq 验证 JSON 格式
cat request.json | jq '.'
```

---

## 💡 高级用法

### 1. 并发测试

```bash
# 同时发送 5 个请求
for i in {1..5}; do
  curl -X POST http://127.0.0.1:8080/api/v1/team/execute \
    -H "Content-Type: application/json" \
    -d @request.json &
done
wait
```

### 2. 性能测试

```bash
# 使用 time 命令测量执行时间
time curl -X POST http://127.0.0.1:8080/api/v1/team/execute \
  -H "Content-Type: application/json" \
  -d @request.json \
  -o response.json
```

### 3. 保存完整的请求和响应

```bash
curl -X POST http://127.0.0.1:8080/api/v1/team/execute \
  -H "Content-Type: application/json" \
  -d @request.json \
  -v \
  -o response.json \
  2> request_log.txt
```

---

## 📚 参考资源

- [cURL 官方文档](https://curl.se/docs/)
- [jq 官方文档](https://stedolan.github.io/jq/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [AutoGen 文档](https://microsoft.github.io/autogen/)
