import json
import os
from datetime import datetime

# 未命中问题统一存储位置
UNANSWERED_FILE = "data/unanswered_questions.jsonl"


def log_unanswered_question(question: str, reason: str):
    """
    【论文注释】
    当系统在知识库中未能检索到足够支撑回答的资料时，
    自动记录用户问题，用于后续人工补充与知识库更新。
    """

    os.makedirs(os.path.dirname(UNANSWERED_FILE), exist_ok=True)

    record = {
        "question": question,
        "reason": reason,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(UNANSWERED_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
