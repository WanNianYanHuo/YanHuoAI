<template>
  <div class="home-page">
    <div class="hero-section">
      <h1 class="title">中医目诊问答系统</h1>
      <p class="subtitle">基于 RAG 技术的智能医学知识问答平台</p>
      <div class="action-buttons">
        <el-button type="primary" size="large" @click="goToChat">
          <span class="button-icon">💬</span>
          开始问答
        </el-button>
        <el-button type="success" size="large" plain @click="goToManage">
          <span class="button-icon">📚</span>
          知识库管理
        </el-button>
      </div>
    </div>

    <div class="features-section">
      <h2>系统功能</h2>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">🤖</div>
          <h3>智能问答</h3>
          <p>基于大语言模型，结合医学知识库提供准确的专业回答</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">📖</div>
          <h3>知识检索</h3>
          <p>使用向量检索技术，快速定位相关医学文献和资料</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">💾</div>
          <h3>知识管理</h3>
          <p>支持多种格式文档导入，灵活管理医学知识库</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">⚡</div>
          <h3>流式输出</h3>
          <p>实时显示生成过程，提供流畅的交互体验</p>
        </div>
      </div>
    </div>

    <div class="examples-section">
      <h2>示例问题</h2>
      <div class="examples-grid">
        <div class="example-card" @click="askQuestion('什么是气虚证？')">
          <div class="example-icon">❓</div>
          <p>什么是气虚证？</p>
        </div>
        <div class="example-card" @click="askQuestion('糖尿病视网膜病变的早期表现有哪些？')">
          <div class="example-icon">👁️</div>
          <p>糖尿病视网膜病变的早期表现有哪些？</p>
        </div>
        <div class="example-card" @click="askQuestion('高血压的诊断标准是什么？')">
          <div class="example-icon">🩺</div>
          <p>高血压的诊断标准是什么？</p>
        </div>
        <div class="example-card" @click="askQuestion('中医目诊如何诊断疾病？')">
          <div class="example-icon">🔍</div>
          <p>中医目诊如何诊断疾病？</p>
        </div>
      </div>
    </div>

    <div class="tech-section">
      <h2>技术架构</h2>
      <div class="tech-stack">
        <div class="tech-item">
          <strong>前端：</strong>Vue 3 + Element Plus
        </div>
        <div class="tech-item">
          <strong>后端：</strong>Python FastAPI
        </div>
        <div class="tech-item">
          <strong>向量数据库：</strong>FAISS
        </div>
        <div class="tech-item">
          <strong>嵌入模型：</strong>BAAI/bge-small-zh
        </div>
        <div class="tech-item">
          <strong>大语言模型：</strong>智谱 AI / Ollama
        </div>
      </div>
    </div>

    <div class="guide-section">
      <h2>快速开始</h2>
      <div class="guide-steps">
        <div class="step">
          <div class="step-number">1</div>
          <div class="step-content">
            <h4>创建知识库</h4>
            <p>前往知识库管理页面，创建一个新的知识库</p>
          </div>
        </div>
        <div class="step">
          <div class="step-number">2</div>
          <div class="step-content">
            <h4>导入文档</h4>
            <p>支持 TXT、JSON、JSONL、Word 等多种格式</p>
          </div>
        </div>
        <div class="step">
          <div class="step-number">3</div>
          <div class="step-content">
            <h4>开始问答</h4>
            <p>选择知识库，输入问题，获取智能回答</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

function goToChat() {
  router.push('/chat');
}

function goToManage() {
  router.push('/manage');
}

function askQuestion(question) {
  router.push({ path: '/chat', query: { q: question } });
}
</script>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  height: 100%;
  overflow-y: hidden;
  box-sizing: border-box;
}

.hero-section {
  text-align: center;
  padding: 60px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
  margin-bottom: 40px;
}

.title {
  font-size: 48px;
  font-weight: 700;
  margin: 0 0 16px 0;
}

.subtitle {
  font-size: 20px;
  opacity: 0.95;
  margin: 0 0 32px 0;
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.button-icon {
  margin-right: 8px;
  font-size: 18px;
}

.features-section,
.examples-section,
.tech-section,
.guide-section {
  margin-bottom: 48px;
}

.features-section h2,
.examples-section h2,
.tech-section h2,
.guide-section h2 {
  font-size: 32px;
  font-weight: 600;
  margin-bottom: 24px;
  color: #303133;
  text-align: center;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
}

.feature-card {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 32px 24px;
  text-align: center;
  transition: all 0.3s;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.feature-card h3 {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: #303133;
}

.feature-card p {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

.examples-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.example-card {
  background: white;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 16px;
}

.example-card:hover {
  border-color: #409eff;
  background: #f0f9ff;
  transform: translateX(4px);
}

.example-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.example-card p {
  font-size: 15px;
  color: #303133;
  margin: 0;
  line-height: 1.5;
}

.tech-stack {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 32px;
}

.tech-item {
  font-size: 15px;
  color: #606266;
  line-height: 1.8;
}

.tech-item strong {
  color: #303133;
}

.guide-steps {
  display: flex;
  gap: 24px;
  justify-content: center;
  flex-wrap: wrap;
}

.step {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 24px;
  flex: 1;
  min-width: 280px;
  max-width: 350px;
}

.step-number {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
}

.step-content h4 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #303133;
}

.step-content p {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

@media (max-width: 768px) {
  .title {
    font-size: 36px;
  }
  
  .subtitle {
    font-size: 16px;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: stretch;
  }
  
  .features-grid,
  .examples-grid {
    grid-template-columns: 1fr;
  }
  
  .guide-steps {
    flex-direction: column;
  }
}
</style>
