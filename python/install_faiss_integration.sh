#!/bin/bash
# 安装 Haystack 2.x FAISS 集成包

echo "正在安装 Haystack 2.x FAISS 集成..."

# 尝试安装 faiss-haystack
pip install faiss-haystack

# 如果失败，尝试通过 haystack-ai 安装
if [ $? -ne 0 ]; then
    echo "faiss-haystack 安装失败，尝试通过 haystack-ai[faiss] 安装..."
    pip install "haystack-ai[faiss]"
fi

# 验证安装
echo ""
echo "验证安装..."
python -c "from haystack_integrations.document_stores.faiss import FAISSDocumentStore; print('✅ FAISS 集成安装成功')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo ""
    echo "安装完成！请重启 Python 后端服务器。"
else
    echo ""
    echo "❌ 安装验证失败，请手动检查。"
    echo "尝试运行: pip install -r requirements.txt"
fi
