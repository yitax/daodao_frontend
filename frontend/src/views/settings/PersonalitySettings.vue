<template>
  <div class="personality-settings">
    <h3 class="section-title">选择AI助手个性</h3>
    <p class="section-desc">选择适合您的AI助手个性，让记账更有趣</p>
    
    <el-row :gutter="20" class="personality-list">
      <el-col :xs="24" :sm="12" :md="8" v-for="personality in personalities" :key="personality.id">
        <el-card 
          :class="['personality-card', { active: personality.id === currentPersonalityId }]" 
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
              v-if="personality.id !== currentPersonalityId" 
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
import { computed, onMounted } from 'vue';
import { useUserStore } from '../../store/user';
import { ElMessage } from 'element-plus';
import { Document, User, Avatar, ChatDotRound, StarFilled, Briefcase, Calendar } from '@element-plus/icons-vue';

const userStore = useUserStore();

// 从 store 获取数据
const personalities = computed(() => userStore.personalities);
const currentPersonalityId = computed(() => userStore.currentPersonalityId);

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
  if (id === currentPersonalityId.value) return;
  try {
    await userStore.updateUserSettings({ personality_id: id });
    ElMessage.success('AI助手已更新');
  } catch (error) {
    console.error('设置AI助手失败:', error);
    ElMessage.error(error.message || '设置失败，请稍后再试');
  }
};

onMounted(() => {
  // 如果store中没有助手列表，则主动获取
  if (personalities.value.length === 0) {
    userStore.fetchPersonalities();
  }
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
  align-items: center;
  min-height: 32px; /* 确保高度一致 */
}
</style> 