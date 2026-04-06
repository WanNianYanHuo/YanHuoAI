// 前端 API 服务模块

const API_BASE = 'http://localhost:8000/api/v1';

// 存储 token
function setToken(token) {
  localStorage.setItem('token', token);
}

function getToken() {
  return localStorage.getItem('token');
}

export { getToken };

function removeToken() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
}

// 存储用户信息
function setUser(user) {
  localStorage.setItem('user', JSON.stringify(user));
}

function getUser() {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
}

export { getUser };

// 检查token是否有效
export function isTokenValid(token = null) {
  const tokenToCheck = token || getToken();
  if (!tokenToCheck) return false;
  
  try {
    // 如果token是JWT格式，检查过期时间
    if (tokenToCheck.includes('.')) {
      const payload = JSON.parse(atob(tokenToCheck.split('.')[1]));
      const now = Date.now() / 1000;
      return payload.exp > now;
    }
    // 如果不是JWT格式，只要存在就认为有效
    return true;
  } catch (e) {
    console.warn('Token validation error:', e);
    return false;
  }
}

// 清除无效token
export function clearInvalidToken() {
  const token = getToken();
  if (token && !isTokenValid(token)) {
    console.log('Clearing invalid token');
    removeToken();
    return true;
  }
  return false;
}

// 通用请求方法
async function request(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });
    
    const data = await response.json();
    
    // 如果是401错误，清除token
    if (response.status === 401) {
      console.log('Received 401, clearing token');
      removeToken();
      throw new Error('登录已过期，请重新登录');
    }
    
    if (!response.ok) {
      throw new Error(data.detail || data.message || `请求失败 (${response.status})`);
    }
    
    return data;
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('网络连接失败，请检查网络设置');
    }
    throw error;
  }
}

// ========== 认证 API ==========

export async function login(username, password) {
  console.log('Login attempt:', username);
  
  try {
    const data = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    
    console.log('Login response:', data);
    
    if (data.success) {
      console.log('Login successful, saving token and user');
      setToken(data.token);
      setUser(data.user);
      console.log('Token saved:', getToken());
      console.log('User saved:', getUser());
    }
    
    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

export async function register(username, email, password) {
  const data = await request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, email, password }),
  });
  
  if (data.success) {
    setToken(data.token);
    setUser(data.user);
  }
  
  return data;
}

export async function getCurrentUser() {
  return await request('/auth/me');
}

export function logout() {
  console.log('Logging out, clearing token and user');
  removeToken();
}

// ========== 知识库 API ==========

export async function listKnowledgeBases() {
  return await request('/knowledge-bases');
}

export async function createKnowledgeBase(kbName) {
  return await request('/knowledge-bases', {
    method: 'POST',
    body: JSON.stringify({ kb_name: kbName }),
  });
}

export async function deleteKnowledgeBase(kbId) {
  return await request(`/knowledge-bases/${kbId}`, {
    method: 'DELETE',
  });
}

export async function getKnowledgeBaseInfo(kbId) {
  return await request(`/knowledge-bases/${kbId}/info`);
}

// ========== 会话 & 会话历史 API ==========

export async function createChatSession(kbId, llmBackend) {
  return await request('/chat/session', {
    method: 'POST',
    body: JSON.stringify({
      kb_id: kbId || '',
      llm_backend: llmBackend || null,
    }),
  });
}

export async function listChatSessions(kbId) {
  return await request(`/chat/sessions?kb_id=${encodeURIComponent(kbId || '')}`);
}

export async function deleteChatSession(sessionId) {
  return await request(`/chat/session/${encodeURIComponent(sessionId)}`, {
    method: 'DELETE',
  });
}

export async function getChatHistory(kbId, sessionId) {
  return await request(
    `/chat/history?kb_id=${encodeURIComponent(kbId || '')}&session_id=${encodeURIComponent(sessionId || '')}`,
  );
}

export async function saveChatHistory(kbId, sessionId, question, answer, llmBackend) {
  return await request('/chat/history/save', {
    method: 'POST',
    body: JSON.stringify({
      kb_id: kbId || '',
      session_id: sessionId,
      question,
      answer,
      llm_backend: llmBackend || null,
    }),
  });
}

// ========== 公共 API ==========

export async function listPublicKnowledgeBases() {
  return await request('/public/knowledge/bases');
}

// ========== 工具函数 ==========

export function isLoggedIn() {
  const token = getToken();
  return token && isTokenValid(token);
}

export function isAdmin() {
  const user = getUser();
  return user && user.role === 'admin';
}

export function getUserRole() {
  const user = getUser();
  return user ? user.role : null;
}

// ========== 管理员 API ==========

export async function listUsers() {
  const token = getToken();
  const response = await fetch(`${API_BASE}/admin/users`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.message || '获取用户列表失败');
  }
  
  return data;
}

export async function setUserAdmin(userId) {
  const token = getToken();
  const response = await fetch(`${API_BASE}/admin/users/${userId}/set-admin`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.message || '设置管理员失败');
  }
  
  return data;
}

export async function deleteUser(userId) {
  const token = getToken();
  const response = await fetch(`${API_BASE}/admin/users/${userId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.message || '删除用户失败');
  }
  
  return data;
}