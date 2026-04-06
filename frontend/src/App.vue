<template>
  <div class="app">
    <!-- 导航栏：登录和注册页面不显示 -->
    <nav v-if="showNavBar" class="nav">
      <div class="nav-left">
        <router-link to="/">首页</router-link>
        <router-link to="/manage">知识库管理</router-link>
        <router-link to="/chat">知识库问答</router-link>
        <router-link v-if="isAdminVal" to="/admin">用户管理</router-link>
      </div>
      <div class="nav-right">
        <div v-if="isLoggedInVal" class="user-section">
          <span class="user-info">
            {{ currentUser?.username }}
            <span v-if="isAdminVal" class="admin-badge">管理员</span>
          </span>
          <button @click="handleLogout" class="btn-logout">退出</button>
        </div>
        <div v-else class="auth-buttons">
          <router-link to="/login" class="btn-login">登录</router-link>
          <router-link to="/register" class="btn-register">注册</router-link>
        </div>
      </div>
    </nav>
    <main class="main" :class="{ 'no-padding': !showNavBar }">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { isLoggedIn, isAdmin, getUser, logout, getToken, clearInvalidToken } from './api/auth';

const router = useRouter();
const route = useRoute();
const currentUser = ref(getUser());
const token = ref(getToken());

// 响应式计算登录状态
const isLoggedInVal = computed(() => {
  return !!token.value && isLoggedIn();
});

const isAdminVal = computed(() => {
  const user = currentUser.value;
  return user && user.role === 'admin';
});

// 是否显示导航栏（登录和注册页面不显示）
const showNavBar = computed(() => {
  const noNavRoutes = ['Login', 'Register'];
  return !noNavRoutes.includes(route.name);
});

// 刷新所有状态
function refreshState() {
  // 清除无效token
  clearInvalidToken();
  
  token.value = getToken();
  currentUser.value = getUser();
  
  console.log('State refreshed:', {
    hasToken: !!token.value,
    isLoggedIn: isLoggedInVal.value,
    user: currentUser.value?.username
  });
}

// 监听路由变化
function handleRouteChange() {
  refreshState();
}

// 监听 localStorage 变化（多标签页同步）
function handleStorageChange(e) {
  if (e.key === 'token' || e.key === 'user') {
    console.log('Storage changed:', e.key, e.newValue);
    refreshState();
  }
}

function handleLogout() {
  console.log('Logging out...');
  logout();
  refreshState();
  router.push('/login');
}

// 定期检查token有效性
let tokenCheckInterval;

function startTokenCheck() {
  tokenCheckInterval = setInterval(() => {
    if (clearInvalidToken()) {
      console.log('Token expired, refreshing state');
      refreshState();
      // 如果当前页面需要登录，跳转到登录页
      if (route.meta.requiresAuth) {
        router.push({
          path: '/login',
          query: { redirect: route.fullPath }
        });
      }
    }
  }, 60000); // 每分钟检查一次
}

function stopTokenCheck() {
  if (tokenCheckInterval) {
    clearInterval(tokenCheckInterval);
    tokenCheckInterval = null;
  }
}

// 监听登录状态变化
watch(isLoggedInVal, (newVal, oldVal) => {
  console.log('Login status changed:', oldVal, '->', newVal);
  if (newVal) {
    startTokenCheck();
  } else {
    stopTokenCheck();
  }
});

// 组件挂载时添加监听
onMounted(() => {
  console.log('App mounted, initializing...');
  refreshState();
  
  if (isLoggedInVal.value) {
    startTokenCheck();
  }
  
  router.afterEach(handleRouteChange);
  window.addEventListener('storage', handleStorageChange);
  
  // 监听页面可见性变化，页面重新可见时检查token
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      refreshState();
    }
  });
});

// 组件卸载时移除监听
onUnmounted(() => {
  window.removeEventListener('storage', handleStorageChange);
  stopTokenCheck();
});
</script>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
  padding: 0;
}

.app {
  display: flex;
  flex-direction: column;
  height: 100%;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.nav {
  padding: 12px 24px;
  background: #f5f5f5;
  border-bottom: 1px solid #e5e5e5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-left {
  display: flex;
  gap: 24px;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav a {
  color: #409eff;
  text-decoration: none;
  padding: 8px 12px;
  border-radius: 4px;
  transition: all 0.3s;
}

.nav a:hover {
  background: rgba(64, 158, 255, 0.1);
}

.nav a.router-link-active {
  font-weight: 600;
  color: #1a1a1a;
  background: rgba(64, 158, 255, 0.1);
}

.user-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #333;
  font-weight: 500;
}

.admin-badge {
  background: #f56c6c;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.auth-buttons {
  display: flex;
  gap: 8px;
}

.btn-login, .btn-register {
  padding: 6px 16px;
  border-radius: 4px;
  font-size: 14px;
  text-decoration: none;
  transition: all 0.3s;
}

.btn-login {
  color: #409eff;
  background: transparent;
  border: 1px solid #409eff;
}

.btn-login:hover {
  background: #409eff;
  color: white;
}

.btn-register {
  color: white;
  background: #409eff;
  border: 1px solid #409eff;
}

.btn-register:hover {
  background: #66b1ff;
  border-color: #66b1ff;
}

.btn-logout {
  padding: 6px 16px;
  background: #909399;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.btn-logout:hover {
  background: #606266;
}

.main {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.main.no-padding {
  padding: 0;
}

@media (max-width: 768px) {
  .nav {
    flex-direction: column;
    gap: 16px;
    padding: 16px;
  }
  
  .nav-left {
    gap: 16px;
  }
  
  .main {
    padding: 16px;
  }
}
</style>