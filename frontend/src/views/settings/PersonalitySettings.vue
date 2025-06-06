<template>
  <div class="personality-settings">
    <h3 class="section-title">选择AI助手个性</h3>
    <p class="section-desc">选择适合您的AI助手个性，让记账更有趣</p>
    
    <el-row :gutter="20" class="personality-list">
      <el-col :xs="24" :sm="12" :md="8" v-for="personality in personalities" :key="personality.id">
        <el-card 
          :class="['personality-card', { active: personality.id === currentPersonality }]" 
          @click="selectPersonality(personality.id)"
        >
          <div class="personality-icon">
            <el-avatar :size="60" :icon="getPersonalityIcon(personality)" />
          </div>
          <div class="personality-info">
            <h4>{{ personality.name }}</h4>
            <p>{{ personality.description }}</p>
            <div class="personality-type">{{ personality.personality_type }}</div>
          </div>
          <div class="personality-select">
            <el-button 
              v-if="personality.id !== currentPersonality" 
              size="small"
              @click.stop="selectPersonality(personality.id)"
            >
              选择
            </el-button>
            <el-tag v-else type="success">当前选择</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <div class="settings-form">
      <h3 class="section-title">自定义AI助手性格</h3>
      <p class="section-desc">创建您自己的AI助手性格（需要高级会员）</p>
      
      <el-form label-position="top" :model="customPersonality" ref="formRef">
        <el-form-item label="个性名称" prop="name">
          <el-input v-model="customPersonality.name" placeholder="给您的AI助手起个名字" disabled />
        </el-form-item>
        <el-form-item label="个性描述" prop="description">
          <el-input 
            v-model="customPersonality.description" 
            type="textarea" 
            rows="3" 
            placeholder="描述AI助手的性格特点"
            disabled
          />
        </el-form-item>
        <el-form-item label="交流风格" prop="style">
          <el-select v-model="customPersonality.style" placeholder="选择交流风格" style="width: 100%" disabled>
            <el-option label="正式" value="formal" />
            <el-option label="友好" value="friendly" />
            <el-option label="幽默" value="humorous" />
            <el-option label="简洁" value="concise" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-tooltip content="需要高级会员才能创建自定义助手" placement="top">
            <el-button type="primary" disabled>升级会员解锁</el-button>
          </el-tooltip>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useUserStore } from '../../store/user';
import { ElMessage } from 'element-plus';
import axios from 'axios';

const userStore = useUserStore();
const formRef = ref(null);

// 创建axios实例用于API请求
const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// 添加请求拦截器用于Token管理
axiosInstance.interceptors.request.use(config => {
  // 从存储获取token
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

// 助手数据
const personalities = ref([]);
const currentPersonality = ref(null);
const customPersonality = reactive({
  name: '',
  description: '',
  style: 'friendly'
});

// 根据助手信息获取图标
const getPersonalityIcon = (personality) => {
  switch(personality.personality_type) {
    case '严谨高效型': return 'Document';
    case '温柔体贴型': return 'Avatar';
    case '俏皮幽默型': return 'ChatDotRound';
    case '简洁利落型': return 'Briefcase';
    case '鼓励打气型': return 'StarFilled';
    default: return 'User';
  }
};

// 选择性格
const selectPersonality = async (id) => {
  try {
    // 调用API更新用户的助手选择
    await axiosInstance.post('/users/settings/personality', { personality_id: id });
    currentPersonality.value = id;
    ElMessage.success('AI助手已更新');
  } catch (error) {
    console.error('设置AI助手失败:', error);
    ElMessage.error('设置失败，请稍后再试');
  }
};

// 获取用户当前AI助手设置
const fetchPersonalitySettings = async () => {
  try {
    console.log('获取AI助手列表...');
    const response = await axiosInstance.get('/chat/personalities');
    console.log('获取到AI助手列表:', response.data);
    
    if (response.data.length > 0) {
      personalities.value = response.data;
      
      // 获取用户当前选择的助手
      try {
        const userSettings = await axiosInstance.get('/users/settings');
        currentPersonality.value = userSettings.data.personality_id || 1;
      } catch (error) {
        console.error('获取用户设置失败，使用默认助手:', error);
        currentPersonality.value = 1; // 默认使用第一个助手
      }
    } else {
      ElMessage.warning('获取助手列表失败，请刷新页面重试');
    }
  } catch (error) {
    console.error('获取AI助手列表失败:', error);
    ElMessage.error('获取助手列表失败，请稍后再试');
  }
};

onMounted(() => {
  fetchPersonalitySettings();
});
</script>

<style scoped>
.personality-settings {
  width: 100%;
}

.section-title {
  margin: 0 0 10px;
  color: var(--text-primary);
  font-weight: 500;
}

.section-desc {
  margin: 0 0 20px;
  color: var(--text-secondary);
  font-size: 14px;
}

.personality-list {
  margin-bottom: 30px;
}

.personality-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.3s ease;
  margin-bottom: 20px;
}

.personality-card:hover {
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.personality-card.active {
  border-color: var(--primary-color);
  box-shadow: 0 0 10px rgba(64, 158, 255, 0.2);
}

.personality-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 15px;
}

.personality-info {
  flex-grow: 1;
  text-align: center;
}

.personality-info h4 {
  margin: 0 0 10px;
  color: var(--text-primary);
}

.personality-info p {
  margin: 0 0 10px;
  color: var(--text-secondary);
  font-size: 14px;
}

.personality-type {
  font-size: 12px;
  color: #5DAF8E;
  margin-bottom: 10px;
  font-weight: 500;
}

.personality-select {
  margin-top: 15px;
  display: flex;
  justify-content: center;
}

.settings-form {
  margin-top: 30px;
  max-width: 600px;
  opacity: 0.8; /* 降低自定义表单的透明度，表示未启用 */
}
</style> 