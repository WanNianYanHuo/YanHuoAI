#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库验证与修复脚本（整合自 validate_kb_startup + simple_fix_kb）
在服务器启动前验证知识库完整性，或修复缺失的目录/映射。
应在 python 目录下运行，或从项目根运行（会自动定位 python/knowledge_bases）。
"""
import os
import sys
import json

# 定位 python 目录（脚本可能在 python/scripts/ 或项目根）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_DIR = os.path.dirname(SCRIPT_DIR)
if os.path.basename(PYTHON_DIR) != "python":
    PYTHON_DIR = os.path.join(os.getcwd(), "python")
KB_ROOT = os.path.join(PYTHON_DIR, "knowledge_bases")


def repair_kb_structure():
    """创建缺失的知识库根目录、映射文件和默认知识库目录。"""
    print("🔧 检查/修复知识库目录结构...")
    os.makedirs(KB_ROOT, exist_ok=True)
    print(f"✅ 知识库根目录: {KB_ROOT}")

    mapping_file = os.path.join(KB_ROOT, "_mapping.json")
    if not os.path.exists(mapping_file):
        default_mapping = {
            "display_to_storage": {"zhongyi": "zhongyi"},
            "storage_to_display": {"zhongyi": "zhongyi"},
            "next_numeric_id": 1,
        }
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(default_mapping, f, ensure_ascii=False, indent=2)
        print(f"✅ 已创建映射文件: _mapping.json")
    else:
        print(f"✅ 映射文件已存在")

    default_kb_dir = os.path.join(KB_ROOT, "zhongyi")
    os.makedirs(default_kb_dir, exist_ok=True)
    print(f"✅ 默认知识库目录已就绪")


def validate_knowledge_bases():
    """验证知识库完整性，返回 True 表示通过或可继续。"""
    print("🔍 验证知识库状态...")

    if not os.path.exists(KB_ROOT):
        print(f"❌ 知识库根目录不存在: {KB_ROOT}")
        print("💡 正在执行修复...")
        repair_kb_structure()
        return True

    mapping_file = os.path.join(KB_ROOT, "_mapping.json")
    if not os.path.exists(mapping_file):
        print(f"❌ 映射文件不存在: {mapping_file}")
        print("💡 正在执行修复...")
        repair_kb_structure()
        return True

    try:
        with open(mapping_file, "r", encoding="utf-8") as f:
            mapping = json.load(f)
        display_to_storage = mapping.get("display_to_storage", {})
        storage_to_display = mapping.get("storage_to_display", {})

        print(f"📚 发现 {len(display_to_storage)} 个知识库:")
        all_valid = True
        for display_name, storage_key in display_to_storage.items():
            kb_dir = os.path.join(KB_ROOT, storage_key)
            if not os.path.exists(kb_dir):
                print(f"⚠️  知识库目录不存在: {storage_key} (显示名: {display_name})")
                os.makedirs(kb_dir, exist_ok=True)
                print(f"✅ 已创建: {kb_dir}")

            faiss_file = os.path.join(kb_dir, "faiss_store.faiss")
            if os.path.exists(faiss_file):
                file_size = os.path.getsize(faiss_file)
                print(f"✅ '{display_name}' - 数据存在 ({file_size} bytes)")
                try:
                    with open(faiss_file, "rb") as f:
                        f.read(100)
                except Exception as e:
                    print(f"❌ '{display_name}' - 文件损坏: {e}")
                    all_valid = False
            else:
                print(f"⚠️  '{display_name}' - 无数据文件，首次使用时将创建")

        for storage_key, display_name in storage_to_display.items():
            if display_to_storage.get(display_name) != storage_key:
                print(f"❌ 映射不一致: {display_name} <-> {storage_key}")
                all_valid = False

        if all_valid:
            print("✅ 知识库验证通过")
        else:
            print("⚠️  发现问题，但可继续启动")
        return True
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        return False


def show_status():
    """显示知识库状态摘要。"""
    mapping_file = os.path.join(KB_ROOT, "_mapping.json")
    if not os.path.exists(mapping_file):
        print("❌ 无法获取知识库状态（映射文件不存在）")
        return
    with open(mapping_file, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    display_to_storage = mapping.get("display_to_storage", {})
    print("\n📊 知识库状态:")
    for display_name, storage_key in display_to_storage.items():
        faiss_file = os.path.join(KB_ROOT, storage_key, "faiss_store.faiss")
        status = f"✅ 有数据 ({os.path.getsize(faiss_file)} bytes)" if os.path.exists(faiss_file) else "⚠️  无数据"
        print(f"  📚 {display_name} ({storage_key}): {status}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "repair":
        repair_kb_structure()
        validate_knowledge_bases()
        show_status()
        print("\n🎉 修复完成。可启动服务器: python run_rag_server.py")
        return
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        show_status()
        return
    success = validate_knowledge_bases()
    if success:
        show_status()
        print("\n🚀 可以安全启动服务器: python run_rag_server.py")
    else:
        print("\n❌ 请先执行修复: python scripts/kb_validate_and_repair.py repair")
        sys.exit(1)


if __name__ == "__main__":
    main()
