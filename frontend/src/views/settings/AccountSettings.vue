<template>
  <div class="account-settings">
    <h3 class="section-title">账户信息</h3>
    <p class="section-desc">查看和修改您的账户信息</p>
    
    <el-form 
      label-position="top" 
      :model="userInfo" 
      ref="formRef"
      :rules="rules"
      class="settings-form"
    >
      <el-form-item label="用户名" prop="username">
        <el-input v-model="userInfo.username" disabled />
      </el-form-item>
      
      <el-form-item label="邮箱地址" prop="email">
        <el-input v-model="userInfo.email" />
      </el-form-item>
      
      <el-divider />
      
      <h3 class="section-title">修改密码</h3>
      <p class="section-desc">更新您的账户密码</p>
      
      <el-form-item label="当前密码" prop="currentPassword">
        <el-input v-model="passwords.currentPassword" type="password" show-password />
      </el-form-item>
      
      <el-form-item label="新密码" prop="newPassword">
        <el-input v-model="passwords.newPassword" type="password" show-password />
      </el-form-item>
      
      <el-form-item label="确认新密码" prop="confirmPassword">
        <el-input v-model="passwords.confirmPassword" type="password" show-password />
      </el-form-item>
      
      <el-divider />
      
      <el-form-item>
        <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
      </el-form-item>
      
      <el-divider />
      
      <h3 class="section-title danger">危险操作区</h3>
      <p class="section-desc">以下操作不可撤销，请谨慎操作</p>
      
      <div class="danger-zone">
        <el-button type="danger" plain @click="showDeleteAccountDialog">删除账户</el-button>
      </div>
    </el-form>
    
    <el-dialog
      title="确认删除账户"
      v-model="deleteDialogVisible"
      width="30%"
      :before-close="handleCloseDialog"
    >
      <div class="delete-account-dialog">
        <p>您确定要删除您的账户吗？此操作不可撤销，所有数据将被永久删除。</p>
        <el-form :model="deleteForm">
          <el-form-item label="请输入密码确认" prop="password">
            <el-input v-model="deleteForm.password" type="password" show-password />
          </el-form-item>
          <el-form-item label='请输入"DELETE"确认' prop="confirmation">
            <el-input v-model="deleteForm.confirmation" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteDialogVisible = false">取消</el-button>
          <el-button 
            type="danger" 
            @click="deleteAccount" 
            :disabled="!canDelete"
            :loading="deleting"
          >
            确认删除
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watchEffect } from 'vue';
import { useUserStore } from '../../store/user';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';

const userStore = useUserStore();
const router = useRouter();
const formRef = ref(null);
const saving = ref(false);
const deleting = ref(false);
const deleteDialogVisible = ref(false);

const userInfo = reactive({
  username: '',
  email: ''
});

const passwords = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
});

const deleteForm = reactive({
  password: '',
  confirmation: ''
});

// 验证两次输入的密码是否一致
const validatePass = (rule, value, callback) => {
  if (value !== passwords.newPassword) {
    callback(new Error('两次输入的密码不一致'));
  } else {
    callback();
  }
};

const rules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '长度在 6 到 20 个字符之间', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validatePass, trigger: 'blur' }
  ]
};

// 只有当密码输入正确且确认文本为DELETE时才能删除
const canDelete = computed(() => {
  return deleteForm.password && deleteForm.confirmation === 'DELETE';
});

// Populate user info from store when component mounts or user data changes
watchEffect(() => {
  if (userStore.user) {
    console.log('[AccountSettings] User data found in store:', userStore.user);
    userInfo.username = userStore.user.username || '';
    userInfo.email = userStore.user.email || '';
  } else {
    console.log('[AccountSettings] User data not yet available in store. User may not be logged in or data is still loading.');
    // Attempt to fetch if not available, though App.vue/router guards should handle initial load
    if (userStore.isLoggedIn && !userStore.user) {
        console.log('[AccountSettings] User is logged in but user object is missing, attempting to fetch user info.');
        userStore.fetchUserInfo().then(userData => {
            if (userData) {
                userInfo.username = userData.username || '';
                userInfo.email = userData.email || '';
            } else {
                ElMessage.error('无法加载用户信息，请尝试重新登录。');
                router.push('/login');
            }
        }).catch(err => {
            console.error('[AccountSettings] Error fetching user info in watchEffect:', err);
            ElMessage.error('加载用户信息时出错。');
        });
    } else if (!userStore.isLoggedIn) {
         console.log('[AccountSettings] User is not logged in. Clearing local user info.');
         userInfo.username = '';
         userInfo.email = '';
    }
  }
});

// 保存设置
const saveSettings = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    
    saving.value = true;
    try {
      // 检查是否需要更新密码
      const updatePassword = passwords.currentPassword && passwords.newPassword;
      
      // 实际应用中应该调用API
      // await userStore.api.put('/user/settings', {
      //   email: userInfo.email,
      //   update_password: updatePassword,
      //   current_password: passwords.currentPassword,
      //   new_password: passwords.newPassword
      // });
      
      ElMessage.success('保存成功');
      
      // 清空密码字段
      passwords.currentPassword = '';
      passwords.newPassword = '';
      passwords.confirmPassword = '';
    } catch (error) {
      console.error('保存设置失败:', error);
      ElMessage.error('保存失败，请稍后再试');
    } finally {
      saving.value = false;
    }
  });
};

// 显示删除账户对话框
const showDeleteAccountDialog = () => {
  ElMessageBox.confirm('删除账户将清除所有数据，此操作不可撤销。是否继续？', '警告', {
    confirmButtonText: '继续',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    deleteDialogVisible.value = true;
  }).catch(() => {});
};

// 关闭对话框
const handleCloseDialog = () => {
  deleteDialogVisible.value = false;
  deleteForm.password = '';
  deleteForm.confirmation = '';
};

// 删除账户
const deleteAccount = async () => {
  if (!canDelete.value) return;
  
  deleting.value = true;
  try {
    // 实际应用中应该调用API
    // await userStore.api.delete('/user/account', {
    //   data: { password: deleteForm.password }
    // });
    
    // 清除登录信息并返回登录页
    ElMessage.success('账户已删除');
    await userStore.logout();
    router.push('/login');
  } catch (error) {
    console.error('删除账户失败:', error);
    ElMessage.error('删除失败，请检查密码是否正确');
  } finally {
    deleting.value = false;
    deleteDialogVisible.value = false;
  }
};

onMounted(() => {
  // The watchEffect will run on mount and handle populating userInfo.
  // If userStore.user is already populated, it will use that.
  // If not, and user is logged in, it will try to fetch.
  console.log('[AccountSettings] Component mounted. Current user from store:', userStore.user);
  if (!userStore.user && userStore.isLoggedIn) {
      console.log("[AccountSettings] User data not immediately available on mount, but user is logged in. Relying on watchEffect or previous fetchUserInfo call.");
  } else if (!userStore.isLoggedIn) {
      ElMessage.info('请先登录以查看或修改账户设置。');
      // Redirect to login if not handled by router guards
      // router.push('/login'); 
  }
});
</script>

<style scoped>
.account-settings {
  width: 100%;
}

.section-title {
  margin: 0 0 10px;
  color: var(--text-primary);
  font-weight: 500;
}

.section-title.danger {
  color: #F56C6C;
}

.section-desc {
  margin: 0 0 20px;
  color: var(--text-secondary);
  font-size: 14px;
}

.settings-form {
  max-width: 600px;
}

.danger-zone {
  padding: 16px;
  background-color: #FFF0F0;
  border-radius: 4px;
  border-left: 4px solid #F56C6C;
}

.delete-account-dialog p {
  margin-bottom: 20px;
  color: var(--text-secondary);
}
</style> 