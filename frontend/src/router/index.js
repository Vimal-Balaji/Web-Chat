import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'login',
      component: () => import('../views/login.vue'),
      meta: { requiresAuth: false }  // Explicitly public
    },
    {
      path: '/signup',
      name: 'signup',
      component: () => import('../views/signup.vue'),
      meta: { requiresAuth: false }  // Explicitly public
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('../views/chat.vue'),
      meta: { requiresAuth: true }   // Requires authentication
    },
    {
      path: '/videoChat',
      name: 'videoChat',
      component: () => import('../views/videoChat.vue'),
      meta: { requiresAuth: true }   // Requires authentication
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
      meta: { requiresAuth: false }
    },
  ]
})

router.beforeEach(async (to, from, next) => {
  // Skip auth check for public routes
  if (!to.meta.requiresAuth) {
    return next();
  }

  try {
    // Call your backend to check if the user is logged in
    const response = await fetch('http://localhost:8000/check-auth', {  // Fixed URL
      method: 'GET',
      credentials: 'include' // Important! Sends HttpOnly cookies
    });

    if (response.ok) {
      const data = await response.json();
      if (data.authenticated) {
        // User is authenticated
        next();
      } else {
        // Not authenticated
        next({ name: 'login' });
      }
    } else {
      // Not authenticated
      next({ name: 'login' });
    }
  } catch (error) {
    console.error('Auth check failed:', error);
    next({ name: 'login' });
  }
});

export default router