# rerank/dashscope_rerank.py

import time
from typing import List, Optional, Any
import requests

from config.settings import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_RERANK_MODEL,
    RERANK_TOP_N
)


class DashScopeReranker:
    """
    阿里云 DashScope Rerank API 封装
    
    功能：
    1. 调用 DashScope API 对文档进行重排序
    2. 仅处理 Top-N 文档以降低成本
    3. 异常处理确保系统稳定
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        top_n: int = 10
    ):
        self.api_key = api_key or DASHSCOPE_API_KEY
        self.model = model or DASHSCOPE_RERANK_MODEL
        self.top_n = top_n or RERANK_TOP_N
        
        # API 端点（正确的 qwen3-vl-rerank URL）
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"
        
        if not self.api_key:
            raise ValueError("DashScope API Key 未配置，请在 config/settings.py 中设置 DASHSCOPE_API_KEY")
    
    def _extract_content(self, doc: Any) -> str:
        """提取文档内容为字符串"""
        if hasattr(doc, 'page_content'):
            content = doc.page_content
        elif hasattr(doc, 'content'):
            content = doc.content
        else:
            content = str(doc)
        
        # 处理非字符串类型
        if not isinstance(content, str):
            if hasattr(content, 'to_string'):
                return content.to_string()
            elif hasattr(content, 'to_json'):
                return content.to_json()
            else:
                return str(content)
        
        return content
    
    def rerank(
        self,
        query: str,
        documents: List[Any],
        top_n: Optional[int] = None,
        fallback_on_error: bool = True
    ) -> List[Any]:
        """
        对文档进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_n: 返回前 N 个文档（默认使用初始化时的值）
            fallback_on_error: API 失败时是否回退到原始排序（默认 True）
            
        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []
        
        top_n = top_n or self.top_n
        
        # 限制处理的文档数量（降低成本）
        docs_to_rerank = documents[:self.top_n]
        
        print(f"[RERANK] 处理 {len(docs_to_rerank)} 个文档")
        
        try:
            # 调用 API
            reranked_docs = self._call_api(query, docs_to_rerank)
            
            # 返回前 top_n 个
            return reranked_docs[:top_n]
            
        except Exception as e:
            if fallback_on_error:
                print(f"[RERANK] API 调用失败，使用原始排序: {e}")
                # 失败时返回原始排序
                return docs_to_rerank[:top_n]
            else:
                # 不回退，直接抛出异常
                raise

    
    def _call_api(self, query: str, documents: List[Any]) -> List[Any]:
        """
        调用 DashScope Rerank API
        
        Args:
            query: 查询文本
            documents: 文档列表
            
        Returns:
            重排序后的文档列表
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 提取文档内容
        doc_texts = [self._extract_content(doc) for doc in documents]
        
        payload = {
            "model": self.model,
            "input": {
                "query": query,
                "documents": doc_texts
            }
        }
        
        try:
            start_time = time.time()
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            elapsed = time.time() - start_time
            print(f"[RERANK] API 调用耗时: {elapsed:.2f}s")
            
            # 检查响应格式
            if "output" not in result or "results" not in result["output"]:
                raise ValueError(f"API 响应格式错误: {result}")
            
            results = result["output"]["results"]
            
            if not results:
                raise ValueError("API 返回空结果")
            
            # 按相关性分数排序
            # results 格式: [{"index": 0, "relevance_score": 0.95}, ...]
            sorted_results = sorted(
                results,
                key=lambda x: x.get("relevance_score", 0),
                reverse=True
            )
            
            print(f"[RERANK] 收到 {len(sorted_results)} 个排序结果")
            
            # 根据排序结果重新组织文档
            reranked_docs = []
            for item in sorted_results:
                idx = item["index"]
                score = item.get("relevance_score", 0)
                
                if 0 <= idx < len(documents):
                    doc = documents[idx]
                    
                    # 保存原始分数（如果存在）
                    if hasattr(doc, 'score'):
                        original_score = doc.score
                        # 只在调试模式下显示详细分数信息
                        # print(f"[RERANK] 文档 {idx}: 原始分数={original_score:.3f}, Rerank分数={score:.3f}")
                    
                    # 更新文档的分数（同时更新 score 属性和 metadata）
                    if hasattr(doc, 'score'):
                        # 使用 warnings 过滤器来抑制 Haystack 的 dataclass 变更警告
                        import warnings
                        with warnings.catch_warnings():
                            warnings.filterwarnings("ignore", message=".*Mutating attribute.*")
                            doc.score = score
                    
                    # 同时也存入 metadata 以便查询
                    if hasattr(doc, 'metadata'):
                        if not isinstance(doc.metadata, dict):
                            doc.metadata = {}
                        doc.metadata['rerank_score'] = score
                    
                    reranked_docs.append(doc)
            
            return reranked_docs
            
        except requests.exceptions.Timeout:
            raise Exception("API 请求超时")
        except requests.exceptions.RequestException as e:
            raise Exception(f"API 请求失败: {e}")
        except (KeyError, IndexError, ValueError) as e:
            raise Exception(f"API 响应解析失败: {e}")


def rerank_documents_with_dashscope(
    query: str,
    documents: List[Any],
    top_n: int = 5,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> List[Any]:
    """
    便捷函数：使用 DashScope 对文档进行重排序
    
    Args:
        query: 查询文本
        documents: 文档列表
        top_n: 返回前 N 个文档
        api_key: API Key（可选）
        model: 模型名称（可选）
        
    Returns:
        重排序后的文档列表
    """
    reranker = DashScopeReranker(
        api_key=api_key,
        model=model,
        top_n=10  # 处理前10个文档
    )
    
    return reranker.rerank(query, documents, top_n=top_n)
