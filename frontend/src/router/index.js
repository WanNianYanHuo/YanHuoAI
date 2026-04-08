import { createRouter, createWebHistory } from 'vue-router';
import { getToken, getUser } from '../api/auth';

const routes = [
  { 
    path: '/', 
    redirect: '/chat'
  },
  // { 
  //   path: '/login', 
  //   name: 'Login', 
  //   component: () => import('../views/Login.vue'), 
  //   meta: { title: '登录', guest: true } 
  // },
  // { 
  //   path: '/register', 
  //   name: 'Register', 
  //   component: () => import('../views/Register.vue'), 
  //   meta: { title: '注册', guest: true } 
  // },
  { 
    path: '/chat', 
    name: 'Chat', 
    component: () => import('../views/Chat.vue'), 
    meta: { title: '知识库问答', requiresAuth: true } 
  },
  { 
    path: '/manage', 
    name: 'KbManage', 
    component: () => import('../views/KbManage.vue'), 
    meta: { title: '知识库管理', requiresAuth: true } 
  },
  { 
    path: '/admin', 
    name: 'Admin', 
    component: () => import('../views/Admin.vue'), 
    meta: { title: '用户管理', requiresAuth: true, requiresAdmin: true } 
  },
  { 
    path: '/kb', 
    redirect: '/manage' 
  },
  // 管理员默认入口
  {
    path: '/admin-home',
    redirect: '/manage',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 检查token是否有效（简单检查格式和过期时间）
function isTokenValid(token) {
  if (!token) return false;
  
  try {
    // 如果token是JWT格式，可以检查过期时间
    const payload = JSON.parse(atob(token.split('.')[1]));
    const now = Date.now() / 1000;
    return payload.exp > now;
  } catch (e) {
    // 如果不是JWT格式，只要存在就认为有效
    return true;
  }
}

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = getToken();
  const user = getUser();
  const isValidToken = isTokenValid(token);
  
  console.log('Route guard:', {
    to: to.name,
    hasToken: !!token,
    isValidToken,
    user: user?.username,
    requiresAuth: to.meta.requiresAuth,
    requiresAdmin: to.meta.requiresAdmin,
    guest: to.meta.guest
  });
  
  // 如果token无效，清除本地存储
  if (token && !isValidToken) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  // 根路径根据角色重定向（管理员→管理页，普通用户→问答页）
  if (to.path === '/') {
    if (token && isValidToken && user?.role === 'admin') {
      next('/manage');
      return;
    }
    next('/chat');
    return;
  }
  
  // 检查是否需要登录
  if (to.meta.requiresAuth) {
    if (!token || !isValidToken) {
      console.log('Not logged in, but proceeding to route.');
      // 不再重定向到登录页
      // next({
      //   path: '/login',
      //   query: { redirect: to.fullPath } // 保存原始路径，登录后跳转
      // });
      // return;
    }
  }
  
  // 检查是否需要管理员权限
  if (to.meta.requiresAdmin) {
    if (!token || !isValidToken || !user || user.role !== 'admin') {
      console.log('Redirecting to chat: admin required');
      next({
        path: '/chat',
        query: { redirect: to.fullPath, error: 'admin_required' }
      });
      return;
    }
  }

  // 管理员账号不允许进入问答页
  if (to.name === 'Chat' && token && isValidToken && user?.role === 'admin') {
    next({ path: '/manage' });
    return;
  }
  
  // 检查是否是访客页面（已登录用户不应该访问登录/注册页）
  if (to.meta.guest) {
    if (token && isValidToken) {
      console.log('Redirecting to home: already logged in');
      // 如果有重定向参数，跳转到重定向页面，否则跳转到首页
      const redirect = to.query.redirect || from.query.redirect || '/';
      next(redirect);
      return;
    }
  }
  
  next();
});

// 路由后置守卫：设置页面标题
router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - 中医目诊问答系统` : '中医目诊问答系统';
});

export default router;
