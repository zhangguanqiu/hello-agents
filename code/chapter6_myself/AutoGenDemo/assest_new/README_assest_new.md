# AutoGen 动态智能体团队 API

## 📖 简介

`assest_new.py` 是一个基于 FastAPI 的 HTTP 服务，允许你通过 HTTP 请求动态创建和执行 AutoGen 智能体团队。相比原始的 `assest.py`，新版本提供了以下优势：

### ✨ 主要特性

1. **动态智能体创建**：通过 JSON 配置动态创建任意数量的智能体
2. **灵活的评估流程**：智能体按 ID 顺序执行，支持多轮迭代
3. **HTTP API 接口**：通过 REST API 调用，易于集成
4. **完整的日志记录**：记录每轮执行的详细信息
5. **健壮的错误处理**：完善的参数验证和异常处理
6. **自动判断逻辑**：所有判断字段都为 true 时自动跳出循环

### 🆚 与原版对比

| 特性 | assest.py | assest_new.py |
|------|-----------|---------------|
| 智能体配置 | 硬编码 | 动态配置（JSON） |
| 调用方式 | 直接运行脚本 | HTTP API |
| 灵活性 | 固定4个智能体 | 任意数量智能体 |
| 可扩展性 | 需修改代码 | 仅需修改配置 |
| 集成难度 | 较难 | 容易（HTTP） |
| 日志记录 | 控制台输出 | 结构化日志 |

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install fastapi uvicorn pydantic python-dotenv autogen-agentchat autogen-ext requests
```

### 2. 配置环境变量

确保 `.env` 文件包含以下配置：

```env
LLM_MODEL_ID=your-model-id
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.example.com/v1
LLM_TIMEOUT=60
```

### 3. 启动服务

```bash
python assest_new.py
```

服务将在 `http://0.0.0.0:8000` 启动。

### 4. 访问 API 文档

打开浏览器访问：`http://localhost:8000/docs`

## 📝 API 使用说明

### 端点列表

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 根路径，返回服务信息 |
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/team/execute` | POST | 执行智能体团队任务 |

### 请求格式

#### POST /api/v1/team/execute

**请求体示例：**

```json
{
  "initial_task": "任务描述文本",
  "modelManager": [
    {
      "model_name": "Agent1",
      "system_message": "智能体1的系统提示词",
      "id": 1,
      "result": {
        "field1": "字段1的值",
        "field2": "字段2的值",
        "judge_field": true
      }
    },
    {
      "model_name": "Agent2",
      "system_message": "智能体2的系统提示词",
      "id": 2,
      "result": {
        "field1": "字段1的值",
        "judge_field": true
      }
    }
  ],
  "max_iterations": 3,
  "max_turns_per_round": 10
}
```

**参数说明：**

- `initial_task` (必需)：任务描述
- `modelManager` (必需)：智能体配置数组
  - `model_name`：智能体名称
  - `system_message`：系统提示词
  - `id`：执行顺序（从1开始，必须连续）
  - `result`：期望的输出格式（必须包含至少一个布尔类型的判断字段）
- `max_iterations` (可选)：最大迭代次数，默认3
- `max_turns_per_round` (可选)：每轮最大对话轮次，默认10

**响应示例：**

```json
{
  "success": true,
  "all_passed": true,
  "total_rounds": 2,
  "final_results": {
    "Agent1": {
      "field1": "结果1",
      "field2": "结果2",
      "judge_field": true
    },
    "Agent2": {
      "field1": "结果1",
      "judge_field": true
    }
  },
  "execution_log": [
    {
      "round": 1,
      "timestamp": "2024-01-01T12:00:00",
      "agents_output": {...},
      "passed": false,
      "failures": ["Agent1 - judge_field 未通过: 原因"]
    },
    {
      "round": 2,
      "timestamp": "2024-01-01T12:01:00",
      "agents_output": {...},
      "passed": true,
      "failures": []
    }
  ],
  "failure_reasons": [],
  "timestamp": "2024-01-01T12:01:00"
}
```

## 💡 使用示例

### 示例1：CVM 成本优化（与原版相同场景）

```python
import requests

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
            "system_message": "你是成本管理专家...",
            "id": 1,
            "result": {
                "recommendation": "推荐原因",
                "recommended_instance": "推荐机型",
                "cost_optimization_result": True
            }
        },
        {
            "model_name": "Engineer",
            "system_message": "你是稳定性专家...",
            "id": 2,
            "result": {
                "stability_result": True,
                "stability_reason": "原因"
            }
        },
        {
            "model_name": "CodeReviewer",
            "system_message": "你是安全专家...",
            "id": 3,
            "result": {
                "security_result": True,
                "security_reason": "原因"
            }
        },
        {
            "model_name": "FinalDecisionAgent",
            "system_message": "你是最终决策者...",
            "id": 4,
            "result": {
                "result": "决策结果",
                "allow": True
            }
        }
    ],
    "max_iterations": 3
}

response = requests.post(
    "http://localhost:8000/api/v1/team/execute",
    json=request_data
)

print(response.json())
```

### 示例2：简单的审批流程

```python
request_data = {
    "initial_task": "请评估项目申请：预算100万，周期6个月",
    "modelManager": [
        {
            "model_name": "BudgetReviewer",
            "system_message": "你是预算审核专家，评估预算是否合理",
            "id": 1,
            "result": {
                "budget_approved": True,
                "comment": "评估意见"
            }
        },
        {
            "model_name": "TechReviewer",
            "system_message": "你是技术评估专家，评估技术可行性",
            "id": 2,
            "result": {
                "tech_approved": True,
                "comment": "评估意见"
            }
        },
        {
            "model_name": "FinalDecision",
            "system_message": "综合评估结果做出最终决定",
            "id": 3,
            "result": {
                "final_approved": True,
                "comment": "最终意见"
            }
        }
    ],
    "max_iterations": 2
}
```

## 🧪 测试

运行测试脚本：

```bash
# 确保服务已启动
python assest_new.py

# 在另一个终端运行测试
python test_assest_new.py
```

## 🔧 核心机制

### 1. 判断字段识别

系统会自动识别 `result` 中的布尔类型字段作为判断字段：

```python
{
    "result": {
        "data": "some data",           # 非判断字段
        "approved": true,               # 判断字段
        "security_check": false,        # 判断字段
        "comment": "some comment"       # 非判断字段
    }
}
```

### 2. 循环跳出条件

当**所有智能体**的**所有判断字段**都为 `true` 时，系统会自动跳出循环：

```python
# 第1轮
Agent1: approved=true, security_check=true   ✅
Agent2: budget_ok=false                      ❌
# 继续下一轮

# 第2轮
Agent1: approved=true, security_check=true   ✅
Agent2: budget_ok=true                       ✅
# 所有判断字段都为true，跳出循环
```

### 3. 反馈机制

当某个智能体的判断字段为 `false` 时，系统会：
1. 记录失败原因（从 `xxx_reason` 字段提取）
2. 在下一轮将反馈传递给第一个智能体
3. 第一个智能体根据反馈调整方案

## ⚙️ 配置优化建议

### 1. 系统提示词设计

```python
system_message = """你是XXX专家。

## 职责
1. 职责1
2. 职责2

## 评估标准
- 标准1
- 标准2

## 输出要求
严格按照JSON格式输出，判断字段必须是布尔值。
"""
```

### 2. 判断字段命名

建议使用清晰的命名：
- `xxx_result`：评估结果
- `xxx_approved`：是否批准
- `xxx_passed`：是否通过
- `xxx_ok`：是否正常

### 3. 原因字段命名

建议与判断字段对应：
- `xxx_result` → `xxx_reason`
- `xxx_approved` → `xxx_comment`
- `xxx_passed` → `xxx_feedback`

## 🛡️ 错误处理

系统提供完善的错误处理：

1. **参数验证**：
   - ID 必须从1开始且连续
   - 必须包含至少一个判断字段
   - 所有必需字段都必须提供

2. **运行时错误**：
   - 模型调用失败
   - JSON 解析失败
   - 超时处理

3. **HTTP 错误码**：
   - `400`：参数错误
   - `500`：服务器错误

## 📊 性能优化

1. **减少 token 消耗**：
   - 在系统提示词中要求"用最少token思考"
   - 限制输出字段数量
   - 使用简洁的任务描述

2. **减少迭代次数**：
   - 设计清晰的评估标准
   - 提供充分的上下文信息
   - 合理设置 `max_iterations`

3. **并发处理**：
   - 可以部署多个服务实例
   - 使用负载均衡

## 🔒 安全建议

1. **API 认证**：建议添加 API Key 认证
2. **速率限制**：防止滥用
3. **输入验证**：严格验证用户输入
4. **日志审计**：记录所有请求

## 📚 扩展功能

可以基于此框架扩展：

1. **数据库集成**：保存执行历史
2. **异步任务**：支持长时间运行的任务
3. **Webhook 通知**：任务完成后回调
4. **多模型支持**：不同智能体使用不同模型
5. **流式输出**：实时返回执行进度

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
