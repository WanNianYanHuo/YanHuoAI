# rag/chain_of_thought.py

"""
推理链（Chain of Thought, CoT）模块
支持结构化 JSON 输出（analysis, syndrome, treatment_principle, final_answer）与文本 fallback。
"""

import json
import re
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass
from llm.ollama_client import call_llm
from prompts.templates import COT_REASONING_PROMPT

# 结构化 CoT 时 LLM temperature（≤0.3 利于稳定 JSON）
COT_TEMPERATURE = 0.3


@dataclass
class ReasoningStep:
    """
    推理步骤数据类
    """
    step_name: str  # 步骤名称
    content: str    # 步骤内容
    confidence: Optional[float] = None  # 置信度（可选）


@dataclass
class ReasoningChain:
    """
    推理链数据类
    包含完整的推理过程
    """
    question: str
    context: str
    reasoning_steps: List[ReasoningStep]
    final_answer: str
    confidence: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "question": self.question,
            "context": self.context,
            "reasoning_steps": [
                {
                    "step_name": step.step_name,
                    "content": step.content,
                    "confidence": step.confidence
                }
                for step in self.reasoning_steps
            ],
            "final_answer": self.final_answer,
            "confidence": self.confidence
        }
    
    def format_reasoning(self) -> str:
        """格式化推理过程为可读文本"""
        lines = ["【推理过程】"]
        for i, step in enumerate(self.reasoning_steps, 1):
            lines.append(f"\n步骤 {i}: {step.step_name}")
            lines.append(f"{step.content}")
            if step.confidence is not None:
                lines.append(f"置信度: {step.confidence:.2f}")
        lines.append(f"\n【最终答案】\n{self.final_answer}")
        return "\n".join(lines)


def build_cot_prompt(question: str, context: str) -> str:
    """
    构建推理链提示词
    
    Args:
        question: 用户问题
        context: 检索到的上下文文档
        
    Returns:
        完整的推理链提示词
    """
    # 使用集中管理的 prompt 模板
    return COT_REASONING_PROMPT.format(context=context, question=question)


def build_cot_prompt_compact(question: str, context: str) -> str:
    """
    构建紧凑版推理链提示词（用于需要简洁输出的场景）
    
    Args:
        question: 用户问题
        context: 检索到的上下文文档
        
    Returns:
        紧凑版推理链提示词
    """
    prompt = f"""你是一个中医医疗问答助手。请基于给定资料，通过以下步骤思考后回答问题：

1. 理解问题：分析问题的核心要点
2. 分析资料：提取与问题相关的关键信息
3. 推理思考：基于资料进行逻辑推理
4. 生成答案：给出准确、完整的答案

【给定资料】
{context}

【问题】
{question}

请按照上述步骤思考，并在回答中展示你的推理过程，最后给出最终答案。
"""
    return prompt


def build_cot_prompt_structured(question: str, context: str) -> str:
    """
    构建结构化 CoT 提示词：要求模型严格按 JSON 输出，便于解析与存储。
    """
    return f"""你是一个中医医疗问答助手，需要基于给定资料进行深入分析和推理后回答问题。

请严格按照以下 JSON 格式输出，不要添加多余文字或 markdown 标记，只输出一个合法 JSON 对象：

{{
  "problem_understanding": "问题理解与分析",
  "information_extraction": "从资料中提取的关键信息",
  "logical_reasoning": "基于信息的逻辑推理过程",
  "final_answer": "最终回答（给用户的完整答案)"
}}

【给定资料】
{context}

【问题】
{question}

请只输出上述 JSON，不要有其他内容。
"""


def parse_cot_response_json(response: str) -> Optional[Dict[str, Any]]:
    """
    尝试从模型响应中解析结构化 JSON。
    支持裸 JSON 或 ```json ... ``` 包裹。失败返回 None。
    """
    text = (response or "").strip()
    if not text:
        return None
    # 尝试提取 ```json ... ``` 或 ``` ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    # 尝试直接解析
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "final_answer" in obj:
            return obj
    except json.JSONDecodeError:
        pass
    return None


def parse_cot_response(response: str) -> ReasoningChain:
    """
    解析模型返回的推理链响应
    
    Args:
        response: 模型的完整响应文本
        
    Returns:
        ReasoningChain对象
    """
    # 尝试解析结构化的推理步骤
    steps = []
    current_step = None
    current_content = []
    
    lines = response.split('\n')
    question = ""
    context = ""
    final_answer = ""
    
    for line in lines:
        line = line.strip()
        
        # 检测步骤标题
        if "步骤1" in line or "理解问题" in line:
            if current_step:
                steps.append(ReasoningStep(
                    step_name=current_step,
                    content="\n".join(current_content).strip()
                ))
            current_step = "理解问题"
            current_content = []
        elif "步骤2" in line or "分析资料" in line:
            if current_step:
                steps.append(ReasoningStep(
                    step_name=current_step,
                    content="\n".join(current_content).strip()
                ))
            current_step = "分析资料"
            current_content = []
        elif "步骤3" in line or "逻辑推理" in line:
            if current_step:
                steps.append(ReasoningStep(
                    step_name=current_step,
                    content="\n".join(current_content).strip()
                ))
            current_step = "逻辑推理"
            current_content = []
        elif "步骤4" in line or "得出结论" in line or "最终答案" in line:
            if current_step:
                steps.append(ReasoningStep(
                    step_name=current_step,
                    content="\n".join(current_content).strip()
                ))
            current_step = "得出结论"
            current_content = []
        elif current_step:
            # 收集当前步骤的内容
            if line and not line.startswith("【"):
                current_content.append(line)
    
    # 添加最后一个步骤
    if current_step:
        steps.append(ReasoningStep(
            step_name=current_step,
            content="\n".join(current_content).strip()
        ))
    
    # 提取最终答案（通常是最后一个步骤或"最终答案"之后的内容）
    if steps:
        final_answer = steps[-1].content
        # 如果最后一步是"得出结论"，则使用其内容
        if steps[-1].step_name == "得出结论":
            final_answer = steps[-1].content
        else:
            # 否则尝试从响应末尾提取
            final_section = response.split("最终答案")[-1] if "最终答案" in response else response
            final_answer = final_section.strip()
    
    # 如果没有解析到步骤，将整个响应作为最终答案
    if not steps:
        final_answer = response.strip()
        steps.append(ReasoningStep(
            step_name="直接回答",
            content=final_answer
        ))
    
    return ReasoningChain(
        question=question,
        context=context,
        reasoning_steps=steps,
        final_answer=final_answer
    )


def generate_with_cot(
    question: str,
    context: str,
    compact: bool = False,
    extract_answer_only: bool = False,
    stream_callback=None,
    on_complete=None,
    llm_backend=None,
    use_structured: bool = True,
    progress_callback=None,  # 进度回调函数
) -> tuple[str, Union[ReasoningChain, Dict[str, Any], None]]:
    """
    使用推理链生成答案。优先使用结构化 JSON 输出；解析失败时 fallback 到文本解析。

    Returns:
        (答案文本, 推理链对象 或 结构化 dict 或 None)
        dict 形如 {"analysis", "syndrome", "treatment_principle", "final_answer"}
    """
    response = None
    if use_structured:
        if progress_callback:
            progress_callback("理解问题", "正在分析问题核心要点...")
        prompt = build_cot_prompt_structured(question, context)
        response = call_llm(
            prompt,
            stream_callback=stream_callback,
            on_complete=on_complete,
            backend=llm_backend,
            temperature=COT_TEMPERATURE,
        )
        if not response:
            return "模型未能生成有效回答。", None
        parsed = parse_cot_response_json(response)
        if parsed is not None:
            answer = (parsed.get("final_answer") or "").strip() or "模型未能生成有效回答。"
            reasoning_dict = {
                "problem_understanding": parsed.get("problem_understanding", ""),
                "information_extraction": parsed.get("information_extraction", ""),
                "logical_reasoning": parsed.get("logical_reasoning", ""),
            }
            return answer, reasoning_dict
        # JSON 解析失败，用同一 response 走文本解析，不重复调用 LLM
    if response is None:
        # 发送 CoT 各阶段进度（初始阶段：理解问题）
        if progress_callback:
            progress_callback("理解问题", "正在分析问题核心要点...")
        
        if compact:
            prompt = build_cot_prompt_compact(question, context)
        else:
            prompt = build_cot_prompt(question, context)
        
        # 创建包装的流式回调，在不同阶段发送进度更新
        stage_markers = {
            "推理过程": "理解问题",
            "1": "理解问题",
            "2": "分析资料",
            "3": "逻辑推理",
            "4": "得出结论",
            "最终答案": "得出结论",
        }
        # 阶段顺序，确保只“前进不后退”，避免在不同标记间来回切换导致频繁重复
        stage_order = {
            "理解问题": 1,
            "分析资料": 2,
            "逻辑推理": 3,
            "得出结论": 4,
        }
        current_stage = [None]  # 使用列表以便在闭包中修改
        accumulated_text = [""]
        
        def wrapped_stream_callback(chunk: str):
            if stream_callback:
                stream_callback(chunk)
            
            # 累积文本用于检测阶段
            accumulated_text[0] += chunk
            
            # 检测阶段标记（只允许阶段单向前进，减少频繁重复的进度更新）
            if progress_callback:
                for marker, stage in stage_markers.items():
                    if marker in accumulated_text[0]:
                        # 如果当前还没有阶段，或新阶段顺序更靠后，则更新阶段
                        cur = current_stage[0]
                        if cur == stage:
                            # 同一阶段不重复发送
                            break
                        if cur is not None and stage_order.get(stage, 0) <= stage_order.get(cur, 0):
                            # 不允许从更“后面”的阶段回退到前面
                            break
                        current_stage[0] = stage
                        stage_messages = {
                            "理解问题": "正在分析问题核心要点...",
                            "分析资料": "正在提取关键信息...",
                            "逻辑推理": "正在进行多步推理...",
                            "得出结论": "正在综合分析结果...",
                        }
                        if stage in stage_messages:
                            progress_callback(stage, stage_messages[stage])
                        break
        
        # 创建包装的完成回调，发送最终阶段进度
        def wrapped_on_complete(timing):
            if progress_callback and current_stage[0] != "得出结论":
                progress_callback("得出结论", "正在综合分析结果...")
            if on_complete:
                on_complete(timing)
        
        response = call_llm(
            prompt,
            stream_callback=wrapped_stream_callback,
            on_complete=wrapped_on_complete,
            backend=llm_backend,
        )
        if not response:
            return "模型未能生成有效回答。", None
    reasoning_chain = parse_cot_response(response)
    reasoning_chain.question = question
    reasoning_chain.context = context
    if extract_answer_only:
        return reasoning_chain.final_answer, reasoning_chain
    return response, reasoning_chain


def format_cot_for_display(reasoning_chain: Optional[ReasoningChain]) -> str:
    """
    格式化推理链用于显示
    
    Args:
        reasoning_chain: 推理链对象
        
    Returns:
        格式化后的文本
    """
    if reasoning_chain is None:
        return ""
    return reasoning_chain.format_reasoning()
