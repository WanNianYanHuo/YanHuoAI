<template>
  <div class="admin-container">
    <h2>用户管理</h2>
    
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getToken } from '../api/auth';

const users = ref([]);
const loading = ref(true);
const error = ref('');

onMounted(() => {
  fetchUsers();
});

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
.admin-container {
  max-width: 1200px;
  margin: 0 auto;
}

h2 {
  margin-bottom: 20px;
  color: #333;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #909399;
}

.error-message {
  color: #f56c6c;
  padding: 20px;
  background: #fef0f0;
  border-radius: 4px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-retry {
  padding: 6px 16px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.user-list {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
}

th {
  background: #fafafa;
  font-weight: 600;
  color: #606266;
}

tr:hover {
  background: #f5f7fa;
}

.role-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.role-tag.admin {
  background: #f56c6c;
  color: white;
}

.role-tag.user {
  background: #409eff;
  color: white;
}

.btn-admin {
  padding: 6px 12px;
  background: #e6a23c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 8px;
}

.btn-admin:hover {
  background: #f5a623;
}

.btn-delete {
  padding: 6px 12px;
  background: #f56c6c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-delete:hover {
  background: #f23c3c;
}

.text-muted {
  color: #909399;
}

.empty-message {
  text-align: center;
  padding: 40px;
  color: #909399;
}
</style>