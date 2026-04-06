<template>
  <div class="auth-page">
    <div class="login-box">
      <h2>登录</h2>
      
      <!-- 显示错误提示 -->
      <div v-if="routeError" class="warning-message">
        <div v-if="routeError === 'admin_required'">
          ⚠️ 该页面需要管理员权限，请使用管理员账号登录
        </div>
        <div v-else>
          ⚠️ 请先登录后再访问该页面
        </div>
      </div>
      
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>用户名</label>
          <input 
            v-model="form.username" 
            type="text" 
            placeholder="请输入用户名"
            required
            :disabled="loading"
          />
        </div>
        
        <div class="form-group">
          <label>密码</label>
          <input 
            v-model="form.password" 
            type="password" 
            placeholder="请输入密码"
            required
            :disabled="loading"
          />
        </div>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <button type="submit" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      
      <div class="links">
        <router-link to="/register">没有账号？立即注册</router-link>
        <span class="divider">|</span>
        <router-link to="/">返回首页</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { login } from '../api/auth';

const router = useRouter();
const route = useRoute();

const form = reactive({
  username: '',
  password: '',
});

const loading = ref(false);
const error = ref('');
const routeError = ref('');

// 获取重定向路径和错误信息
onMounted(() => {
  routeError.value = route.query.error || '';
  console.log('Login page mounted:', {
    redirect: route.query.redirect,
    error: route.query.error
  });
});

async function handleLogin() {
  loading.value = true;
  error.value = '';
  
  try {
    console.log('Attempting login for:', form.username);
    const result = await login(form.username, form.password);
    
    if (result.success) {
      console.log('Login successful, redirecting...');
      
      // 获取重定向路径
      const redirectPath = route.query.redirect || '/';
      console.log('Redirecting to:', redirectPath);
      
      // 登录成功后跳转
      await router.push(redirectPath);
    } else {
      error.value = result.message || '登录失败';
    }
  } catch (e) {
    console.error('Login error:', e);
    error.value = e.message || '登录失败，请检查网络连接';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;

  height: 100%;
  background-image: url('@/assets/login-bg.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  padding: 20px;
  box-sizing: border-box;
}

.login-box {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 400px;
}

h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 28px;
  font-weight: 600;
}

.warning-message {
  background: #fff7e6;
  border: 1px solid #ffd591;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 20px;
  color: #d46b08;
  font-size: 14px;
  text-align: center;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #666;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

.form-group input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

button {
  width: 100%;
  padding: 14px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

button:hover:not(:disabled) {
  background: #66b1ff;
}

button:disabled {
  background: #a0cfff;
  cursor: not-allowed;
}

.error-message {
  color: #f56c6c;
  font-size: 14px;
  margin-bottom: 20px;
  text-align: center;
  background: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 6px;
  padding: 10px;
}

.links {
  margin-top: 24px;
  text-align: center;
  font-size: 14px;
}

.links a {
  color: #409eff;
  text-decoration: none;
  transition: color 0.3s;
}

.links a:hover {
  color: #66b1ff;
  text-decoration: underline;
}

.divider {
  margin: 0 12px;
  color: #ccc;
}

@media (max-width: 480px) {
  .auth-page {
    padding: 10px;
  }
  
  .login-box {
    padding: 30px 20px;
  }
}
</style>