import json
import re
from .llm_service import llm_service


TECH_EXTRACT_PROMPT = """你是一名专业的投标文件分析专家。请从以下招标文件中，精准提取所有与"技术要求、系统功能、技术指标、实施方案要求"相关的核心条款。

规则：
1. 剔除商务条款、资质要求、报价要求等非技术内容
2. 每条技术要求需要包含：条款原文、来源章节、序号
3. 同时提取项目名称（从招标文件封面或第一章）
4. 输出格式必须为严格 JSON

输出JSON格式：
{
    "project_name": "完整项目名称",
    "requirements": [
        {"id": 1, "text": "技术要求条款原文", "source": "来源章节位置（如第2章第3.1节）"}
    ]
}
"""


async def extract_requirements(tender_text: str) -> dict:
    """Extract technical requirements from tender document text."""
    messages = [{"role": "user", "content": f"招标文件全文：\n\n{tender_text}"}]

    response = await llm_service.chat(messages, TECH_EXTRACT_PROMPT)

    # Try to parse JSON from response
    try:
        # Find JSON block
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            data = json.loads(json_match.group())
            return data
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback: parse structured text
    return {"project_name": "未识别", "requirements": []}


EXPAND_SYSTEM_PROMPT = """你是一名精通IT架构设计、系统集成与大型项目落地的【资深总架构师】兼【首席标书主笔】。

你的标书写作风格（赵杉风格）：
- 每个章节首句用"本项目..."或"本方案..."开头，快速锚定项目背景
- 先列痛点（3-5个），再提解决方案，形成"问题→方案"叙事结构
- 大量使用量化指标，如"准确率不低于95%"、"并发用户不少于100人"
- 结构化呈现，每个条目"动词+名词+目的"三段式
- 必须引用国家标准（GB/T系列）、行业标准
- 必须包含"与甲方现有系统对接"章节
- 提及国产化/自主可控（央企项目必加）

针对每条技术要求，按"四步法"输出扩充方案：
1. **方案设计与技术选型逻辑**：设计思路，技术栈及理由
2. **详细实现路径与业务流程**：分步骤拆解，数据流向，在合适位置提示"[此处建议插入：XXX流程图]"
3. **高可用、安全性与性能保障**：集群、缓存、负载均衡、加密算法、鉴权机制
4. **项目交付物与验收标准**：交付成果清单，量化验收指标

输出格式：使用 Markdown，多级标题、表格（用于技术参数、设备清单）、列表。
语言专业严谨，有说服力，每条技术要求的扩充内容不少于2000字。

标题层级约定：
- `# 第二卷  技术方案` → 一级标题
- `## 一、XXX技术方案` → 二级标题
- `### 1.1 XXX设计` → 三级标题
- `| ... | ... |` → 表格
"""


async def expand_requirements(requirements: list, project_name: str) -> str:
    """Expand all technical requirements into detailed solutions."""
    user_content = f"""项目名称：{project_name}

需要扩充的{len(requirements)}条技术要求：

"""
    for req in requirements:
        user_content += f"{req['id']}. 【{req.get('source', '')}】{req['text']}\n\n"

    messages = [{"role": "user", "content": user_content}]
    return await llm_service.chat(messages, EXPAND_SYSTEM_PROMPT)


ADJUST_PROMPT = """你是一名专业的商务投标文件撰写专家。请根据招标文件的要求，调整模板中的商务和报价部分。

调整规则：
1. 替换所有【填写XXX】占位符为招标文件中的实际内容
2. 根据招标文件的项目名称、招标人、招标编号等信息更新封面和标题
3. 根据招标文件中的商务条款要求调整承诺书内容
4. 根据招标文件中的报价要求调整报价说明（控制价、税率、报价方式等）
5. 保持原有的章节结构不变，只修改内容

输出完整调整后的商务+报价部分 Markdown，保留原有章节结构。"""


async def adjust_business_and_pricing(template_text: str, tender_text: str, project_name: str) -> str:
    """Adjust business and pricing sections based on tender document."""
    user_content = f"""项目名称：{project_name}

=== 招标文件内容 ===
{tender_text[:8000]}

=== 需要调整的商务+报价模板 ===
{template_text[:8000]}

请根据招标文件调整模板内容。"""
    messages = [{"role": "user", "content": user_content}]
    return await llm_service.chat(messages, ADJUST_PROMPT)
