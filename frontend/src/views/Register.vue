<template>
  <div class="auth-container">
    <div class="auth-box">
      <div class="auth-header">
        <h1 class="auth-title">注册账号</h1>
        <p class="auth-subtitle">加入叨叨账本，让理财更轻松</p>
      </div>

      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        class="auth-form"
        @submit.prevent="handleRegister"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="用户名"
            prefix-icon="User"
            clearable
            class="auth-input"
          />
        </el-form-item>

        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="邮箱"
            prefix-icon="Message"
            clearable
            class="auth-input"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
            class="auth-input"
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            placeholder="确认密码"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleRegister"
            class="auth-input"
          />
        </el-form-item>

        <div class="auth-options">
          <router-link to="/login" class="auth-link">已有账号？去登录</router-link>
        </div>

        <el-button
          type="primary"
          :loading="loading"
          class="auth-button"
          @click="handleRegister"
        >
          注册
        </el-button>
      </el-form>

      <div class="auth-footer">
        <p>© {{ new Date().getFullYear() }} 叨叨账本 - 更轻松的记账方式</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "../store/user";
import { User, Lock, Message } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import '../assets/owl-theme.css';

const router = useRouter();
const userStore = useUserStore();
const loading = ref(false);
const registerFormRef = ref(null);

const registerForm = reactive({
  username: "",
  email: "",
  password: "",
  confirmPassword: ""
});

// 验证两次输入的密码是否一致
const validatePass = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'));
  } else {
    callback();
  }
};

const registerRules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, max: 20, message: "长度在 3 到 20 个字符之间", trigger: "blur" }
  ],
  email: [
    { required: true, message: "请输入邮箱地址", trigger: "blur" },
    { type: "email", message: "请输入正确的邮箱地址", trigger: "blur" }
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, max: 20, message: "长度在 6 到 20 个字符之间", trigger: "blur" }
  ],
  confirmPassword: [
    { required: true, message: "请再次输入密码", trigger: "blur" },
    { validator: validatePass, trigger: "blur" }
  ]
};

const handleRegister = async () => {
  if (!registerFormRef.value) return;

  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return;

    loading.value = true;
    try {
      const success = await userStore.register(
        registerForm.username,
        registerForm.email,
        registerForm.password
      );

      if (success) {
        ElMessage.success("注册成功，请登录");
        router.push("/login");
      }
    } catch (error) {
      console.error("注册出错:", error);
      ElMessage.error("注册失败，请稍后再试");
    } finally {
      loading.value = false;
    }
  });
};
</script>

<style>
/* 注册页面特有样式 */
.auth-box {
  max-width: 450px;
}

/* 自定义错误提示样式 */
:deep(.el-form-item.is-error .el-input__wrapper) {
  border-color: #F56C6C !important;
}

:deep(.el-form-item__error) {
  color: #F56C6C;
}
</style> 