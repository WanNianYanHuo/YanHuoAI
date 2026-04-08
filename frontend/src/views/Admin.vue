<template>
  <div class="page admin-shell">
    <aside class="admin-sidebar" :class="{ collapsed: isSidebarCollapsed }">
      <div class="admin-sidebar-header">
        <button class="icon-btn" @click="toggleSidebar" :title="isSidebarCollapsed ? '展开侧栏' : '收起侧栏'">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
            <path fill="currentColor" d="M9.29 6.71a1 1 0 0 0 0 1.41L13.17 12l-3.88 3.88a1 1 0 1 0 1.42 1.41l4.58-4.58a1 1 0 0 0 0-1.42l-4.58-4.58a1 1 0 0 0-1.42 0Z"/>
          </svg>
        </button>
        <span v-if="!isSidebarCollapsed" class="admin-sidebar-title">管理设置</span>
      </div>
      <div class="admin-nav">
        <button class="nav-btn" @click="goToManage" :title="isSidebarCollapsed ? '知识库管理' : null">
          <span class="nav-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24">
              <path fill="currentColor" d="M5 5a2 2 0 0 1 2-2h9a1 1 0 0 1 0 2H7v13a1 1 0 0 1-2 0V5Zm4 2a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v11.5a1.5 1.5 0 0 1-2.098 1.356L16 18.382l-2.902 1.474A1.5 1.5 0 0 1 11 18.5Z"/>
            </svg>
          </span>
          <span v-if="!isSidebarCollapsed" class="nav-text">知识库管理</span>
        </button>
        <button class="nav-btn" @click="goToAdmin" :title="isSidebarCollapsed ? '用户管理' : null">
          <span class="nav-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24">
              <path fill="currentColor" d="M15 8a3 3 0 1 1-3-3a3 3 0 0 1 3 3Zm-9 9.25C6 14.679 8.686 13 12 13s6 1.679 6 4.25a.75.75 0 0 1-1.5 0C16.5 15.784 14.79 15 12 15s-4.5.784-4.5 2.25A.75.75 0 0 1 6 17.25Z"/>
            </svg>
          </span>
          <span v-if="!isSidebarCollapsed" class="nav-text">用户管理</span>
        </button>
      </div>

      <div class="admin-sidebar-footer">
        <button class="nav-btn" @click="toggleUserCenter" :title="isSidebarCollapsed ? '用户中心' : null">
          <span class="nav-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24">
              <path fill="currentColor" d="M12 12a4 4 0 1 0-4-4a4 4 0 0 0 4 4Zm0 2c-4.418 0-8 2.239-8 5a1 1 0 0 0 2 0c0-1.42 2.685-3 6-3s6 1.58 6 3a1 1 0 0 0 2 0c0-2.761-3.582-5-8-5Z"/>
            </svg>
          </span>
          <span v-if="!isSidebarCollapsed" class="nav-text">用户中心</span>
        </button>
        <button class="nav-btn danger" @click="handleLogout" :title="isSidebarCollapsed ? '退出登录' : null">
          <span class="nav-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24">
              <path fill="currentColor" d="M10 7a1 1 0 0 1 1-1h6a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-6a1 1 0 1 1 0-2h6V8h-6a1 1 0 0 1-1-1Zm-1.293 3.293a1 1 0 0 1 0 1.414L7.414 13H15a1 1 0 1 1 0 2H7.414l1.293 1.293a1 1 0 0 1-1.414 1.414l-3-3a1 1 0 0 1 0-1.414l3-3a1 1 0 0 1 1.414 0Z"/>
            </svg>
          </span>
          <span v-if="!isSidebarCollapsed" class="nav-text">退出登录</span>
        </button>

      </div>
    </aside>

    <main class="admin-main">
      <h2 class="admin-title">用户管理</h2>
    
    <div v-if="loading" class="loading">加载中...</div>
    
    <div v-if="error" class="error-message">
      {{ error }}
      <button @click="fetchUsers" class="btn-retry">重试</button>
    </div>
    
    <div v-if="!loading && !error" class="user-list">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>邮箱</th>
            <th>角色</th>
            <th>创建时间</th>
            <th>最后登录</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span :class="['role-tag', user.role]">
                {{ user.role === 'admin' ? '管理员' : '普通用户' }}
              </span>
            </td>
            <td>{{ formatTime(user.created_at) }}</td>
            <td>{{ formatTime(user.last_login) }}</td>
            <td>
              <button 
                v-if="user.role !== 'admin'"
                @click="setAdmin(user)"
                class="btn-admin"
              >
                设为管理员
              </button>
              <button 
                v-if="user.role !== 'admin'"
                @click="deleteUser(user)"
                class="btn-delete"
              >
                删除
              </button>
              <span v-else class="text-muted">-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-if="!loading && !error && users.length === 0" class="empty-message">
      暂无用户
    </div>
    </main>
  </div>

  <el-dialog
    v-model="userCenterOpen"
    title="用户中心"
    width="520px"
    align-center
    destroy-on-close
    class="user-center-dialog"
    modal-class="user-center-modal"
  >
    <div class="user-center-content">
      <div class="uc-header">
        <div class="uc-avatar">
          <span class="uc-avatar-icon">
            {{ (currentUser?.username || 'U').charAt(0).toUpperCase() }}
          </span>
        </div>
        <div class="uc-header-info">
          <div class="uc-name">{{ currentUser?.username || '-' }}</div>
          <div class="uc-role-badge">
            {{ currentUser?.role === 'admin' ? '管理员' : '普通用户' }}
          </div>
        </div>
      </div>

      <div class="uc-divider"></div>

      <div class="uc-grid">
        <div class="uc-item">
          <div class="uc-item-label">用户名</div>
          <div class="uc-item-value">{{ currentUser?.username || '-' }}</div>
        </div>
        <div class="uc-item">
          <div class="uc-item-label">角色</div>
          <div class="uc-item-value">{{ currentUser?.role === 'admin' ? '管理员' : '普通用户' }}</div>
        </div>
        <div v-if="currentUser?.email" class="uc-item">
          <div class="uc-item-label">邮箱</div>
          <div class="uc-item-value">{{ currentUser.email }}</div>
        </div>
        <div v-if="currentUser?.id !== undefined" class="uc-item">
          <div class="uc-item-label">用户 ID</div>
          <div class="uc-item-value">{{ currentUser.id }}</div>
        </div>
      </div>
    </div>
    <template #footer>
      <el-button type="primary" @click="userCenterOpen = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getToken, getUser, logout } from '../api/auth';

const users = ref([]);
const loading = ref(true);
const error = ref('');
const router = useRouter();
const SIDEBAR_COLLAPSED_KEY = 'admin_sidebar_collapsed';
const isSidebarCollapsed = ref(localStorage.getItem(SIDEBAR_COLLAPSED_KEY) !== '0');
const currentUser = ref(getUser() || null);
const userCenterOpen = ref(false);

onMounted(() => {
  fetchUsers();
});

function goToManage() { router.push('/manage'); }
function goToAdmin() { router.push('/admin'); }
function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
  localStorage.setItem(SIDEBAR_COLLAPSED_KEY, isSidebarCollapsed.value ? '1' : '0');
}
function toggleUserCenter() {
  currentUser.value = getUser() || null;
  userCenterOpen.value = !userCenterOpen.value;
}
function handleLogout() {
  logout();
  userCenterOpen.value = false;
  router.replace('/chat');
}

async function fetchUsers() {
  loading.value = true;
  error.value = '';
  
  try {
    const token = getToken();
    if (!token) {
      error.value = '请先登录';
      loading.value = false;
      return;
    }
    
    const response = await fetch('http://localhost:8000/api/v1/admin/users', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json',
      },
    });
    
    // 检查内容类型
    const contentType = response.headers.get('content-type');
    let data;
    
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      // 非 JSON 响应
      const text = await response.text();
      console.error('非 JSON 响应:', text.substring(0, 300));
      error.value = '后端服务器错误，请检查控制台输出';
      loading.value = false;
      return;
    }
    
    if (!response.ok) {
      if (response.status === 401) {
        error.value = data.message || '登录已过期，请重新登录';
      } else if (response.status === 403) {
        error.value = data.message || '需要管理员权限';
      } else {
        error.value = data.message || `服务器错误 (${response.status})`;
      }
      loading.value = false;
      return;
    }
    
    if (data.success) {
      users.value = data.users || [];
    } else {
      error.value = data.message || '获取用户列表失败';
    }
  } catch (e) {
    console.error('获取用户列表失败:', e);
    error.value = '网络错误，请检查后端是否运行';
  } finally {
    loading.value = false;
  }
}

async function setAdmin(user) {
  if (!confirm(`确定要将用户 ${user.username} 设为管理员吗？`)) {
    return;
  }
  
  try {
    const token = getToken();
    const response = await fetch(`http://localhost:8000/api/v1/admin/users/${user.id}/set-admin`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    const data = await response.json();
    
    if (data.success) {
      user.role = 'admin';
    } else {
      alert(data.message || '操作失败');
    }
  } catch (e) {
    alert(e.message);
  }
}

async function deleteUser(user) {
  if (!confirm(`确定要删除用户 ${user.username} 吗？此操作不可恢复。`)) {
    return;
  }
  
  try {
    const token = getToken();
    const response = await fetch(`http://localhost:8000/api/v1/admin/users/${user.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    const data = await response.json();
    
    if (data.success) {
      users.value = users.value.filter(u => u.id !== user.id);
    } else {
      alert(data.message || '删除失败');
    }
  } catch (e) {
    alert(e.message);
  }
}

function formatTime(timeStr) {
  if (!timeStr) return '-';
  try {
    return new Date(timeStr).toLocaleString('zh-CN');
  } catch {
    return timeStr;
  }
}
</script>

<style scoped>
.page {
  height: 100%;
  color: #e5e7eb;
}

.admin-topbar {
  display: none;
}

.admin-title {
  margin: 0 0 16px 0;
  color: #f3f4f6;
}

.admin-topbar-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.topbar-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #343434;
  background: #202020;
  color: #e5e7eb;
  cursor: pointer;
  white-space: nowrap;
}

.topbar-btn:hover {
  background: #2a2a2a;
  border-color: #444;
}

.topbar-btn.danger {
  border-color: #5a2e2e;
  background: #3a2020;
  color: #fca5a5;
}

.topbar-btn.danger:hover {
  background: #4a2424;
}

.btn-icon {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-text {
  font-size: 14px;
  font-weight: 600;
}

.user-center-pop {
  position: absolute;
  left: 12px;
  bottom: 120px;
  z-index: 20;
}

.user-center-content {
  display: flex;
  flex-direction: column;
}

.uc-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 8px;
}

.uc-avatar {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: #111827;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #1f2937;
}

.uc-avatar-icon {
  font-size: 16px;
  font-weight: 700;
  color: #e5e7eb;
}

.uc-header-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.uc-name {
  font-size: 14px;
  font-weight: 600;
  color: #f9fafb;
}

.uc-role-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  background: #1f2937;
  color: #9ca3af;
}

.uc-divider {
  height: 1px;
  background: #262626;
  margin: 6px 0 4px;
}

.uc-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 12px;
  padding-top: 8px;
}

.uc-item {
  border: 1px solid #262626;
  border-radius: 10px;
  background: #111111;
  padding: 10px 12px;
  min-width: 0;
}

.uc-item-label {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 6px;
}

.uc-item-value {
  font-size: 13px;
  font-weight: 700;
  color: #e5e7eb;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 弹窗与管理端风格对齐 */
:deep(.user-center-dialog.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
}

:deep(.user-center-modal) {
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.user-center-modal .el-overlay-dialog) {
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.user-center-dialog .el-dialog__header) {
  margin-right: 0;
  padding: 14px 16px;
  border-bottom: 1px solid #2a2a2a;
}

:deep(.user-center-dialog .el-dialog__title) {
  color: #f3f4f6;
  font-weight: 700;
}

:deep(.user-center-dialog .el-dialog__body) {
  padding: 16px;
}

:deep(.user-center-dialog .el-dialog__footer) {
  padding: 12px 16px 16px;
  border-top: 1px solid #2a2a2a;
}

.uc-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 2px;
  border-bottom: 1px solid #262626;
}
.uc-row:last-of-type {
  border-bottom: none;
}
.uc-label {
  font-size: 12px;
  color: #a3a3a3;
}
.uc-value {
  font-size: 13px;
  color: #e5e7eb;
  font-weight: 600;
}
.uc-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.admin-shell {
  display: flex;
  gap: 18px;
  padding: 8px;
  box-sizing: border-box;
  height: 100%;
  background: #0b0b0b;
}

.admin-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: #141414;
  border-radius: 14px;
  border: 1px solid #2a2a2a;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: width 0.2s ease, padding 0.2s ease;
  overflow: hidden;
  position: relative;
}

.admin-sidebar.collapsed {
  width: 60px;
  padding: 10px 8px;
}

.admin-sidebar-header {
  display: flex;
  justify-content: center;
  align-items: center;
}

.admin-sidebar-title {
  text-align: center;
  margin-left: 10px;
  font-size: 14px;
  font-weight: 700;
  color: #e5e7eb;
  white-space: nowrap;
}

.icon-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: 1px solid #2f2f2f;
  background: #1b1b1b;
  color: #e5e7eb;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.icon-btn:hover {
  background: #262626;
  border-color: #3a3a3a;
}

.admin-nav {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
}

.admin-sidebar-footer {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
}

.nav-btn {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid #2f2f2f;
  background: #1b1b1b;
  color: #e5e7eb;
  cursor: pointer;
}
.admin-sidebar.collapsed .nav-btn {
  width: 44px;
  height: 44px;
  padding: 0;
}
.nav-btn:hover {
  background: #262626;
  border-color: #3a3a3a;
}

.nav-btn.danger {
  border-color: #5a2e2e;
  background: #3a2020;
  color: #fca5a5;
}

.nav-btn.danger:hover {
  background: #4a2424;
}
.nav-icon {
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  line-height: 1;
}
.nav-text {
  font-size: 14px;
  font-weight: 600;
}

.admin-main {
  flex: 1;
  min-width: 0;
  background: #111111;
  border-radius: 14px;
  border: 1px solid #2a2a2a;
  padding: 20px;
  overflow: auto;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
}

.error-message {
  color: #fca5a5;
  padding: 20px;
  background: #2b1c1c;
  border: 1px solid #4a2a2a;
  border-radius: 8px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-retry {
  padding: 6px 16px;
  background: #1f2937;
  color: #f3f4f6;
  border: 1px solid #374151;
  border-radius: 8px;
  cursor: pointer;
}

.user-list {
  background: #141414;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.28);
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #2c2c2c;
}

th {
  background: #191919;
  font-weight: 600;
  color: #c4c4c4;
}

tr:hover {
  background: #1b1b1b;
}

.role-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.role-tag.admin {
  background: #3a2020;
  color: #fca5a5;
}

.role-tag.user {
  background: #1e293b;
  color: #93c5fd;
}

.btn-admin {
  padding: 6px 12px;
  background: #3b2f1f;
  color: #fcd34d;
  border: 1px solid #5b4427;
  border-radius: 8px;
  cursor: pointer;
  margin-right: 8px;
}

.btn-admin:hover {
  background: #4b3924;
}

.btn-delete {
  padding: 6px 12px;
  background: #3a2020;
  color: #fca5a5;
  border: 1px solid #5a2e2e;
  border-radius: 8px;
  cursor: pointer;
}

.btn-delete:hover {
  background: #4a2424;
}

.text-muted {
  color: #9ca3af;
}

.empty-message {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
}
</style>