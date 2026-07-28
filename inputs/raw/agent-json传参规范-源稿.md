# Agent 之间 JSON 传参规范

> 适用场景：智能建模 `data_model_design → table_select → parameter_generator` 主链路  
> 文档版本：V1.0  
> 整理日期：2026/07/27

---

## 目录

1. [为什么用 JSON 传参](#1-为什么用-json-传参)
2. [Structured Output 与 JSON Mode](#2-structured-output-与-json-mode)
3. [JSON Schema 编写指南](#3-json-schema-编写指南)
4. [三个 Agent 的 Schema 定义](#4-三个-agent-的-schema-定义)
5. [Strict Mode 注意事项](#5-strict-mode-注意事项)
6. [稳定输出的四层保障](#6-稳定输出的四层保障)
7. [与测试问题的映射](#7-与测试问题的映射)
8. [研发接入模板](#8-研发接入模板)

---

## 1. 为什么用 JSON 传参

### 1.1 优势

| 优势 | 说明 |
|------|------|
| 解耦 Agent | 每个 Agent 只关心自己的输入输出，避免上下文反复传递导致 lost in middle |
| 机器可读 | 可直接传参、映射画布节点，适合自动化执行 |
| 可校验 | 用 Schema 检查字段、类型、枚举值 |
| 可追踪 | 便于日志、回放、问题定位 |
| 版本兼容 | 通过 `schema_version` 支持平滑升级 |
| 适合编排 | Orchestrator 只负责「调 Agent → 校验 JSON → 传给下游」 |

### 1.2 劣势

| 劣势 | 说明 |
|------|------|
| LLM 输出不稳定 | 缺字段、多解释文字、语法错误、层级错乱 |
| 错误级联 | 上游错一个字段，下游选错表、参数失败、反复重试 |
| Schema 设计成本高 | 需明确字段边界、多表联合、复合指标如何表达 |
| 调试门槛高 | 用户看到「无建模规划」，研发需查哪层 JSON 断了 |
| 过度结构化 | 模糊需求被过早压成 JSON，可能丢失上下文 |

### 1.3 主链路示意

```
意图识别 Agent
   ↓
data_model_design  →  输出建模规划 JSON
   ↓
table_select       →  输出 selected_tables JSON
   ↓
parameter_generator →  输出 operator_params JSON
   ↓
可视化画布
```

**核心原则：Schema 先行 + 结构化输出 + 生成后校验 + 失败修复 + 状态化返回 + 全链路 trace**

---

## 2. Structured Output 与 JSON Mode

### 2.1 四种能力对比

| 能力 | 保证 JSON 语法 | 保证字段结构 | 保证类型/枚举 | 适合 Agent 传参 |
|------|----------------|--------------|---------------|----------------|
| 普通 Prompt | ❌ | ❌ | ❌ | ❌ |
| JSON Mode | ✅ | ❌ | ❌ | 一般 |
| Function Calling | ✅ | ✅ | 较强 | ✅ |
| Structured Output | ✅ | ✅ | ✅ | 最适合 |

- **JSON Mode**：只保证合法 JSON，不保证 Schema 一致
- **Function Calling**：模型调用预定义函数，参数由 Schema 约束
- **Structured Output / Response Schema**：输出严格符合 JSON Schema

### 2.2 主流模型支持情况

| 厂商 | JSON Mode | Function Calling | 严格 Schema |
|------|-----------|------------------|-------------|
| OpenAI (GPT-4o+) | ✅ | ✅ | ✅ Structured Output |
| Claude (4.5+) | — | ✅ Tool Use | ✅ output_config.format |
| Gemini (2.x/3.x) | 部分 | ✅ | ✅ response_schema |
| 通义千问 Qwen | ✅ | ✅ | 主要是 JSON Mode，需自研校验 |
| DeepSeek | ✅ | 部分 | 通常不稳定 |

**推荐策略：**

- 生产主链路：OpenAI / Claude / Gemini 的 Structured Output 或 strict Function Calling
- 国内 Qwen：JSON Mode + Function Calling + 程序侧 Schema 校验 + JSON 修复

### 2.3 正确调用链

```
Structured Output / Function Calling
        ↓
JSON 语法解析
        ↓
Schema 校验
        ↓
业务规则校验
        ↓
传给下游 Agent
```

语法层靠模型能力约束，语义层靠程序校验。

---

## 3. JSON Schema 编写指南

### 3.1 JSON 与 Schema 的关系

**JSON** 是数据本身：

```json
{
  "intent": "data_model_design",
  "status": "success",
  "tables": [
    { "table_name": "企业基本信息", "role": "main" }
  ]
}
```

**JSON Schema** 是规则，规定 JSON 必须长什么样。

### 3.2 核心关键字

| 字段 | 作用 | 示例 |
|------|------|------|
| `type` | 数据类型 | `"string"` / `"object"` / `"array"` |
| `properties` | 对象有哪些字段 | `{ "intent": {...} }` |
| `required` | 必填字段 | `["intent", "status"]` |
| `items` | 数组元素结构 | 数组里每个元素是什么 |
| `enum` | 限定取值 | `["success", "failed"]` |
| `description` | 字段说明（给模型看） | `"用户原始需求"` |
| `additionalProperties` | 是否允许额外字段 | 通常设为 `false` |

### 3.3 常见类型写法

**字符串：**

```json
{ "type": "string", "description": "用户建模意图" }
```

**带枚举：**

```json
{ "type": "string", "enum": ["main", "dim", "fact", "result"] }
```

**数组（对象数组）：**

```json
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "table_name": { "type": "string" }
    },
    "required": ["table_name"],
    "additionalProperties": false
  }
}
```

**可选字段（strict 模式）：**

```json
{ "type": ["string", "null"] }
```

表示可以是字符串，也可以是 null。strict 模式下，`required` 需列出所有 properties 中的字段。

### 3.4 编写步骤

1. **先画业务对象**：用户说了什么、用了哪些表、怎么关联、输出什么
2. **区分必填/可选**：必填写 `required`，可选用 `["type", "null"]`
3. **定类型**：名字用 `string`，列表用 `array`，配置块用 `object`
4. **加 description**：帮助模型理解字段语义
5. **用 enum 限制自由发挥**：状态、角色、算子类型等
6. **加版本和状态字段**：`schema_version`、`status` 便于联调与升级

### 3.5 常见错误

| 错误 | 问题 | 正确做法 |
|------|------|----------|
| 字段太自由 | `"tables": { "type": "string" }` 难解析 | 用对象数组 |
| 没有 status | 失败时乱填或空对象 | 始终返回 status |
| 算子不绑白名单 | 模型输出 `"filter_data"` 等 | 用 enum 限定 node_type |
| 一个 Schema 管所有 Agent | 过大、易漏字段 | 每个 Agent 独立 Schema |

---

## 4. 三个 Agent 的 Schema 定义

### 4.1 通用响应头（所有 Agent 共用）

```json
{
  "type": "object",
  "properties": {
    "schema_version": {
      "type": "string",
      "enum": ["1.0"],
      "description": "Schema 版本号"
    },
    "intent": {
      "type": "string",
      "description": "Agent 标识"
    },
    "task_id": {
      "type": "string",
      "description": "本次任务唯一 ID"
    },
    "status": {
      "type": "string",
      "enum": ["success", "need_clarify", "partial", "failed"],
      "description": "执行状态"
    },
    "error_code": {
      "type": ["string", "null"],
      "description": "错误码，成功时为 null"
    },
    "error_message": {
      "type": ["string", "null"],
      "description": "错误描述，成功时为 null"
    },
    "missing_info": {
      "type": "array",
      "items": { "type": "string" },
      "description": "需用户补充的信息"
    }
  },
  "required": [
    "schema_version",
    "intent",
    "task_id",
    "status",
    "error_code",
    "error_message",
    "missing_info"
  ],
  "additionalProperties": false
}
```

### 4.2 data_model_design 输出 Schema

**职责：** 将自然语言需求转为建模规划 JSON。

**Function Calling 定义：**

```json
{
  "name": "generate_model_plan",
  "description": "根据用户自然语言需求生成建模规划",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {
      "schema_version": { "type": "string", "enum": ["1.0"] },
      "intent": { "type": "string", "enum": ["data_model_design"] },
      "task_id": { "type": "string" },
      "status": {
        "type": "string",
        "enum": ["success", "need_clarify", "partial", "failed"]
      },
      "user_query": {
        "type": "string",
        "description": "用户原始需求"
      },
      "tables": {
        "type": "array",
        "description": "建模涉及的数据表",
        "items": {
          "type": "object",
          "properties": {
            "table_name": { "type": "string", "description": "表名" },
            "table_id": { "type": ["string", "null"], "description": "表 ID" },
            "role": {
              "type": "string",
              "enum": ["main", "dim", "fact", "result"],
              "description": "表在建模中的角色"
            },
            "source": {
              "type": "string",
              "enum": ["manual", "recommended", "referenced"],
              "description": "来源：手动选择/AI推荐/@引用"
            },
            "reason": { "type": "string", "description": "选用原因" }
          },
          "required": ["table_name", "table_id", "role", "source", "reason"],
          "additionalProperties": false
        }
      },
      "metrics": {
        "type": "array",
        "description": "涉及的指标",
        "items": {
          "type": "object",
          "properties": {
            "metric_name": { "type": "string" },
            "metric_type": {
              "type": "string",
              "enum": ["atomic", "derived", "composite"]
            },
            "expression": { "type": ["string", "null"] }
          },
          "required": ["metric_name", "metric_type", "expression"],
          "additionalProperties": false
        }
      },
      "joins": {
        "type": "array",
        "description": "多表关联关系",
        "items": {
          "type": "object",
          "properties": {
            "left_table": { "type": "string" },
            "right_table": { "type": "string" },
            "join_key": { "type": "string" },
            "join_type": {
              "type": "string",
              "enum": ["inner", "left", "right"]
            }
          },
          "required": ["left_table", "right_table", "join_key", "join_type"],
          "additionalProperties": false
        }
      },
      "filters": {
        "type": "array",
        "description": "筛选条件",
        "items": {
          "type": "object",
          "properties": {
            "field": { "type": "string" },
            "operator": { "type": "string" },
            "value": { "type": "string" }
          },
          "required": ["field", "operator", "value"],
          "additionalProperties": false
        }
      },
      "output_fields": {
        "type": "array",
        "items": { "type": "string" },
        "description": "期望输出字段"
      },
      "referenced_entities": {
        "type": "array",
        "description": "用户 @ 引用的实体",
        "items": {
          "type": "object",
          "properties": {
            "entity_type": {
              "type": "string",
              "enum": ["table", "node", "field"]
            },
            "entity_name": { "type": "string" },
            "entity_id": { "type": ["string", "null"] }
          },
          "required": ["entity_type", "entity_name", "entity_id"],
          "additionalProperties": false
        }
      },
      "missing_info": {
        "type": "array",
        "items": { "type": "string" }
      },
      "error_code": { "type": ["string", "null"] },
      "error_message": { "type": ["string", "null"] }
    },
    "required": [
      "schema_version",
      "intent",
      "task_id",
      "status",
      "user_query",
      "tables",
      "metrics",
      "joins",
      "filters",
      "output_fields",
      "referenced_entities",
      "missing_info",
      "error_code",
      "error_message"
    ],
    "additionalProperties": false
  }
}
```

**输出示例：**

```json
{
  "schema_version": "1.0",
  "intent": "data_model_design",
  "task_id": "task-20260727-001",
  "status": "success",
  "user_query": "做一个筛选近期公司倒闭的模型",
  "tables": [
    {
      "table_name": "企业基本信息",
      "table_id": "tb_001",
      "role": "main",
      "source": "manual",
      "reason": "用户手动指定，用于识别企业状态"
    },
    {
      "table_name": "企业异常名录",
      "table_id": "tb_002",
      "role": "dim",
      "source": "manual",
      "reason": "用户手动指定，用于补充异常信息"
    }
  ],
  "metrics": [],
  "joins": [
    {
      "left_table": "企业基本信息",
      "right_table": "企业异常名录",
      "join_key": "统一社会信用代码",
      "join_type": "inner"
    }
  ],
  "filters": [
    { "field": "status", "operator": "=", "value": "closed" }
  ],
  "output_fields": ["企业名称", "统一社会信用代码", "状态"],
  "referenced_entities": [],
  "missing_info": [],
  "error_code": null,
  "error_message": null
}
```

---

### 4.3 table_select 输出 Schema

**职责：** 从元数据中匹配并返回最终可用表。

**Function Calling 定义：**

```json
{
  "name": "select_tables",
  "description": "根据建模规划从元数据中匹配可用数据表",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {
      "schema_version": { "type": "string", "enum": ["1.0"] },
      "intent": { "type": "string", "enum": ["table_select"] },
      "task_id": { "type": "string" },
      "status": {
        "type": "string",
        "enum": ["success", "need_clarify", "partial", "failed"]
      },
      "selected_tables": {
        "type": "array",
        "description": "最终选中的数据表",
        "items": {
          "type": "object",
          "properties": {
            "table_name": { "type": "string" },
            "table_id": { "type": "string" },
            "logical_name": { "type": ["string", "null"] },
            "confidence": {
              "type": "number",
              "description": "匹配置信度 0-1"
            },
            "reason": { "type": "string" }
          },
          "required": ["table_name", "table_id", "logical_name", "confidence", "reason"],
          "additionalProperties": false
        }
      },
      "rejected_tables": {
        "type": "array",
        "description": "被过滤掉的表及原因",
        "items": {
          "type": "object",
          "properties": {
            "table_name": { "type": "string" },
            "reason": { "type": "string" }
          },
          "required": ["table_name", "reason"],
          "additionalProperties": false
        }
      },
      "missing_info": {
        "type": "array",
        "items": { "type": "string" }
      },
      "error_code": { "type": ["string", "null"] },
      "error_message": { "type": ["string", "null"] }
    },
    "required": [
      "schema_version",
      "intent",
      "task_id",
      "status",
      "selected_tables",
      "rejected_tables",
      "missing_info",
      "error_code",
      "error_message"
    ],
    "additionalProperties": false
  }
}
```

**业务规则（Schema 之外）：**

- 用户手动指定的表（`source: manual`）必须出现在 `selected_tables` 中
- `confidence < 0.6` 的推荐表不自动进入下游
- 多表场景不允许因「同类型只能二选一」而丢弃已选表

---

### 4.4 parameter_generator 输出 Schema

**职责：** 生成符合平台算子定义的节点参数。

**Function Calling 定义：**

```json
{
  "name": "generate_operator_params",
  "description": "根据建模规划生成算子节点参数",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {
      "schema_version": { "type": "string", "enum": ["1.0"] },
      "intent": { "type": "string", "enum": ["parameter_generator"] },
      "task_id": { "type": "string" },
      "status": {
        "type": "string",
        "enum": ["success", "need_clarify", "partial", "failed"]
      },
      "nodes": {
        "type": "array",
        "description": "算子节点列表",
        "items": {
          "type": "object",
          "properties": {
            "node_id": { "type": "string" },
            "node_name": { "type": "string" },
            "node_type": {
              "type": "string",
              "enum": [
                "data_input",
                "data_filter",
                "data_join",
                "aggregate",
                "deduplicate",
                "field_select",
                "sql"
              ]
            },
            "operator_code": { "type": "string" },
            "inputs": {
              "type": "array",
              "items": { "type": "string" }
            },
            "outputs": {
              "type": "array",
              "items": { "type": "string" }
            },
            "params": {
              "type": "object",
              "properties": {
                "condition": { "type": ["string", "null"] },
                "group_by": {
                  "type": "array",
                  "items": { "type": "string" }
                },
                "metrics": {
                  "type": "array",
                  "items": { "type": "string" }
                },
                "join_key": { "type": ["string", "null"] },
                "sql": { "type": ["string", "null"] }
              },
              "required": ["condition", "group_by", "metrics", "join_key", "sql"],
              "additionalProperties": false
            }
          },
          "required": [
            "node_id",
            "node_name",
            "node_type",
            "operator_code",
            "inputs",
            "outputs",
            "params"
          ],
          "additionalProperties": false
        }
      },
      "edges": {
        "type": "array",
        "description": "节点连接关系",
        "items": {
          "type": "object",
          "properties": {
            "from": { "type": "string" },
            "to": { "type": "string" }
          },
          "required": ["from", "to"],
          "additionalProperties": false
        }
      },
      "missing_info": {
        "type": "array",
        "items": { "type": "string" }
      },
      "error_code": { "type": ["string", "null"] },
      "error_message": { "type": ["string", "null"] }
    },
    "required": [
      "schema_version",
      "intent",
      "task_id",
      "status",
      "nodes",
      "edges",
      "missing_info",
      "error_code",
      "error_message"
    ],
    "additionalProperties": false
  }
}
```

**输出示例：**

```json
{
  "schema_version": "1.0",
  "intent": "parameter_generator",
  "task_id": "task-20260727-001",
  "status": "success",
  "nodes": [
    {
      "node_id": "n1",
      "node_name": "读取企业基本信息",
      "node_type": "data_input",
      "operator_code": "table_input",
      "inputs": [],
      "outputs": ["企业基本信息"],
      "params": {
        "condition": null,
        "group_by": [],
        "metrics": [],
        "join_key": null,
        "sql": null
      }
    },
    {
      "node_id": "n2",
      "node_name": "筛选倒闭企业",
      "node_type": "data_filter",
      "operator_code": "filter",
      "inputs": ["n1"],
      "outputs": ["筛选结果"],
      "params": {
        "condition": "status = 'closed'",
        "group_by": [],
        "metrics": [],
        "join_key": null,
        "sql": null
      }
    }
  ],
  "edges": [
    { "from": "n1", "to": "n2" }
  ],
  "missing_info": [],
  "error_code": null,
  "error_message": null
}
```

---

## 5. Strict Mode 注意事项

使用 OpenAI Structured Output 或 Claude strict Tool Use 时，必须遵守：

### 5.1 硬性规则

1. 每个 `object` 必须设置 `"additionalProperties": false`
2. `required` 必须列出 `properties` 中的所有字段
3. 可选字段用 `["string", "null"]` 等方式表达，不能省略
4. 枚举值优先于自由文本
5. 数组必须定义 `items`

### 5.2 错误示例 vs 正确示例

**错误：**

```json
{
  "type": "object",
  "properties": {
    "status": { "type": "string" },
    "tables": { "type": "array" }
  },
  "required": ["status"]
}
```

问题：缺 `additionalProperties`、数组无 `items`、`tables` 未列入 required。

**正确：**

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["success", "failed"]
    },
    "tables": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "table_name": { "type": "string" }
        },
        "required": ["table_name"],
        "additionalProperties": false
      }
    }
  },
  "required": ["status", "tables"],
  "additionalProperties": false
}
```

---

## 6. 稳定输出的四层保障

不要只依赖 Prompt，建议完整流程：

```
第 1 层：Structured Output / Function Calling（语法层约束）
        ↓
第 2 层：JSON 语法解析 + Schema 校验（结构层校验）
        ↓
第 3 层：业务规则校验（语义层校验）
        ↓
第 4 层：失败修复 / 追问用户（兜底）
```

### 6.1 业务规则校验示例

| 规则 | 条件 | 失败处理 |
|------|------|----------|
| 手动选表优先 | `source=manual` 的表必须在 selected_tables 中 | 报错 MANUAL_TABLE_DROPPED |
| 多表必有关联 | `tables.length > 1` 时 joins 不能为空 | 报错 MISSING_JOINS |
| 算子白名单 | node_type 必须在平台算子列表中 | 报错 INVALID_NODE_TYPE |
| 复合指标 | metric_type=composite 时 expression 不能为空 | 报错 COMPOSITE_METRIC_UNSUPPORTED |
| 低置信度过滤 | confidence < 0.6 不推荐进入下游 | 标记 need_clarify |

### 6.2 失败修复策略

**一级：语法修复** — 去 markdown、补括号  
**二级：结构修复** — 缺字段补默认值、字段 alias 映射  
**三级：语义修复** — 把校验失败原因反馈给 LLM，只修 JSON 不重规划

```text
上次输出未通过校验：
- nodes[1].node_type 不在允许范围内
- joins 为空但 tables 有 2 张表

请仅返回修正后的 JSON。
```

### 6.3 统一错误码

| 错误码 | 含义 | 对应测试问题 |
|--------|------|-------------|
| `TABLE_NOT_FOUND` | 未找到业务匹配的表 | 手动添加表报错 |
| `MANUAL_TABLE_DROPPED` | 手动选表被丢弃 | OPT-001 |
| `NO_MODEL_PLAN` | 无建模规划 | OPT-002 |
| `INVALID_NODE_PARAMS` | 算子参数不合规 | OPT-003 |
| `LOW_CONFIDENCE_TABLE` | 推荐表置信度过低 | OPT-004 |
| `ENTITY_PARSE_FAILED` | @ 引用解析失败 | OPT-005 |
| `TABLE_TYPE_CONFLICT` | 多表类型互斥 | OPT-006 |
| `COMPOSITE_METRIC_UNSUPPORTED` | 复合指标不支持 | 数据域评测 |

---

## 7. 与测试问题的映射

| 测试问题 | 对应 Agent | Schema/规则改进 |
|----------|-----------|----------------|
| 手动选表后仍推荐 | table_select | `source: manual` 优先级最高，跳过自动推荐 |
| 无建模规划 | data_model_design | 禁止空 JSON，必须返回 status |
| 算子参数生成失败 | parameter_generator | node_type/params 独立 Schema + 白名单 |
| 推荐表不准 | table_select | confidence + reason 必填，低置信度拦截 |
| 多表只能二选一 | data_model_design + table_select | tables[] 多选 + joins[] 表达关联 |
| @ 引用失败 | data_model_design | referenced_entities[] 先结构化 |
| 复合指标无法解决 | data_model_design | metric_type=composite + expression 字段 |
| 缺失会话记录 | 全链路 | 记录每步 JSON 输入输出 |

---

## 8. 研发接入模板

### 8.1 Agent 契约声明

每个 Agent 发布时需声明：

```
Agent 名称：data_model_design
Schema 版本：1.0
输入：user_query, referenced_entities, manual_tables（可选）
输出：generate_model_plan JSON
依赖：元数据服务、指标服务
错误码：TABLE_NOT_FOUND, NO_MODEL_PLAN, COMPOSITE_METRIC_UNSUPPORTED
```

### 8.2 调用流程伪代码

```python
def run_modeling_pipeline(user_query, manual_tables=None):
    # 1. 建模规划
    plan = call_agent("data_model_design", {
        "user_query": user_query,
        "manual_tables": manual_tables
    })
    plan_json = parse_and_validate(plan, schema=MODEL_PLAN_SCHEMA)
    plan_json = validate_business_rules(plan_json)
    if plan_json["status"] != "success":
        return plan_json  # 追问用户或报错

    # 2. 选表
    tables = call_agent("table_select", {"plan": plan_json})
    tables_json = parse_and_validate(tables, schema=TABLE_SELECT_SCHEMA)
    tables_json = validate_business_rules(tables_json)

    # 3. 参数生成
    params = call_agent("parameter_generator", {
        "plan": plan_json,
        "selected_tables": tables_json
    })
    params_json = parse_and_validate(params, schema=PARAM_GENERATOR_SCHEMA)
    params_json = validate_business_rules(params_json)

    # 4. 渲染画布
    render_to_canvas(params_json)
    return params_json
```

### 8.3 日志 Trace 模板

每次 Agent 调用记录：

```json
{
  "trace_id": "trace-001",
  "agent": "data_model_design",
  "timestamp": "2026-07-27T13:00:00Z",
  "input": { "user_query": "..." },
  "raw_llm_output": "...",
  "parsed_json": { ... },
  "schema_valid": true,
  "business_valid": true,
  "downstream_result": "passed to table_select"
}
```

---

## 附录：变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| V1.0 | 2026/07/27 | 初版：JSON 传参规范 + 三 Agent Schema + 研发模板 |
