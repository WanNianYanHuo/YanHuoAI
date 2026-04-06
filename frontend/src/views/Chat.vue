<template>
  <div class="chat-page">
    <div class="left-panel">
      <div class="panel-header">
        <h2>设置</h2>
        <el-button type="primary" plain @click="goToKb">知识库管理</el-button>
      </div>

      <div class="panel-section">
        <h3>知识库</h3>
        <div class="switch-item">
          <span>使用知识库</span>
          <el-switch v-model="useKb" />
        </div>
        <el-select
          v-model="selectedKb"
          placeholder="选择知识库"
          :disabled="!useKb"
        >
          <el-option
            v-for="kb in kbList"
            :key="kb.kb_id"
            :label="kb.kb_name"
            :value="kb.kb_id"
          />
        </el-select>
      </div>

      <div class="panel-section" v-if="getToken()">
        <h3>会话管理</h3>
        <el-select
          v-model="currentSessionId"
          placeholder="选择或新建会话"
          @change="handleSessionChange"
        >
          <el-option
            v-for="s in sessions"
            :key="s.session_id"
            :label="s.title || '新会话'"
            :value="s.session_id"
          />
        </el-select>
        <div class="session-buttons">
          <el-button type="primary" @click="handleNewSession">新建</el-button>
          <el-button
            type="danger"
            plain
            :disabled="!currentSessionId"
            @click="handleDeleteSession"
          >
            删除
          </el-button>
        </div>
      </div>

      <div class="panel-section">
        <h3>问答模式</h3>
        <el-select v-model="llmBackend" placeholder="LLM后端">
          <el-option label="Ollama" value="ollama" />
          <el-option label="智谱AI" value="zhipu" />
        </el-select>
        <div class="switch-item">
          <span>智能路由</span>
          <el-switch v-model="useSmartRouter" />
        </div>
      </div>

      <div class="panel-section">
        <h3>调试</h3>
        <div class="switch-item">
          <span>调试模式</span>
          <el-switch v-model="debugMode" />
        </div>
      </div>
    </div>

    <div class="chat-main">
      <div class="chat-header">
        <h1>{{ currentSessionId ? ((sessions.find(s => s.session_id === currentSessionId) || {}).title || '新会话') : '知识库问答' }}</h1>
        <transition name="fade">
          <div v-if="currentProgress.visible" class="progress-badge" :class="progressBadgeClass">
            <span class="progress-text">{{ currentProgress.stage }}: {{ currentProgress.message }}</span>
          </div>
        </transition>
      </div>

      <div class="messages" ref="messagesRef">
        <div v-if="!history.length" class="empty-tip">
          <div class="empty-icon">
            <img src="@/assets/icon-placeholder.png" alt="bot-icon" style="width: 48px; height: 48px;"/>
          </div>
          <p>你好！请在下方输入问题开始对话。</p>
          <p v-if="!useKb">当前为“无知识库”模式，将由大模型直接回答。</p>
          <p v-else-if="!selectedKb">请先在左侧选择一个知识库。</p>
        </div>
        
        <template v-for="(item, idx) in history" :key="idx">
          <!-- 用户问题 -->
          <div class="message-item user-message">
            <div class="avatar-icon-container">
              <img src="@/assets/user-icon.png" alt="user-icon"/>
            </div>
            <div class="message-content-wrapper question-content">
              {{ item.question }}
            </div>
          </div>
          
          <!-- AI 回答 -->
          <div class="message-item ai-message">
            <div class="avatar-icon-container">
              <img src="@/assets/ai-icon.png" alt="ai-icon"/>
            </div>
            <div class="message-content-wrapper answer-wrapper">
              <div v-if="getAnswerMode(item)" class="main-title" :class="`mode-${getAnswerMode(item)}`">
                {{ getAnswerModeText(item) }}
              </div>

              <div v-if="debugMode && !item.pending && item.use_smart_router && item.timing?.router_info?.strategy === 'cot_rag' && parseCoTSteps(item.rawAnswer || item.answer)" class="cot-steps">
                <div class="sub-title">推理过程</div>
                <div class="steps-container">
                  <div 
                    v-for="step in parseCoTSteps(item.rawAnswer || item.answer)" 
                    :key="step.number"
                    class="step-item"
                  >
                    <div class="step-header">
                      <div class="step-title">步骤{{ step.number }}：{{ step.title }}</div>
                    </div>
                    <div class="step-content">{{ step.content }}</div>
                  </div>
                </div>
              </div>

              <div 
                class="answer" 
                v-html="item.answer || (item.pending ? '正在生成回答...' : '')"
              ></div>

              <div v-if="item.use_kb && !item.pending" class="references">
                <div class="references-header" style="display: flex; justify-content: space-between; align-items: center;">
                  <el-button size="small" plain @click="toggleReferences(idx)">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <img src="@/assets/icon-placeholder.png" alt="ref-icon" style="width: 24px; height: 24px;"/>
                      <span>{{ item.referencesExpanded ? '收起' : '引用来源' }}</span>
                    </div>
                  </el-button>
                  <span v-if="debugMode" style="color: #909399; font-size: 12px;">检索结果（调试模式）</span>
                </div>

                <div v-show="item.referencesExpanded" class="references-content">
                  <div v-if="debugMode && item.timing && item.timing.router_info" class="router-info">
                    <div class="sub-title">智能路由分析</div>
                    <div class="router-details">
                      <div class="router-item">
                        <span class="router-label">问题复杂度:</span>
                        <span class="router-value" :class="item.timing.router_info.complexity === '复杂' ? 'complex' : 'simple'">
                          {{ item.timing.router_info.complexity }}
                        </span>
                      </div>
                      <div class="router-item">
                        <span class="router-label">策略:</span>
                        <span class="router-value">{{ item.timing.router_info.strategy === 'cot_rag' ? 'CoT推理' : '普通RAG' }}</span>
                      </div>
                      <div v-if="item.timing.router_info.rewritten_question !== item.question" class="router-item full-width">
                        <span class="router-label">重写问题:</span>
                        <span class="router-value">{{ item.timing.router_info.rewritten_question }}</span>
                      </div>
                      <div v-if="item.timing.router_info.keywords" class="router-item full-width">
                        <span class="router-label">关键词:</span>
                        <span class="router-value">{{ item.timing.router_info.keywords }}</span>
                      </div>
                    </div>
                  </div>

                  <div v-if="debugMode && item.timing" class="debug-timing">
                    <div class="sub-title">性能指标</div>
                    <div class="timing-item">
                      <span class="timing-label">检索时间:</span>
                      <span class="timing-value">{{ item.timing.retrieve_time }}s</span>
                    </div>
                    <div class="timing-item">
                      <span class="timing-label">重排序时间:</span>
                      <span class="timing-value">{{ item.timing.rerank_time }}s</span>
                    </div>
                    <div class="timing-item">
                      <span class="timing-label">生成时间:</span>
                      <span class="timing-value">{{ item.timing.generate_time }}s</span>
                    </div>
                    <div v-if="item.timing.router_time" class="timing-item">
                      <span class="timing-label">路由时间:</span>
                      <span class="timing-value">{{ item.timing.router_time }}s</span>
                    </div>
                    <div class="timing-item">
                      <span class="timing-label">总时间:</span>
                      <span class="timing-value">{{ item.timing.total_time }}s</span>
                    </div>
                    <div class="timing-item">
                      <span class="timing-label">知识库使用:</span>
                      <span class="timing-value">{{ item.timing.kb_used ? '是' : '否' }}</span>
                    </div>
                  </div>

                  <div v-if="item.allRefs && item.allRefs.length > 0" class="references-list">
                    <div
                      v-for="(ref, refIdx) in (debugMode ? item.allRefs : item.refs)"
                      :key="refIdx"
                      class="reference-item"
                      :class="{ 'debug-item': debugMode && refIdx >= (item.refs?.length || 0) }"
                    >
                      <div class="reference-header">
                        <div class="reference-main">
                          <span class="reference-index">{{ refIdx + 1 }}</span>
                          <span class="reference-title">{{ ref.meta?.title || '未命名文档' }}</span>
                        </div>
                        <span v-if="ref.meta?.doc_id" class="reference-meta-inline">ID: {{ ref.meta.doc_id }}</span>
                        <span v-if="debugMode && refIdx >= (item.refs?.length || 0)" class="debug-badge">
                          未使用
                        </span>
                      </div>
                      <div class="reference-content">{{ ref.content }}</div>
                      <div class="reference-footer">
                        <span v-if="debugMode && ref.meta?.tags && ref.meta.tags.length > 0" class="reference-tags">
                          标签: {{ ref.meta.tags.join(', ') }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="no-references">
                    <div class="no-references-text">未找到相关知识块，回答基于模型通识推理</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <div class="input-area">
        <el-input
          v-model="question"
          type="textarea"
          :rows="2"
          placeholder="请输入问题..."
          :disabled="loading || (useKb && !selectedKb)"
          @keydown.enter.prevent="handleSend"
        />
        <el-button
          type="primary"
          :loading="loading"
          class="send-btn"
          :disabled="useKb && !selectedKb"
          @click="handleSend"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { marked } from 'marked';
import axios from 'axios';
import { ElMessage } from 'element-plus';
import {
  getToken,
  createChatSession,
  listChatSessions,
  deleteChatSession,
  getChatHistory,
  saveChatHistory,
} from '../api/auth';

const HISTORY_STORAGE_KEY = 'rag_chat_history';
const KB_CACHE_KEY = 'rag_selected_kb';
const LLM_BACKEND_CACHE_KEY = 'rag_llm_backend';
const USE_KB_CACHE_KEY = 'rag_use_kb';
const NO_KB_HISTORY_KEY = '__no_kb__';

const router = useRouter();
const route = useRoute();
const API_BASE = import.meta.env.VITE_PY_API_BASE_URL || 'http://127.0.0.1:8000';

const kbList = ref([]);
const selectedKb = ref('');
const history = ref([]);
const sessions = ref([]);
const currentSessionId = ref('');
const question = ref('');
const loading = ref(false);
const messagesRef = ref(null);
const llmBackend = ref('zhipu');
const useKb = ref(true);
const useSmartRouter = ref(false);
const debugMode = ref(false);

// 进度推送系统
const progressEventSource = ref(null);
const currentProgressSession = ref(null);
const currentProgress = ref({
  stage: '',
  message: '',
  visible: false
});

function _historyKey() {
  return useKb.value ? selectedKb.value : NO_KB_HISTORY_KEY;
}

function loadHistoryFromStorage() {
  try {
    const raw = localStorage.getItem(HISTORY_STORAGE_KEY);
    const data = raw ? JSON.parse(raw) : {};
    const key = _historyKey();
    const list = key ? (data[key] || []) : [];
    history.value = Array.isArray(list) ? list : [];
  } catch {
    history.value = [];
  }
}

// 从后端加载当前会话历史（仅登录用户）
async function loadHistoryFromServer() {
  const token = getToken();
  if (!token) {
    return;
  }
  const kbKey = useKb.value ? (selectedKb.value || '') : NO_KB_HISTORY_KEY;
  if (!kbKey || !currentSessionId.value) return;

  try {
    const records = await getChatHistory(kbKey, currentSessionId.value);
    if (!Array.isArray(records) || !records.length) {
      return;
    }
    const items = [];
    for (let i = 0; i < records.length - 1; i += 2) {
      const userMsg = records[i];
      const botMsg = records[i + 1];
      if (userMsg.role !== 'user' || botMsg.role !== 'assistant') continue;
      items.push({
        question: userMsg.content,
        answer: marked.parse(botMsg.content || ''),
        rawAnswer: botMsg.content || '',
        refs: [],
        allRefs: [],
        timing: null,
        pending: false,
        llm_backend: llmBackend.value,
        use_kb: useKb.value,
        kb_id: useKb.value ? selectedKb.value : null,
        use_smart_router: useSmartRouter.value,
        referencesExpanded: false,
      });
    }
    if (items.length) {
      history.value = items;
    }
  } catch (e) {
    console.warn('加载服务器会话历史失败', e);
  }
}

function saveHistoryToStorage() {
  try {
    const raw = localStorage.getItem(HISTORY_STORAGE_KEY);
    const data = raw ? JSON.parse(raw) : {};
    const key = _historyKey();
    if (!key) return;
    data[key] = history.value;
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(data));
  } catch (e) {
    console.warn('保存对话历史失败', e);
  }
}

function clearHistory() {
  history.value = [];
  saveHistoryToStorage();
  ElMessage.success(useKb.value ? '已清空当前知识库的对话历史' : '已清空“无知识库模式”的对话历史');
}

// 加载会话列表
async function loadSessions() {
  const token = getToken();
  if (!token) {
    sessions.value = [];
    currentSessionId.value = '';
    return;
  }
  const kbKey = useKb.value ? (selectedKb.value || '') : NO_KB_HISTORY_KEY;
  if (!kbKey) return;
  try {
    const list = await listChatSessions(kbKey);
    sessions.value = Array.isArray(list) ? list : [];
    if (!currentSessionId.value && sessions.value.length > 0) {
      currentSessionId.value = sessions.value[0].session_id;
    }
  } catch (e) {
    console.warn('加载会话列表失败', e);
  }
}

// 新建会话
async function handleNewSession() {
  const token = getToken();
  if (!token) {
    ElMessage.warning('请先登录再创建会话');
    return;
  }
  const kbKey = useKb.value ? (selectedKb.value || '') : NO_KB_HISTORY_KEY;
  try {
    const session = await createChatSession(kbKey, llmBackend.value);
    currentSessionId.value = session.session_id;
    // 最新会话插入到列表最前
    sessions.value = [session, ...sessions.value];
    history.value = [];
    saveHistoryToStorage();
  } catch (e) {
    console.error('创建会话失败', e);
    ElMessage.error(e.message || '创建会话失败');
  }
}

// 删除当前会话
async function handleDeleteSession() {
  if (!currentSessionId.value) return;
  try {
    await deleteChatSession(currentSessionId.value);
    sessions.value = sessions.value.filter(s => s.session_id !== currentSessionId.value);
    currentSessionId.value = sessions.value.length ? sessions.value[0].session_id : '';
    history.value = [];
    saveHistoryToStorage();
    if (currentSessionId.value) {
      await loadHistoryFromServer();
    }
    ElMessage.success('会话已删除');
  } catch (e) {
    console.error('删除会话失败', e);
    ElMessage.error(e.message || '删除会话失败');
  }
}

// 切换会话
async function handleSessionChange() {
  history.value = [];
  saveHistoryToStorage();
  await loadHistoryFromServer();
}

// 格式化相似度分数
function formatScore(score) {
  if (score === null || score === undefined) return 'N/A';
  
  // Haystack FAISS 返回的 score 通常是余弦相似度，范围 0-1
  // 如果 score 在 0-1 之间，认为是余弦相似度，转换为百分比
  if (score >= 0 && score <= 1) {
    return `${(score * 100).toFixed(1)}%`;
  }
  
  // 如果 score 大于 1，可能是其他度量，直接显示原始值
  if (score > 1) {
    return score.toFixed(3);
  }
  
  // 如果 score 是负数，可能是负的余弦相似度或距离度量
  return score.toFixed(3);
}

// 切换引用来源的展开/收起状态
function toggleReferences(index) {
  if (history.value[index]) {
    history.value[index].referencesExpanded = !history.value[index].referencesExpanded;
  }
}

// 解析 CoT 步骤
function parseCoTSteps(text) {
  if (!text) return null;
  
  // 清理 HTML 标签和实体，提取纯文本
  let cleanText = text
    .replace(/<\/?(p|div|br|span|strong|em|ul|ol|li)[^>]*>/gi, '\n')  // 块级标签转换为换行
    .replace(/<[^>]+>/g, '')  // 移除所有其他 HTML 标签
    .replace(/&nbsp;/g, ' ')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\n\s*\n/g, '\n')  // 多个连续换行合并为一个
    .trim();
  
  let steps = [];
  
  // 尝试格式1: 步骤1：标题
  const pattern1 = /步骤\s*(\d+)\s*[：:]\s*([^\n]+)/g;
  let matches1 = [...cleanText.matchAll(pattern1)];
  
  if (matches1.length >= 2) {
    // 找到标准格式
    for (let i = 0; i < matches1.length; i++) {
      const match = matches1[i];
      const stepNum = parseInt(match[1]);
      let title = match[2].trim();
      
      // 移除标题末尾可能的】符号
      title = title.replace(/】\s*$/, '').trim();
      
      // 提取内容（从标题后到下一个步骤之前）
      const startPos = match.index + match[0].length;
      const nextMatch = matches1[i + 1];
      const endPos = nextMatch ? nextMatch.index : cleanText.length;
      let content = cleanText.substring(startPos, endPos).trim();
      
      // 移除内容开头可能的】符号和末尾的【符号
      content = content.replace(/^】\s*/, '').replace(/【\s*$/, '').trim();
      const { note, normalizedContent } = extractStepNote(content);
      const fullTitle = note ? `${title} [${note}]` : title;
      
      steps.push({
        number: stepNum,
        title: fullTitle,
        content: normalizedContent
      });
    }
    return steps.length > 0 ? steps : null;
  }
  
  // 尝试格式2: 【1标题】或【步骤1：标题】
  const pattern2 = /【\s*(?:步骤\s*)?(\d+)\s*[：:]?\s*([^】]+?)】/g;
  let matches2 = [...cleanText.matchAll(pattern2)];
  
  if (matches2.length >= 2) {
    for (let i = 0; i < matches2.length; i++) {
      const match = matches2[i];
      const stepNum = parseInt(match[1]);
      let title = match[2].trim();
      
      // 提取内容（从】后到下一个【之前）
      const startPos = match.index + match[0].length;
      const nextMatch = matches2[i + 1];
      const endPos = nextMatch ? nextMatch.index : cleanText.length;
      let content = cleanText.substring(startPos, endPos).trim();
      const { note, normalizedContent } = extractStepNote(content);
      const fullTitle = note ? `${title} [${note}]` : title;
      
      steps.push({
        number: stepNum,
        title: fullTitle,
        content: normalizedContent
      });
    }
    return steps.length > 0 ? steps : null;
  }
  
  return null;
}

function extractStepNote(content) {
  if (!content) {
    return { note: '', normalizedContent: '' };
  }
  const match = content.match(/^\s*[\[【]([^\]】]+)[\]】]\s*/);
  if (!match) {
    return { note: '', normalizedContent: content };
  }
  const note = (match[1] || '').trim();
  const normalizedContent = content.slice(match[0].length).trim();
  return { note, normalizedContent };
}

// ========== 进度推送系统函数 ==========

// 创建进度会话
async function createProgressSession() {
  try {
    const response = await axios.post(`${API_BASE}/api/v1/progress/create`);
    console.log('[Progress] 会话创建成功:', response.data.session_id);
    return response.data.session_id;
  } catch (e) {
    console.error('[Progress] 创建会话失败:', e);
    return null;
  }
}

// 开始接收进度推送
function startProgressStreaming(sessionId) {
  if (progressEventSource.value) {
    progressEventSource.value.close();
    progressEventSource.value = null;
  }
  
  currentProgress.value = {
    stage: '准备中',
    message: '正在初始化...',
    visible: true
  };
  
  const url = `${API_BASE}/api/v1/progress/${sessionId}/stream`;
  console.log('[Progress] 建立SSE连接:', url);
  
  progressEventSource.value = new EventSource(url);
  
  progressEventSource.value.onmessage = (event) => {
    try {
      const progress = JSON.parse(event.data);
      console.log('[Progress] 收到更新:', progress);
      
      if (progress.error) {
        console.error('[Progress] 错误:', progress.error);
        currentProgress.value = {
          stage: '错误',
          message: progress.error,
          visible: true
        };
        progressEventSource.value.close();
        return;
      }
      
      if (progress.is_completed) {
        currentProgress.value = {
          stage: '已完成',
          message: '处理完成',
          visible: true
        };
        progressEventSource.value.close();
        setTimeout(() => {
          currentProgress.value.visible = false;
        }, 3000);
      } else if (progress.is_active && progress.current_stage) {
        const stage = (progress.current_stage || '').replace(/[🔍⚡]/g, '').trim();
        const message = (progress.current_message || '').replace(/[🔍⚡]/g, '').trim();
        currentProgress.value = {
          stage: stage,
          message: message,
          visible: true
        };
      }
    } catch (e) {
      console.error('[Progress] 解析数据失败:', e);
    }
  };
  
  progressEventSource.value.onerror = (error) => {
    console.error('[Progress] 连接错误:', error);
    if (progressEventSource.value) {
      progressEventSource.value.close();
      progressEventSource.value = null;
    }
  };
  
  progressEventSource.value.onopen = () => {
    console.log('[Progress] 连接已建立');
  };
}

// 清理进度连接
function cleanupProgress() {
  console.log('[Progress] 清理进度连接');
  
  if (progressEventSource.value) {
    progressEventSource.value.close();
    progressEventSource.value = null;
  }
  
  if (currentProgressSession.value) {
    axios.delete(`${API_BASE}/api/v1/progress/${currentProgressSession.value}`)
      .catch(e => console.error('[Progress] 删除会话失败:', e));
    currentProgressSession.value = null;
  }
  
  currentProgress.value.visible = false;
}

// 计算进度标签CSS类
const progressBadgeClass = computed(() => {
  const stage = currentProgress.value.stage;
  if (stage === '已完成') return 'completed';
  if (stage === '错误') return 'error';
  return 'active';
});

function hasCoTContent(item) {
  if (!item) return false;
  return !!parseCoTSteps(item.rawAnswer || item.answer);
}


function getAnswerMode(item) {
  if (!item || !item.use_smart_router) return '';
  const strategy = item.timing?.router_info?.strategy;
  if (strategy === 'cot_rag') return 'cot';
  if (strategy === 'simple_rag' || strategy === 'rag') return 'simple';
  // 兜底：当后端未及时返回 strategy 时，根据回答内容识别 CoT 结构
  if (hasCoTContent(item)) return 'cot';
  return 'simple';
}

function getAnswerModeText(item) {
  return getAnswerMode(item) === 'cot' ? 'CoT 深度推理模式' : '简单问答模式';
}

async function loadKbList() {
  try {
    const token = localStorage.getItem('token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const resp = await axios.get(`${API_BASE}/api/v1/knowledge-bases`, { headers });
    kbList.value = resp.data.knowledge_bases || [];
    if (kbList.value.length > 0) {
      const cached = localStorage.getItem(KB_CACHE_KEY);
      const exists = cached && kbList.value.some(k => k.kb_id === cached);
      selectedKb.value = exists ? cached : kbList.value[0].kb_id;
      localStorage.setItem(KB_CACHE_KEY, selectedKb.value);
    } else {
      selectedKb.value = '';
    }
  } catch (e) {
    console.error('获取知识库列表失败', e);
    kbList.value = [];
    selectedKb.value = '';
  }
}

onMounted(async () => {
  const cached = localStorage.getItem(KB_CACHE_KEY);
  if (cached) selectedKb.value = cached;
  const cachedBackend = localStorage.getItem(LLM_BACKEND_CACHE_KEY);
  if (cachedBackend === 'ollama' || cachedBackend === 'zhipu') llmBackend.value = cachedBackend;
  const cachedUseKb = localStorage.getItem(USE_KB_CACHE_KEY);
  if (cachedUseKb === '0' || cachedUseKb === '1') useKb.value = cachedUseKb === '1';
  await loadKbList();
  loadHistoryFromStorage();

  // 登录用户：加载会话列表与当前会话
  const token = getToken();
  if (token) {
    await loadSessions();
    if (!currentSessionId.value) {
      await handleNewSession();
    } else {
      await loadHistoryFromServer();
    }
  }
  
  // 处理 URL 参数中的问题
  const urlQuestion = route.query.q;
  if (urlQuestion && typeof urlQuestion === 'string') {
    question.value = urlQuestion;
    // 清除 URL 参数
    router.replace({ query: {} });
  }
});

watch(selectedKb, (val) => {
  if (val) {
    localStorage.setItem(KB_CACHE_KEY, val);
    loadHistoryFromStorage();
    loadSessions();
  }
});

watch(llmBackend, (val) => {
  localStorage.setItem(LLM_BACKEND_CACHE_KEY, val);
});

watch(useKb, (val) => {
  localStorage.setItem(USE_KB_CACHE_KEY, val ? '1' : '0');
  loadHistoryFromStorage();
});

function goToKb() {
  router.push({ path: '/kb', query: selectedKb.value ? { kb_id: selectedKb.value } : {} });
}

const handleSend = async () => {
  const q = question.value.trim();
  if (!q || loading.value) return;
  if (useKb.value && !selectedKb.value) return;
  // 确保存在当前会话（登录用户）
  const token = getToken();
  if (token && !currentSessionId.value) {
    await handleNewSession();
  }
  loading.value = true;
  question.value = '';

  // 创建进度会话（所有问答都使用统一的进度标签）
  let progressSessionId = await createProgressSession();
  if (progressSessionId) {
    currentProgressSession.value = progressSessionId;
    startProgressStreaming(progressSessionId);
  }

  const newItem = {
    question: q,
    answer: '',
    rawAnswer: '',  // 原始文本（用于步骤解析）
    refs: [],  // 引用信息（实际使用的）
    allRefs: [],  // 所有检索到的文档（调试模式）
    timing: null,  // 时间信息
    pending: true,
    llm_backend: llmBackend.value,
    use_kb: useKb.value,
    kb_id: useKb.value ? selectedKb.value : null,
    use_smart_router: useSmartRouter.value,  // 是否使用智能路由
    referencesExpanded: false,  // 引用来源默认收起
  };
  history.value.push(newItem);
  const itemIdx = history.value.length - 1;
  await nextTick();
  if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight;

  const reqBody = {
    question: q,
    history: [],
    kb_id: useKb.value ? selectedKb.value : null,
    llm_backend: llmBackend.value,
    use_kb: useKb.value,
    use_smart_router: useSmartRouter.value,
    progress_session_id: progressSessionId,
  };

  try {
    const response = await fetch(`${API_BASE}/rag/ask/stream`, {
      method: 'POST',
      body: JSON.stringify(reqBody),
      headers: { 'Content-Type': 'application/json' },
    });

    const reader = response.body
      .pipeThrough(new TextDecoderStream('utf-8'))
      .getReader();

    let done = false;
    let fullText = '';
    while (!done) {
      const { value, done: readerDone } = await reader.read();
      if (readerDone) break;
      const chunk = value || '';
      const events = chunk.split('\n\n').filter(Boolean);
      for (const ev of events) {
        const line = ev.trim();
        if (!line.startsWith('data:')) continue;
        const jsonStr = line.substring(5).trim();
        if (!jsonStr) continue;
        let obj;
        try {
          obj = JSON.parse(jsonStr);
        } catch {
          continue;
        }
        if (obj.error) throw new Error(obj.error);
        const content = obj.message?.content || '';
        fullText += content;
        
        // 接收引用信息和时间信息
        if (obj.done) {
          if (history.value[itemIdx]) {
            // 接收引用信息
            if (obj.refs && Array.isArray(obj.refs)) {
              history.value[itemIdx].refs = obj.refs;
            }
            // 接收所有检索结果（调试模式）
            if (obj.allRefs && Array.isArray(obj.allRefs)) {
              history.value[itemIdx].allRefs = obj.allRefs;
            } else {
              // 如果后端没有返回 allRefs，使用 refs
              history.value[itemIdx].allRefs = obj.refs || [];
            }
            // 接收时间信息
            if (obj.timing) {
              history.value[itemIdx].timing = obj.timing;
            }
          }
        }
        
        // Streaming 阶段也使用 Markdown 渲染，保证前端展示为 Markdown 格式
        if (history.value[itemIdx]) {
          history.value[itemIdx].answer = marked.parse(fullText);
          // Ensure DOM updates immediately
          await nextTick();
          // Auto-scroll to latest content
          if (messagesRef.value) {
            messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
          }
        }
        
        if (obj.done) done = true;
      }
    }

    // Parse Markdown only when streaming completes
    if (history.value[itemIdx]) {
      // 保存原始文本用于步骤解析
      history.value[itemIdx].rawAnswer = fullText;
      history.value[itemIdx].answer = marked.parse(fullText);
      history.value[itemIdx].pending = false;
    }

    // 本地缓存
    saveHistoryToStorage();

    // 登录用户则持久化到后端
    const token = getToken();
    if (token && currentSessionId.value) {
      try {
        const kbKey = useKb.value ? (selectedKb.value || '') : NO_KB_HISTORY_KEY;
        const resp = await saveChatHistory(kbKey, currentSessionId.value, q, fullText, llmBackend.value);
        // 若后端生成了会话标题，更新本地会话列表
        if (resp && resp.session_id && resp.title !== undefined) {
          const idx = sessions.value.findIndex(s => s.session_id === resp.session_id);
          if (idx >= 0) {
            sessions.value[idx].title = resp.title || sessions.value[idx].title;
          }
        }
      } catch (e) {
        console.warn('保存服务器会话历史失败', e);
      }
    }
    await nextTick();
    if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
  } catch (e) {
    console.error(e);
    ElMessage.error('提问失败：' + (e.message || '请重试'));
    question.value = q;
    if (history.value[itemIdx]) {
      history.value[itemIdx].pending = false;
      history.value[itemIdx].answer = history.value[itemIdx].answer || '（本次请求失败）';
    }
  } finally {
    loading.value = false;
    // 确保本轮问答结束后关闭并清理进度会话
    cleanupProgress();
  }
};
</script>

<style scoped>
.chat-page {
  display: flex;
  height: 100%;
  width: 100%;
  gap: 18px;
  padding: 8px;
  box-sizing: border-box;
  background: linear-gradient(180deg, #f7f9fc 0%, #f3f6fb 100%);
}

/* Left Panel Styling */
.left-panel {
  width: 280px;
  flex-shrink: 0;
  background: linear-gradient(180deg, #ffffff 0%, #fcfdff 100%);
  border-radius: 14px;
  border: 1px solid #e8edf5;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  box-shadow: 0 8px 24px rgba(54, 93, 142, 0.08);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  margin-bottom: 12px;
  border-bottom: 1px solid #ebf0f6;
}

.panel-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #25324a;
}

.panel-section {
  padding-bottom: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid #f1f4f9;
}
.panel-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.panel-section h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #4c5c78;
}

.panel-section .el-select,
.panel-section .el-button {
  width: 100%;
}

.session-buttons {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}
.session-buttons .el-button {
  flex: 1;
}

.switch-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}
.switch-item span {
  font-size: 14px;
  color: #344054;
}


/* Chat Main Area */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
  border-radius: 14px;
  border: 1px solid #e8edf5;
  box-shadow: 0 10px 30px rgba(54, 93, 142, 0.1);
}

.cot-steps .step-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background-color: #ffffff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: box-shadow 0.3s ease;
}
.cot-steps .step-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.reference-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  background-color: #ffffff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  transition: box-shadow 0.3s ease;
}
.reference-item:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.reference-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.reference-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.reference-index {
  background: #eef2ff;
  color: #4f46e5;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.reference-meta-inline {
  background: #f0f2f5;
  color: #606266;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.reference-title {
  color: #2d3f5f;
  font-size: 13px;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reference-content {
  font-size: 14px;
  color: #2d3748;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.reference-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.reference-tags {
  background: #f6f7fb;
  color: #606266;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.step-title {
  font-weight: bold;
  font-size: 14px;
}

.step-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
}

.reference-score {
  background-color: #f0f2f5;
  color: #606266;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  margin-left: auto; /* Pushes it to the right */
}

.chat-header {
  padding: 16px 20px;
  border-bottom: 1px solid #eaf0f6;
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chat-header h1 {
  margin: 0;
  font-size: 21px;
  font-weight: 600;
  color: #1f2a40;
}

/* Messages Area */
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.message-item {
  display: flex;
  gap: 12px;
  max-width: 90%;
}

.message-item.user-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-item.ai-message {
  align-self: flex-start;
}

.avatar-icon-container {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #edf2f7;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
}
.avatar-icon-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.message-content-wrapper {
  padding: 12px 16px;
  border-radius: 18px;
  line-height: 1.6;
}

.question-content {
  background: linear-gradient(135deg, #409eff 0%, #2e82f2 100%);
  color: white;
  padding: 12px 16px;
  border-radius: 18px;
  border-top-right-radius: 4px;
}
.user-message .question-content {
  border-top-right-radius: 18px;
  border-top-left-radius: 4px;
}

.answer-wrapper {
  background: linear-gradient(180deg, #f8fbff 0%, #f3f7fd 100%);
  color: #2d3748;
  width: 100%;
  border-radius: 18px;
  border-top-left-radius: 4px;
  padding: 12px 16px;
  border: 1px solid #e5edf8;
}

.answer-mode {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.main-title {
  font-size: 14px;
  font-weight: 600;
  color: #2d3f5f;
  margin-bottom: 12px;
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid transparent;
}

.main-title.mode-cot {
  background: #ecf8f1;
  color: #128a57;
  border-color: #bdebd2;
}

.main-title.mode-simple {
  background: #eef5ff;
  color: #2d67d6;
  border-color: #cfe0ff;
}

.sub-title {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin-top: 16px;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e4e7ed;
}

.references-header .toggle-icon {
  cursor: pointer;
  color: #409eff;
  font-size: 14px;
}

/* Empty State */
.empty-tip {
  margin: auto;
  text-align: center;
  color: #909399;
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

/* Input Area */
.input-area {
  padding: 16px 20px;
  border-top: 1px solid #eaf0f6;
  display: flex;
  gap: 12px;
  align-items: center;
  background-color: #fdfefe;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}
.input-area .el-textarea {
  flex: 1;
}
.send-btn {
  height: 38px;
  min-width: 84px;
  border-radius: 10px;
}
</style>
