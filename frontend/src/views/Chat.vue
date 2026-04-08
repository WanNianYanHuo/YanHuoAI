<template>
  <div class="chat-page" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <div class="left-panel">
      <div class="panel-header">
        <div v-if="!isSidebarCollapsed" class="panel-header-left">
          <img src="@/assets/应用图标.png" alt="app-icon" class="panel-logo" />
          <h2>万年AI</h2>
        </div>
        <button class="sidebar-toggle-btn" @click="toggleSidebar" :title="isSidebarCollapsed ? '展开侧栏' : '收起侧栏'">
          <span class="sidebar-toggle-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24">
              <!-- 展开状态：显示“收起侧栏” -->
              <path class="icon-collapse" fill="currentColor"
                d="M14.71 6.71a1 1 0 0 1 0 1.41L10.83 12l3.88 3.88a1 1 0 1 1-1.42 1.41l-4.58-4.58a1 1 0 0 1 0-1.42l4.58-4.58a1 1 0 0 1 1.42 0Z"
              />
              <!-- 收起状态默认：系统/菜单图标 -->
              <path class="icon-system" fill="currentColor"
                d="M4 7a1 1 0 0 1 1-1h14a1 1 0 1 1 0 2H5a1 1 0 0 1-1-1Zm0 5a1 1 0 0 1 1-1h14a1 1 0 1 1 0 2H5a1 1 0 0 1-1-1Zm1 4a1 1 0 1 0 0 2h14a1 1 0 1 0 0-2H5Z"
              />
              <!-- 收起状态悬停：显示“打开侧栏” -->
              <path class="icon-expand" fill="currentColor"
                d="M9.29 6.71a1 1 0 0 0 0 1.41L13.17 12l-3.88 3.88a1 1 0 1 0 1.42 1.41l4.58-4.58a1 1 0 0 0 0-1.42l-4.58-4.58a1 1 0 0 0-1.42 0Z"
              />
            </svg>
          </span>
        </button>
      </div>

      <div class="panel-section">
        <h3>会话</h3>
        <div class="session-buttons session-actions" style="margin-top: 0;">
          <button class="menu-action-btn" @click="handleQuickNewSession" :title="isSidebarCollapsed ? '新聊天' : null">
            <div class="flex items-center justify-center [opacity:var(--menu-item-icon-opacity,1)] icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" class="icon">
                <path
                  fill="currentColor"
                  d="M11 5a1 1 0 0 1 1 1v5h5a1 1 0 1 1 0 2h-5v5a1 1 0 1 1-2 0v-5H6a1 1 0 1 1 0-2h5V6a1 1 0 0 1 1-1Z"
                />
              </svg>
            </div>
            <span v-if="!isSidebarCollapsed">新聊天</span>
          </button>
          <button class="menu-action-btn" @click="toggleSearchInput" :title="isSidebarCollapsed ? '搜索聊天' : null">
            <div class="flex items-center justify-center [opacity:var(--menu-item-icon-opacity,1)] icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" class="icon">
                <path
                  fill="currentColor"
                  d="M10.5 3a7.5 7.5 0 1 1 4.596 13.43l3.737 3.737a1 1 0 0 1-1.414 1.414l-3.737-3.737A7.5 7.5 0 0 1 10.5 3Zm0 2a5.5 5.5 0 1 0 0 11a5.5 5.5 0 0 0 0-11Z"
                />
              </svg>
            </div>
            <span v-if="!isSidebarCollapsed">搜索聊天</span>
          </button>
        </div>
        <el-input
          v-if="showSearchInput && !isSidebarCollapsed"
          class="chat-search-input"
          v-model="chatSearchKeyword"
          placeholder="搜索聊天"
          clearable
          style="margin-top: 10px"
        />
      </div>

      <div class="panel-section" v-if="canShowKbSection && !isSidebarCollapsed">
        <h3>知识库</h3>
        <div v-if="canShowAdminControls" class="switch-item">
          <span>使用知识库</span>
          <el-switch v-model="useKb" />
        </div>
        <el-select
          v-model="selectedKb"
          placeholder="选择知识库"
          :disabled="canShowAdminControls && !useKb"
        >
          <el-option
            v-for="kb in kbList"
            :key="kb.kb_id"
            :label="kb.kb_name"
            :value="kb.kb_id"
          />
        </el-select>
      </div>

      <div class="panel-section" v-if="isLoggedIn && !isSidebarCollapsed">
        <h3>会话管理</h3>
        <el-select
          v-model="currentSessionId"
          placeholder="选择或新建会话"
          @change="handleSessionChange"
        >
          <el-option
            v-for="s in filteredSessions"
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

      <div class="panel-section" v-if="canShowAdminControls && !isSidebarCollapsed">
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

      <div class="panel-section" v-if="canShowAdminControls && !isSidebarCollapsed">
        <h3>调试</h3>
        <div class="switch-item">
          <span>调试模式</span>
          <el-switch v-model="debugMode" />
        </div>
      </div>
    </div>

    <div class="right-panel">
      <div class="chat-nav">
        <div class="top-nav">
          <div class="top-nav-left">
            <template v-if="isLoggedIn">
              <router-link to="/chat">知识库问答</router-link>
              <router-link to="/manage">知识库管理</router-link>
              <router-link v-if="isAdmin" to="/admin">用户管理</router-link>
            </template>
          </div>
          <div class="top-nav-right">
            <div v-if="isLoggedIn" class="user-section">
              <span class="user-info">
                {{ currentUser?.username }}
                <span v-if="isAdmin" class="admin-badge">管理员</span>
              </span>
              <button class="btn-logout" @click="handleLogout">退出</button>
            </div>
            <div v-else class="auth-buttons">
              <button class="btn-login" @click="showLoginModal = true">登录</button>
              <button class="btn-register" @click="showRegisterModal = true">注册</button>
            </div>
          </div>
        </div>
        <div class="chat-header">
        <h1>{{ currentSessionId ? ((sessions.find(s => s.session_id === currentSessionId) || {}).title || '新会话') : '知识库问答' }}</h1>
        <transition name="fade">
          <div v-if="currentProgress.visible" class="progress-badge" :class="progressBadgeClass">
            <span class="progress-text">{{ currentProgress.stage }}: {{ currentProgress.message }}</span>
          </div>
        </transition>
        </div>
      </div>

      <div class="chat-main">
      <div class="messages" ref="messagesRef">
        <div v-if="!filteredHistory.length" class="empty-tip">
          <p v-if="chatSearchKeyword">没有搜索到匹配聊天。</p>
          <p v-else>你好！请在下方输入问题开始对话。</p>
          <p v-if="!useKb">向 AI 聊天机器人发送消息即表示，你同意我们的条款并已阅读我们的隐私政策。</p>
          <p v-else-if="isLoggedIn && !selectedKb">请先在左侧选择一个知识库。</p>
        </div>
        
        <template v-for="(item, idx) in filteredHistory" :key="idx">
          <!-- 用户问题 -->
          <div class="message-item user-message">
            <div class="avatar-icon-container">
              <img src="@/assets/应用图标.png" alt="app-icon"/>
            </div>
            <div class="message-content-wrapper question-content">
              {{ item.question }}
            </div>
          </div>
          
          <!-- AI 回答 -->
          <div class="message-item ai-message">
            <div class="avatar-icon-container">
              <img src="@/assets/应用图标.png" alt="app-icon"/>
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
                  <el-button size="small" plain @click="toggleReferencesByItem(item)">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <img src="@/assets/应用图标.png" alt="app-icon" style="width: 24px; height: 24px;"/>
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

    <div v-if="showLoginModal" class="modal-overlay" @click.self="showLoginModal = false">
      <div class="modal-content">
        <button class="modal-close-btn" @click="showLoginModal = false">×</button>
        <h2>登录</h2>
        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="chat-login-username">用户名</label>
            <input id="chat-login-username" v-model="loginForm.username" type="text" required>
          </div>
          <div class="form-group">
            <label for="chat-login-password">密码</label>
            <input id="chat-login-password" v-model="loginForm.password" type="password" required>
          </div>
          <p v-if="loginError" class="error-message">{{ loginError }}</p>
          <button type="submit" class="btn-submit">登录</button>
        </form>
      </div>
    </div>

    <div v-if="showRegisterModal" class="modal-overlay" @click.self="showRegisterModal = false">
      <div class="modal-content">
        <button class="modal-close-btn" @click="showRegisterModal = false">×</button>
        <h2>注册</h2>
        <form @submit.prevent="handleRegister">
          <div class="form-group">
            <label for="chat-register-username">用户名</label>
            <input id="chat-register-username" v-model="registerForm.username" type="text" required>
          </div>
          <div class="form-group">
            <label for="chat-register-password">密码</label>
            <input id="chat-register-password" v-model="registerForm.password" type="password" required>
          </div>
          <p v-if="registerError" class="error-message">{{ registerError }}</p>
          <button type="submit" class="btn-submit">注册</button>
        </form>
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
  getUser,
  login,
  register,
  logout,
  clearInvalidToken,
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
const chatSearchKeyword = ref('');
const showSearchInput = ref(false);
const showLoginModal = ref(false);
const showRegisterModal = ref(false);
const loginForm = ref({ username: '', password: '' });
const registerForm = ref({ username: '', password: '' });
const loginError = ref('');
const registerError = ref('');
const isSidebarCollapsed = ref(false);
const token = ref(getToken());
const currentUser = ref(getUser() || null);

const userRole = computed(() => currentUser.value?.role || 'guest');
const isLoggedIn = computed(() => !!token.value);
const isAdmin = computed(() => userRole.value === 'admin');
const canShowKbSection = computed(() => isLoggedIn.value);
const canShowAdminControls = computed(() => isAdmin.value);

const filteredSessions = computed(() => {
  const keyword = chatSearchKeyword.value.trim().toLowerCase();
  if (!keyword) return sessions.value;
  return sessions.value.filter((s) => (s.title || '新会话').toLowerCase().includes(keyword));
});

const filteredHistory = computed(() => {
  const keyword = chatSearchKeyword.value.trim().toLowerCase();
  if (!keyword) return history.value;
  return history.value.filter((item) => {
    const q = (item.question || '').toLowerCase();
    const a = (item.rawAnswer || item.answer || '').toLowerCase();
    return q.includes(keyword) || a.includes(keyword);
  });
});

function refreshAuthState() {
  clearInvalidToken();
  token.value = getToken();
  currentUser.value = getUser() || null;
}

async function handleLogin() {
  try {
    await login(loginForm.value.username, loginForm.value.password);
    refreshAuthState();
    if (isAdmin.value) {
      showLoginModal.value = false;
      loginError.value = '';
      loginForm.value = { username: '', password: '' };
      router.replace('/manage');
      return;
    }
    showLoginModal.value = false;
    loginError.value = '';
    loginForm.value = { username: '', password: '' };
    await loadKbList();
    await loadSessions();
    if (!currentSessionId.value) {
      await handleNewSession();
    } else {
      await loadHistoryFromServer();
    }
  } catch (error) {
    loginError.value = error.message || '登录失败，请检查您的凭据';
  }
}

async function handleRegister() {
  try {
    await register(registerForm.value.username, registerForm.value.password);
    await login(registerForm.value.username, registerForm.value.password);
    refreshAuthState();
    if (isAdmin.value) {
      showRegisterModal.value = false;
      registerError.value = '';
      registerForm.value = { username: '', password: '' };
      router.replace('/manage');
      return;
    }
    showRegisterModal.value = false;
    registerError.value = '';
    registerForm.value = { username: '', password: '' };
    await loadKbList();
    await loadSessions();
    if (!currentSessionId.value) {
      await handleNewSession();
    } else {
      await loadHistoryFromServer();
    }
  } catch (error) {
    registerError.value = error.message || '注册失败，请稍后再试';
  }
}

function handleLogout() {
  logout();
  refreshAuthState();
  history.value = [];
  sessions.value = [];
  currentSessionId.value = '';
  selectedKb.value = '';
  useKb.value = false;
  try {
    // 清空本地所有聊天历史缓存
    localStorage.removeItem(HISTORY_STORAGE_KEY);
  } catch (e) {
    console.warn('清理本地聊天历史失败', e);
  }
}

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
    // 未登录时不展示本地历史
    if (!isLoggedIn.value) {
      history.value = [];
      return;
    }
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
    // 未登录时不持久化历史
    if (!isLoggedIn.value) return;
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

function toggleReferencesByItem(item) {
  const index = history.value.indexOf(item);
  if (index >= 0) {
    toggleReferences(index);
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
  refreshAuthState();
  // 管理员账号不进入问答页（双保险：除路由守卫外，页面加载时也重定向）
  if (isAdmin.value) {
    router.replace('/manage');
    return;
  }
  const cached = localStorage.getItem(KB_CACHE_KEY);
  if (cached) selectedKb.value = cached;
  const cachedBackend = localStorage.getItem(LLM_BACKEND_CACHE_KEY);
  if (cachedBackend === 'ollama' || cachedBackend === 'zhipu') llmBackend.value = cachedBackend;
  const cachedUseKb = localStorage.getItem(USE_KB_CACHE_KEY);
  if (cachedUseKb === '0' || cachedUseKb === '1') useKb.value = cachedUseKb === '1';
  if (!isLoggedIn.value) {
    useKb.value = false;
    debugMode.value = false;
  } else if (!isAdmin.value) {
    useKb.value = true;
    debugMode.value = false;
  }
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

watch([isLoggedIn, isAdmin], ([loggedIn, admin]) => {
  if (!loggedIn) {
    useKb.value = false;
    debugMode.value = false;
    useSmartRouter.value = false;
    return;
  }
  if (!admin) {
    useKb.value = true;
    debugMode.value = false;
  }
});

function goToKb() {
  router.push({ path: '/kb', query: selectedKb.value ? { kb_id: selectedKb.value } : {} });
}

async function handleQuickNewSession() {
  chatSearchKeyword.value = '';
  showSearchInput.value = false;
  if (isLoggedIn.value) {
    await handleNewSession();
    return;
  }
  history.value = [];
  saveHistoryToStorage();
}

function toggleSearchInput() {
  showSearchInput.value = !showSearchInput.value;
  if (!showSearchInput.value) {
    chatSearchKeyword.value = '';
  }
}

function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
  if (isSidebarCollapsed.value) {
    showSearchInput.value = false;
  }
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
  background: #0b0b0b;
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid #2a2a2a;
}

.top-nav-left,
.top-nav-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.top-nav-left a {
  color: #a3a3a3;
  text-decoration: none;
  padding: 7px 10px;
  border-radius: 8px;
  border: 1px solid transparent;
  font-size: 13px;
}

.top-nav-left a:hover,
.top-nav-left a.router-link-active {
  background: #1a1a1a;
  color: #f5f5f5;
  border-color: #303030;
}

.auth-buttons {
  display: inline-flex;
  gap: 2px;
  padding: 3px;
  border-radius: 10px;
  background: #131313;
  border: 1px solid #2a2a2a;
}

.btn-login,
.btn-register,
.btn-logout {
  padding: 9px 14px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  border: 1px solid transparent;
  background: transparent;
  color: #d1d5db;
}

.btn-login:hover,
.btn-register:hover,
.btn-logout:hover {
  background: #1c1c1c;
  color: #fff;
}

.user-section {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 2px;
  border-radius: 10px;
  border: 1px solid #2a2a2a;
  background: #131313;
}

.user-info {
  color: #d1d5db;
  font-size: 13px;
  padding: 0 8px;
}

.admin-badge {
  margin-left: 6px;
  background: #2a2216;
  border: 1px solid #4b3a1f;
  color: #fbbf24;
  padding: 1px 7px;
  border-radius: 999px;
  font-size: 11px;
}

/* Left Panel Styling */
.left-panel {
  width: 280px;
  flex-shrink: 0;
  background: #141414;
  border-radius: 14px;
  border: 1px solid #2a2a2a;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
  transition: width 0.2s ease, padding 0.2s ease;
}

.sidebar-collapsed .left-panel {
  width: 60px;
  padding: 10px 8px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  margin-bottom: 12px;
  border-bottom: 1px solid #2a2a2a;
}

.sidebar-collapsed .panel-header {
  justify-content: center;
}

.sidebar-collapsed .panel-header {
  padding-bottom: 8px;
  margin-bottom: 10px;
  border-bottom: none;
}

/* 收起侧栏：顶部按钮与图标按钮同规格，整体更“方” */
.sidebar-collapsed .sidebar-toggle-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
}

.panel-header-left {
  display: inline-flex;
  align-items: center;
  gap: 30px;
}

.panel-logo {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  object-fit: cover;
}

.panel-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #f3f4f6;
  line-height: 1;
}

.panel-section {
  padding-bottom: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid #272727;
}
.panel-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.panel-section h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #d1d5db;
}

.sidebar-collapsed .panel-section h3 {
  display: none;
}

/* 收起侧栏：减少分区间距，避免“空白块” */
.sidebar-collapsed .panel-section {
  padding-bottom: 10px;
  margin-bottom: 10px;
  border-bottom: none;
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
.session-actions {
  flex-direction: column;
  gap: 8px;
}

.sidebar-collapsed .session-actions {
  gap: 10px;
  align-items: center;
}

.session-buttons .el-button {
  flex: 1;
}

.menu-action-btn {
  width: 100%;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #343434;
  background: #202020;
  color: #e5e7eb;
  cursor: pointer;
}

.menu-action-btn:hover {
  background: #2a2a2a;
  border-color: #444;
}

.menu-action-btn .icon {
  width: 20px;
  height: 20px;
}

.sidebar-collapsed .menu-action-btn {
  justify-content: center;
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: 12px;
}

/* 收起侧栏：按钮外观更轻，减少视觉噪音 */
.sidebar-collapsed .menu-action-btn,
.sidebar-collapsed .sidebar-toggle-btn {
  border-color: #2f2f2f;
  background: #1b1b1b;
}

.sidebar-collapsed .menu-action-btn:hover,
.sidebar-collapsed .sidebar-toggle-btn:hover {
  background: #262626;
  border-color: #3a3a3a;
}

.sidebar-collapsed .menu-action-btn .icon {
  width: 20px;
  height: 20px;
}

/* 收起侧栏：保证顶部按钮与下方按钮同一垂直中线 */
.sidebar-collapsed .menu-action-btn,
.sidebar-collapsed .sidebar-toggle-btn {
  margin-left: auto;
  margin-right: auto;
}

.sidebar-toggle-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid #343434;
  background: #202020;
  color: #e5e7eb;
  cursor: pointer;
  transition: background 0.15s ease;
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.sidebar-toggle-btn:hover {
  background: #2a2a2a;
}

.sidebar-toggle-icon {
  position: absolute;
  inset: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.12s ease;
  opacity: 1;
}

/* 默认隐藏收起状态的“打开侧栏” */
.icon-expand {
  opacity: 0;
}

/* 展开状态：只显示“收起侧栏” */
.icon-collapse {
  opacity: 1;
}
.icon-system {
  opacity: 0;
}

/* 收起状态：默认显示系统图标；悬停侧栏时切换为“打开侧栏” */
.sidebar-collapsed .icon-collapse {
  opacity: 0;
}
.sidebar-collapsed .icon-system {
  opacity: 0;
}
.sidebar-collapsed .icon-expand {
  opacity: 1;
}

.icon-collapse,
.icon-system,
.icon-expand {
  transition: opacity 0.12s ease;
}

/* 图标大小与位置统一 */
.sidebar-toggle-icon svg {
  display: block;
  width: 20px;
  height: 20px;
}

.switch-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}
.switch-item span {
  font-size: 14px;
  color: #c4c4c4;
}


/* Chat Main Area */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: #111111;
  border-radius: 14px;
  border: 1px solid #2a2a2a;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.38);
}

.chat-nav {
  flex-shrink: 0;
}

.chat-main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.chat-search-input :deep(.el-input__wrapper) {
  background: #1f2937 !important;
  border: 1px solid #374151 !important;
  box-shadow: none !important;
}

.chat-search-input :deep(.el-input__inner) {
  color: #f3f4f6 !important;
}

.chat-search-input :deep(.el-input__inner::placeholder) {
  color: #d1d5db !important;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.72);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  position: relative;
  background: #171717;
  border: 1px solid #2a2a2a;
  padding: 22px;
  border-radius: 12px;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
}

.modal-close-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: #9ca3af;
  font-size: 18px;
  cursor: pointer;
}

.modal-content h2 {
  margin-top: 0;
  margin-bottom: 18px;
  color: #f5f5f5;
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #a3a3a3;
  font-size: 13px;
}

.form-group input {
  width: 100%;
  padding: 11px 12px;
  border-radius: 10px;
  border: 1px solid #2f2f2f;
  background: #0f0f0f;
  color: #f3f4f6;
  box-sizing: border-box;
}

.btn-submit {
  width: 100%;
  padding: 11px;
  border: 1px solid #3a3a3a;
  border-radius: 10px;
  background: #222222;
  color: #f9fafb;
  font-size: 14px;
  cursor: pointer;
}

.error-message {
  color: #f87171;
  margin-bottom: 12px;
  font-size: 13px;
}

.cot-steps .step-item {
  border: 1px solid #2f2f2f;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background-color: #171717;
  box-shadow: 0 2px 8px rgba(0,0,0,0.25);
  transition: box-shadow 0.3s ease;
}
.cot-steps .step-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.reference-item {
  border: 1px solid #2f2f2f;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  background-color: #171717;
  box-shadow: 0 1px 4px rgba(0,0,0,0.2);
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
  background: #20242d;
  color: #cfd8ff;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.reference-meta-inline {
  background: #262626;
  color: #a3a3a3;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.reference-title {
  color: #e5e7eb;
  font-size: 13px;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reference-content {
  font-size: 14px;
  color: #d1d5db;
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
  background: #242424;
  color: #bfbfbf;
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
  color: #d1d5db;
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
  border-bottom: 1px solid #2a2a2a;
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chat-header h1 {
  margin: 0;
  font-size: 21px;
  font-weight: 600;
  color: #f3f4f6;
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
  border: 1px solid #2c2c2c;
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
  background: #181818;
  color: #d1d5db;
  width: 100%;
  border-radius: 18px;
  border-top-left-radius: 4px;
  padding: 12px 16px;
  border: 1px solid #2e2e2e;
}

.answer-mode {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.main-title {
  font-size: 14px;
  font-weight: 600;
  color: #d1d5db;
  margin-bottom: 12px;
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid transparent;
}

.main-title.mode-cot {
  background: #1d2a22;
  color: #7dd3a8;
  border-color: #2f4b3d;
}

.main-title.mode-simple {
  background: #1f2530;
  color: #93c5fd;
  border-color: #324355;
}

.sub-title {
  font-size: 14px;
  font-weight: 600;
  color: #d1d5db;
  margin-top: 16px;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid #323232;
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
  color: #9ca3af;
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

/* Input Area */
.input-area {
  padding: 16px 20px;
  border-top: 1px solid #2a2a2a;
  display: flex;
  gap: 12px;
  align-items: center;
  background-color: #121212;
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
