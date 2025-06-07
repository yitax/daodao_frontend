<template>
  <div class="auth-container">
    <div class="auth-box">
      <div class="auth-header">
        <h1 class="auth-title">叨叨记账</h1>
        <p class="auth-subtitle">AI智能记账助手</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="auth-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            prefix-icon="User"
            clearable
            class="auth-input"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
            class="auth-input"
          />
        </el-form-item>

        <div class="auth-options">
          <el-checkbox v-model="rememberMe" class="auth-checkbox">记住我</el-checkbox>
          <router-link to="/register" class="auth-link">注册账号</router-link>
        </div>

        <el-button
          type="primary"
          :loading="loading"
          class="auth-button"
          @click="handleLogin"
        >
          登录
        </el-button>
      </el-form>

      <div class="auth-footer">
        <p>© {{ new Date().getFullYear() }} 叨叨记账 - 更轻松的记账方式</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useUserStore } from "../store/user";
import { User, Lock } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import '../assets/owl-theme.css';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const loading = ref(false);
const rememberMe = ref(false);

const loginForm = reactive({
  username: "",
  password: "",
});

const loginRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const loginFormRef = ref(null);

const handleLogin = async () => {
  if (!loginFormRef.value) return;

  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return;

    loading.value = true;
    try {
      const success = await userStore.login(
        loginForm.username,
        loginForm.password,
        rememberMe.value
      );

      if (success) {
        ElMessage.success("登录成功");

        // 如果有重定向地址，则导航到该地址
        const redirect = route.query.redirect || "/chat";
        router.replace(redirect);
      } else {
        ElMessage.error("用户名或密码错误");
      }
    } catch (error) {
      console.error("登录出错:", error);
      ElMessage.error("登录失败，请稍后再试");
    } finally {
      loading.value = false;
    }
  });
};

onMounted(() => {
  // 如果已经登录，直接跳转到首页
  if (userStore.isLoggedIn) {
    router.replace("/chat");
  }
});
</script>

<style>
/* 自定义 Element Plus 组件样式 */
:deep(.el-input__wrapper) {
  background-color: var(--owl-neutral-light) !important;
  border: 1px solid var(--owl-border) !important;
  border-radius: 6px !important;
  box-shadow: none !important;
  transition: all var(--owl-transition) !important;
}

:deep(.el-input__wrapper.is-focus) {
  background-color: white !important;
  border-color: var(--owl-primary) !important;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
}

:deep(.el-input__prefix-inner) {
  color: var(--owl-primary);
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: var(--owl-primary);
  border-color: var(--owl-primary);
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, var(--owl-green-2), var(--owl-primary));
  border: none;
  height: 48px;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  transition: all var(--owl-transition);
}

:deep(.el-button--primary:hover) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
  background: linear-gradient(135deg, var(--owl-green-2), var(--owl-green-3));
}
</style> 