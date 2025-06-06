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
            <el-avatar 
              :size="60" 
              :style="{ backgroundColor: getPersonalityIcon(personality).color }"
            >
              <el-icon><component :is="getPersonalityIcon(personality).icon" /></el-icon>
            </el-avatar>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useUserStore } from '../../store/user';
import { ElMessage } from 'element-plus';
import axios from 'axios';
import { Document, User, Avatar, ChatDotRound, StarFilled, Briefcase, Calendar } from '@element-plus/icons-vue';

const userStore = useUserStore();

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

// 根据助手信息获取图标
const getPersonalityIcon = (personality) => {
  if (!personality) return {
    icon: 'User',
    color: '#409EFF'
  };
  
  // 根据助手名称和类型返回对应图标
  switch(personality.name) {
    case '睿记': return {
      icon: 'Document',
      color: '#2E5E4E' // 深绿色，专业感
    };
    case '小暖': return {
      icon: 'ChatDotRound',
      color: '#F08C7A' // 温暖的珊瑚色
    };
    case '乐豆': return {
      icon: 'StarFilled',
      color: '#F7C242' // 活泼的黄色
    };
    case '简': return {
      icon: 'Briefcase',
      color: '#687C97' // 简约的蓝灰色
    };
    case '启航': return {
      icon: 'Calendar',
      color: '#6A8D73' // 积极的绿色
    };
    default:
      // 根据性格类型作为备选分类
      switch(personality.personality_type) {
        case '严谨高效型': return {
          icon: 'Document',
          color: '#2E5E4E'
        };
        case '温柔体贴型': return {
          icon: 'Avatar',
          color: '#F08C7A'
        };
        case '俏皮幽默型': return {
          icon: 'ChatDotRound',
          color: '#F7C242'
        };
        case '简洁利落型': return {
          icon: 'Briefcase',
          color: '#687C97'
        };
        case '鼓励打气型': return {
          icon: 'StarFilled',
          color: '#6A8D73'
        };
        default: return {
          icon: 'User',
          color: '#409EFF' // 默认蓝色
        };
      }
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


</style> 