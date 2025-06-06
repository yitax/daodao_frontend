<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1 class="app-title">叨叨账本</h1>
        <p class="app-desc">AI智能记账助手</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <div class="login-options">
          <el-checkbox v-model="rememberMe">记住我</el-checkbox>
          <router-link to="/register" class="register-link"
            >注册账号</router-link
          >
        </div>

        <el-button
          type="primary"
          :loading="loading"
          class="login-button"
          @click="handleLogin"
        >
          登录
        </el-button>
      </el-form>

      <div class="login-footer">
        <p>© {{ new Date().getFullYear() }} 叨叨账本 - 更轻松的记账方式</p>
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

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: var(--background-color);
}

.login-box {
  width: 360px;
  padding: 30px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.app-title {
  font-size: 28px;
  color: var(--primary-color);
  margin-bottom: 10px;
}

.app-desc {
  color: var(--text-secondary);
  font-size: 16px;
}

.login-form {
  margin-bottom: 20px;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.register-link {
  color: var(--primary-color);
  text-decoration: none;
}

.register-link:hover {
  text-decoration: underline;
}

.login-button {
  width: 100%;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  color: var(--text-secondary);
  font-size: 12px;
}
</style> 