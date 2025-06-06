<template>
  <div class="chat-page">
    <div class="chat-header">
      <div class="personality-selector">
        <el-dropdown @command="changePersonality">
          <span class="personality-display">
            <el-avatar :size="20" :icon="getPersonalityIcon(currentPersonality)" class="personality-avatar" />
            {{ currentPersonality.name }}
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="personality in personalities"
                :key="personality.id"
                :command="personality.id"
              >
                <div class="dropdown-personality-item">
                  <el-avatar :size="20" :icon="getPersonalityIcon(personality)" />
                  <span>{{ personality.name }}</span>
                  <span class="personality-type">{{ personality.personality_type }}</span>
                </div>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-chat">
        <el-empty description="来和叨叨聊天吧！">
          <template #image>
            <img
              src="../assets/chat-empty.svg"
              class="empty-image"
              alt="开始聊天"
            />
          </template>
          <div class="quick-starts">
            <el-button
              v-for="(hint, index) in quickHints"
              :key="index"
              size="small"
              @click="sendQuickMessage(hint)"
            >
              {{ hint }}
            </el-button>
          </div>
        </el-empty>
      </div>

      <template v-else>
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="message-group"
        >
          <div
            :class="['message', msg.is_user ? 'user-message' : 'ai-message']"
          >
            <div class="message-avatar">
              <el-avatar
                :icon="msg.is_user ? User : getPersonalityIcon(currentPersonality)"
                :size="40"
              />
            </div>
            <div class="message-content">
              <div class="message-bubble">
                {{ msg.content }}
              </div>
              <div class="message-time">
                {{ formatTime(msg.created_at) }}
              </div>
            </div>
          </div>

          <!-- 显示交易确认框 -->
          <div
            v-if="msg.id === pendingTransactionMessageId && showConfirmation"
            class="transaction-confirmation"
          >
            <div class="confirmation-header">
              <el-icon><InfoFilled /></el-icon>
              <span>请确认交易信息</span>
            </div>
            <div class="confirmation-content">
              <el-form
                label-position="left"
                :model="extractedInfo"
                label-width="80px"
              >
                <el-form-item label="交易类型">
                  <el-select v-model="extractedInfo.type" style="width: 100%">
                    <el-option label="收入" value="income" />
                    <el-option label="支出" value="expense" />
                  </el-select>
                </el-form-item>
                <el-form-item label="金额">
                  <el-input-number
                    v-model="extractedInfo.amount"
                    :min="0"
                    :precision="2"
                    style="width: 100%"
                  />
                </el-form-item>
                <el-form-item label="日期">
                  <el-date-picker
                    v-model="extractedInfo.date"
                    type="date"
                    style="width: 100%"
                    value-format="YYYY-MM-DD"
                  />
                </el-form-item>
                <el-form-item label="描述">
                  <el-input v-model="extractedInfo.description" />
                </el-form-item>
                <el-form-item label="分类">
                  <el-select
                    v-model="extractedInfo.category"
                    style="width: 100%"
                  >
                    <el-option label="餐饮美食" value="餐饮美食" />
                    <el-option label="交通出行" value="交通出行" />
                    <el-option label="服饰美容" value="服饰美容" />
                    <el-option label="日用百货" value="日用百货" />
                    <el-option label="住房物业" value="住房物业" />
                    <el-option label="医疗健康" value="医疗健康" />
                    <el-option label="文教娱乐" value="文教娱乐" />
                    <el-option label="人情往来" value="人情往来" />
                    <el-option label="工资薪酬" value="工资薪酬" />
                    <el-option label="投资理财" value="投资理财" />
                    <el-option label="其他收入" value="其他收入" />
                    <el-option label="其他支出" value="其他支出" />
                    <el-option label="未分类" value="未分类" />
                  </el-select>
                </el-form-item>
              </el-form>
            </div>
            <div class="confirmation-actions">
              <el-button @click="cancelTransaction">取消</el-button>
              <el-button type="primary" @click="confirmTransaction"
                >确认记账</el-button
              >
            </div>
          </div>

          <!-- 已确认的交易记录卡片 -->
          <div v-if="msg.confirmedTransaction" class="confirmed-transaction">
            <div class="transaction-card">
              <div class="transaction-card-header">
                <el-icon><Check /></el-icon>
                <span>交易记录已保存</span>
              </div>
              <div class="transaction-card-content">
                <div class="transaction-type">
                  <el-tag
                    :type="
                      msg.confirmedTransaction.type === 'income'
                        ? 'success'
                        : 'danger'
                    "
                  >
                    {{
                      msg.confirmedTransaction.type === "income"
                        ? "收入"
                        : "支出"
                    }}
                  </el-tag>
                </div>
                <div class="transaction-amount">
                  {{ msg.confirmedTransaction.amount }} 元
                </div>
                <div class="transaction-details">
                  <div class="transaction-date">
                    <el-icon><Calendar /></el-icon>
                    {{ msg.confirmedTransaction.date }}
                  </div>
                  <div class="transaction-category">
                    <el-icon><Collection /></el-icon>
                    {{ msg.confirmedTransaction.category }}
                  </div>
                </div>
                <div class="transaction-description">
                  {{ msg.confirmedTransaction.description }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <div v-if="isTyping" class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>

    <div class="chat-input-container">
      <el-input
        v-model="inputMessage"
        placeholder="输入消息..."
        :disabled="loading"
        @keyup.enter="sendMessage"
        clearable
      >
        <template #append>
          <el-button :loading="loading" @click="sendMessage">
            <el-icon><Message /></el-icon>
          </el-button>
        </template>
      </el-input>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick, computed } from "vue";
import { useUserStore } from "../store/user";
import {
  ArrowDown,
  User,
  ChatDotRound,
  Message,
  InfoFilled,
  Check,
  Calendar,
  Collection,
  Document,
  Briefcase,
  StarFilled,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import axios from "axios";

const userStore = useUserStore();

// Use the API instance from userStore
const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Add request interceptor for token management
axiosInstance.interceptors.request.use(config => {
  // Get token from storage
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

const messagesContainer = ref(null);
const inputMessage = ref("");
const messages = ref([]);
const loading = ref(false);
const isTyping = ref(false);
const showConfirmation = ref(false);
const pendingTransactionMessageId = ref(null);
const extractedInfo = reactive({
  type: "expense",
  amount: null,
  date: new Date().toISOString().split("T")[0],
  description: "",
  category: "未分类",
});

// AI助手数据
const personalities = ref([]);
const currentPersonalityId = ref(1);
const currentPersonality = computed(() => {
  return (
    personalities.value.find((p) => p.id === currentPersonalityId.value) ||
    { id: 1, name: '默认助手', personality_type: '默认类型' }
  );
});

// 根据助手信息获取图标
const getPersonalityIcon = (personality) => {
  if (!personality) return 'User';
  
  switch(personality.personality_type) {
    case '严谨高效型': return Document;
    case '温柔体贴型': return ChatDotRound;
    case '俏皮幽默型': return StarFilled;
    case '简洁利落型': return Briefcase;
    case '鼓励打气型': return Calendar;
    default: return User;
  }
};

// 快速提示信息
const quickHints = ref([
  "我今天午饭花了25元",
  "收到工资5000元",
  "查询上周支出",
  "帮我设置一个提醒，明天带文件",
]);

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return "";
  
  const date = new Date(timestamp);
  
  // 检查时间戳是否可能是服务器返回的UTC时间（8小时差异）
  // 如果时间与当前时间相差超过6小时，且小于当前时间，可能是时区问题
  const now = new Date();
  const hoursDiff = (now - date) / (1000 * 60 * 60);
  
  // 如果是从后端返回的消息时间（通常时间较早，相差接近8小时），进行时区校正
  if (hoursDiff > 6 && hoursDiff < 12) {
    // 服务器返回的时间可能是UTC，需要加上8小时转换为中国时间
    date.setHours(date.getHours() + 8);
  }
  
  // 使用本地时区格式化时间
  return date.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false // 使用24小时制
  });
};

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() && !loading.value) return;

  const userMessageContent = inputMessage.value.trim();
  const userMessage = {
    id: Date.now(), // Unique ID for the user message
    content: userMessageContent,
    is_user: true,
    created_at: new Date().toISOString(),
  };
  messages.value.push(userMessage);
  const userInput = inputMessage.value; // Store before clearing
  inputMessage.value = "";
  scrollToBottom();

  loading.value = true;
  isTyping.value = true;

  console.log("[Chat] 发送消息给后端:", { message: userInput, personality_id: currentPersonalityId.value });

  try {
    const payload = {
      content: userInput, // 修改字段名为 content
      personality_id: typeof currentPersonalityId.value === 'number' ? currentPersonalityId.value : null // 确保发送的是数字或null
    };
    console.log("[Chat] 构造的请求体 (payload):", payload);

    const response = await axiosInstance.post("/chat/", payload);

    isTyping.value = false;
    // Deep clone response.data for logging to avoid issues with Proxy objects
    console.log("[Chat] 从后端收到的原始回复 (response.data):", JSON.parse(JSON.stringify(response.data)));

    if (response && response.data && response.data.message) { // Ensure response.data.message exists
      const aiReplyFullMessage = response.data.message; // This is the MessageResponse object
      const extractedTransactionInfo = response.data.extracted_info;
      const needsConfirmation = response.data.needs_confirmation || false;

      console.log("[Chat] 从后端收到的回复详情:", {
        "AI消息ID": aiReplyFullMessage.id,
        "AI回复内容": aiReplyFullMessage.content ? aiReplyFullMessage.content.substring(0, 50) + "..." : "无内容",
        "提取的交易信息": extractedTransactionInfo,
        "需要确认": needsConfirmation
      });

      let aiMessageContent = aiReplyFullMessage.content || "抱歉，AI未能提供有效的文本回复。";
      if (!aiReplyFullMessage.content) {
          console.warn("[Chat] AI回复的 message 对象中未找到 'content' 文本字段, aiReplyFullMessage:", JSON.parse(JSON.stringify(aiReplyFullMessage)));
      }
      
      console.log("[Chat] 解析后的AI文本回复内容:", aiMessageContent);

      // 保存用户消息ID，用于后续确认交易
      const userMessageId = userMessage.id; // 前端生成的临时ID
      const backendUserMessageId = aiReplyFullMessage.user_id; // 后端用户ID
      console.log("[Chat] 用户消息ID - 前端临时:", userMessageId, "后端用户ID:", backendUserMessageId);

      const aiMsgId = aiReplyFullMessage.id || Date.now() + 1; 
    const aiMessage = {
        id: aiMsgId,
        content: aiMessageContent,
      is_user: false,
        created_at: aiReplyFullMessage.created_at || new Date().toISOString(),
        transaction_details: extractedTransactionInfo || null, 
        confirmedTransaction: null, 
        related_user_message_id: userMessageId, // 存储关联的用户消息ID
    };

    messages.value.push(aiMessage);
      scrollToBottom();
      console.log("[Chat] AI消息已推送到messages数组:", JSON.parse(JSON.stringify(aiMessage)));

      // 检查是否需要显示确认框
      if (needsConfirmation && extractedTransactionInfo) {
        console.log("[Chat] 后端指示需要确认交易，交易详情:", JSON.parse(JSON.stringify(extractedTransactionInfo)));
        
        // 确保金额是数字
        const amount = parseFloat(extractedTransactionInfo.amount);
        if (!isNaN(amount)) {
          Object.assign(extractedInfo, {
            type: extractedTransactionInfo.type || "expense",
            amount: amount,
            date: extractedTransactionInfo.date || new Date().toISOString().split("T")[0],
            description: extractedTransactionInfo.description || "",
            category: extractedTransactionInfo.category || "未分类",
          });

          pendingTransactionMessageId.value = aiMsgId;
      showConfirmation.value = true;
          console.log("[Chat] 交易确认框已设置为显示, extractedInfo:", JSON.parse(JSON.stringify(extractedInfo)));
        } else {
          console.error("[Chat] 交易金额无效:", extractedTransactionInfo.amount);
          showConfirmation.value = false;
        }
    } else {
        console.log("[Chat] 不需要确认交易. needsConfirmation:", needsConfirmation, "extractedTransactionInfo:", extractedTransactionInfo);
        showConfirmation.value = false;
      }
    } else {
      console.error("后端响应为空或无效", response);
      messages.value.push({
        id: Date.now() + 1,
        content: "抱歉，AI服务暂时没有返回有效信息，请稍后再试。",
        is_user: false,
        created_at: new Date().toISOString(),
      });
      scrollToBottom();
    }
  } catch (error) {
    isTyping.value = false;
    console.error("发送消息或处理回复时出错:", error);
    ElMessage.error(
      `消息处理失败: ${
        error.response?.data?.detail || error.message || "网络错误"
      }`
    );
    messages.value.push({
      id: Date.now() + 1,
      content: "抱歉，与服务器通信或处理回复时发生错误。",
      is_user: false,
      created_at: new Date().toISOString(),
    });
    scrollToBottom();
  } finally {
    loading.value = false;
  }
};

// 发送快速提示消息
const sendQuickMessage = (hint) => {
  inputMessage.value = hint;
  sendMessage();
};

// 确认交易
const confirmTransaction = async () => {
  if (!pendingTransactionMessageId.value) {
    console.warn("[Chat] confirmTransaction called without pendingTransactionMessageId.");
    return;
  }

  // 找到AI消息
  const aiMessageIndex = messages.value.findIndex(
    (msg) => msg.id === pendingTransactionMessageId.value
  );
  
  if (aiMessageIndex === -1) {
    console.error("[Chat] 确认交易时：无法在messages数组中找到ID为", pendingTransactionMessageId.value, "的AI消息");
    showConfirmation.value = false; 
    pendingTransactionMessageId.value = null;
    return;
  }
  
  const aiMessage = messages.value[aiMessageIndex];
  
  try {
    // 确保所有数据都正确格式化
    console.log("[Chat] 提交前检查交易数据...");
    
    // 1. 使用小写类型，和后端中枚举定义的值匹配 
    let type = extractedInfo.type.toLowerCase();
    
    if (type !== 'income' && type !== 'expense') {
      throw new Error(`无效的交易类型: ${extractedInfo.type}`);
    }
    
    console.log(`[Chat] 使用交易类型(小写): ${type}`);
    
    // 2. 确保金额是有效数值并且大于0
    const amount = Number(extractedInfo.amount);
    if (isNaN(amount) || amount <= 0) {
      throw new Error(`无效的交易金额: ${extractedInfo.amount}`);
    }
    
    // 3. 确保日期格式正确(YYYY-MM-DD)
    let formattedDate = extractedInfo.date;
    if (!formattedDate) {
      formattedDate = new Date().toISOString().split('T')[0];
    }
    // 验证日期格式
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(formattedDate)) {
      formattedDate = new Date(formattedDate).toISOString().split('T')[0];
    }
    
    // 4. 确保描述不为空
    const description = extractedInfo.description || "未填写描述";
    
    // 5. 确保分类不为空
    const category = extractedInfo.category || "未分类";
    
    // 打印详细日志
    console.log("[Chat] 准备提交的交易数据详情:", {
      类型: type,
      金额: amount,
      日期: formattedDate,
      描述: description,
      分类: category
    });
    
    // 直接使用提取的交易信息，确保格式正确
    const transactionPayload = {
      confirm: true,
      type: type,  // 使用小写值
      amount: amount,
      description: description,
      category: category,
      date: formattedDate,
      message_id: -1  // 使用-1表示一个不需要依赖数据库查询的特殊ID
    };

    console.log("[Chat] 发送给 /chat/confirm-transaction 的 payload:", transactionPayload);

    // Call the correct backend endpoint for confirming chat-extracted transactions
    const response = await axiosInstance.post("/chat/confirm-transaction", transactionPayload);
    console.log("[Chat] /chat/confirm-transaction API响应状态:", response.status, "数据:", response.data);

    if (response.data && response.data.confirmed === true && response.data.transaction) {
      ElMessage.success("交易已成功记录！");
      
      const confirmedTxDetailsFromBackend = response.data.transaction;
      
      // Update the original AI message that presented the transaction to show it as confirmed.
      // The template should have logic to display msg.confirmedTransaction.
      if (messages.value[aiMessageIndex]) {
         messages.value[aiMessageIndex].confirmedTransaction = {
            type: confirmedTxDetailsFromBackend.type,
            amount: confirmedTxDetailsFromBackend.amount,
            date: confirmedTxDetailsFromBackend.date,
            description: confirmedTxDetailsFromBackend.description,
            category: confirmedTxDetailsFromBackend.category,
            // id: confirmedTxDetailsFromBackend.id // if backend sends transaction id in this sub-object
         };
         messages.value[aiMessageIndex].transaction_details = null; // Clear pending details
         // Optionally, update the AI message content itself if needed
         // messages.value[aiMessageIndex].content = "交易已确认，记录如下："; 
    } else {
          console.error("[Chat] AI Message at index", aiMessageIndex, "was unexpectedly undefined during transaction confirmation.");
    }

    showConfirmation.value = false;
    pendingTransactionMessageId.value = null;

      // Optionally, add a new, separate AI confirmation message from the bot
      // This might be redundant if the original message is updated clearly.
      // messages.value.push({
      //   id: Date.now(),
      //   content: `好的，已为您记录一笔${confirmedTxDetailsFromBackend.type === 'income' ? '收入' : '支出'}：${confirmedTxDetailsFromBackend.description}，金额 ${confirmedTxDetailsFromBackend.amount}元。详情请在总账单中查看。`,
      //   is_user: false,
      //   created_at: new Date().toISOString(),
      // });
      // scrollToBottom();

      console.log("[Chat] 交易已确认并更新UI. Messages:", JSON.parse(JSON.stringify(messages.value)));
    } else {
      ElMessage.error(response.data.message || "记录交易失败，请稍后再试。服务端返回状态: " + response.status);
      console.error("[Chat] 记录交易失败, 服务端响应:", response.data);
    }
  } catch (error) {
    console.error("[Chat] 确认交易时出错:", error.response || error.message || error);
    ElMessage.error(
      `记录交易失败: ${ (error.response?.data?.detail || error.message || "网络错误")}`
    );
  } finally {
    // Ensure these are reset IF they were not reset by success path already
    if (showConfirmation.value) showConfirmation.value = false;
    if (pendingTransactionMessageId.value) pendingTransactionMessageId.value = null;
  }
};

// 取消交易
const cancelTransaction = () => {
  showConfirmation.value = false;
  pendingTransactionMessageId.value = null;
  ElMessage.info("交易已取消。");
  console.log("交易已取消");
  
  messages.value.push({
    id: Date.now(),
    content: "好的，已取消当前交易记录操作。",
    is_user: false,
    created_at: new Date().toISOString(),
  });
  scrollToBottom();
};

// 切换AI性格
const changePersonality = (id) => {
  currentPersonalityId.value = id;
  const selectedPersonality = personalities.value.find(p => p.id === id);
  ElMessage.success(`助手已切换为: ${selectedPersonality ? selectedPersonality.name : '默认助手'}`);
    messages.value.push({
    id: Date.now(),
    content: `我已经切换为${selectedPersonality ? selectedPersonality.name : '默认助手'}，有什么可以帮您？`,
      is_user: false,
      created_at: new Date().toISOString(),
    });
    scrollToBottom();
  console.log("助手已切换为:", currentPersonalityId.value);
};

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
  });
};

// 获取聊天历史
const fetchChatHistory = async () => {
  try {
    console.log("获取聊天历史...");
    const response = await axiosInstance.get("/chat/history");
    console.log("获取到聊天历史:", response.data.length, "条消息");
    // 为每个消息添加confirmedTransaction字段，确保兼容新结构
    messages.value = response.data.map((msg) => ({
      ...msg,
      confirmedTransaction: null,
    }));
    scrollToBottom();
  } catch (error) {
    console.error("获取聊天历史失败:", error);
    if (error.response) {
      console.error("响应状态:", error.response.status);
      console.error("响应数据:", error.response.data);
    }
  }
};

// 获取AI性格列表
const fetchPersonalities = async () => {
  try {
    console.log("获取AI性格列表...");
    const response = await axiosInstance.get("/chat/personalities");
    console.log("获取到AI性格列表:", response.data);
    if (response.data.length > 0) {
      personalities.value = response.data;
      
      // 尝试获取用户当前选择的助手
      try {
        const userSettings = await axiosInstance.get('/users/settings');
        if (userSettings.data && userSettings.data.personality_id) {
          currentPersonalityId.value = userSettings.data.personality_id;
        } else {
          currentPersonalityId.value = 1; // 默认使用第一个助手
        }
      } catch (error) {
        console.error('获取用户设置失败，使用默认助手:', error);
        currentPersonalityId.value = 1;
      }
      
      console.log("成功加载并设置助手列表:", JSON.parse(JSON.stringify(personalities.value)));
    } else {
      console.warn("从后端获取的助手列表为空或格式不正确，将使用默认助手列表。", response.data);
      personalities.value = [{ id: 1, name: '默认助手', personality_type: '默认类型' }];
      currentPersonalityId.value = 1;
    }
  } catch (error) {
    console.error('获取助手列表失败，将使用默认助手列表:', error);
    personalities.value = [{ id: 1, name: '默认助手', personality_type: '默认类型' }];
    currentPersonalityId.value = 1;
  }
};

// 监听消息变化，自动滚动到底部
watch(messages, scrollToBottom, { deep: true });

onMounted(async () => {
  console.log("Chat.vue onMounted: 组件已挂载");
  scrollToBottom();
  // 获取助手列表
  await fetchPersonalities();
  // 获取聊天历史
  await fetchChatHistory();
});

watch(
  () => userStore.isLoggedIn,
  (isLoggedIn) => {
    if (!isLoggedIn) {
      messages.value = []; 
      console.log("用户已登出，聊天消息已清空");
  }
  }
);

</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px); /* Adjust based on your layout's header/footer */
  background-color: #E3F2ED; /* Mint theme background */
  overflow: hidden; /* Prevent double scrollbars */
}

.chat-header {
  padding: 12px 20px;
  background-color: #fff;
  border-bottom: 2px solid #A7E0C7;
  display: flex;
  align-items: center;
  justify-content: flex-end; /* Align personality selector to the right */
  box-shadow: 0 2px 8px rgba(61, 110, 89, 0.1);
}

.personality-selector {
  cursor: pointer;
}

.personality-display {
  cursor: pointer;
  color: #3D6E59; /* Mocha green */
  display: flex;
  align-items: center;
  font-weight: 500;
  gap: 5px;
}

.personality-avatar {
  margin-right: 4px;
}

.dropdown-personality-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.personality-type {
  font-size: 12px;
  color: #5DAF8E;
  margin-left: 4px;
}

.chat-messages {
  flex-grow: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px; /* Spacing between message groups */
}

.empty-chat {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #3D6E59;
}

.empty-image {
  width: 150px;
  height: 150px;
  opacity: 0.8;
}

.quick-starts {
  margin-top: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

/* Style the quick start buttons with mint theme */
.quick-starts .el-button {
  background-color: #F0FBF7;
  color: #3D6E59;
  border: 1px solid #A7E0C7;
  border-radius: 20px;
  transition: all 0.3s ease;
}

.quick-starts .el-button:hover {
  background-color: #5DAF8E;
  color: white;
  border-color: #5DAF8E;
}

.message {
  display: flex;
  align-items: flex-end;
  max-width: 75%;
  word-wrap: break-word;
}

.user-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.ai-message {
  align-self: flex-start;
}

.message-avatar {
  margin: 0 10px;
}

.message-content {
  display: flex;
  flex-direction: column;
}

.user-message .message-content {
  align-items: flex-end;
}

.ai-message .message-content {
  align-items: flex-start;
}

.message-bubble {
  padding: 10px 15px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.5;
}

.user-message .message-bubble {
  background-color: #5DAF8E; /* Medium mint */
  color: white;
  border-top-right-radius: 5px;
  box-shadow: 0 2px 6px rgba(61, 110, 89, 0.2);
}

.ai-message .message-bubble {
  background-color: #fff;
  color: #3D6E59; /* Mocha green for text */
  border: 1px solid #A7E0C7;
  border-top-left-radius: 5px;
  box-shadow: 0 2px 6px rgba(61, 110, 89, 0.1);
}

.message-time {
  font-size: 11px;
  color: #5DAF8E;
  margin-top: 5px;
  padding: 0 5px;
}

/* Typing Indicator */
.typing-indicator {
  display: flex;
  align-items: center;
  padding: 10px 20px;
  align-self: flex-start;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  margin: 0 2px;
  background-color: #A7E0C7;
  border-radius: 50%;
  display: inline-block;
  animation: wave 1.3s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -1.1s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: -0.9s;
}

@keyframes wave {
  0%, 60%, 100% {
    transform: initial;
  }
  30% {
    transform: translateY(-8px);
  }
}

/* Transaction Confirmation Box */
.transaction-confirmation {
  background-color: #F0FBF7;
  border: 1px solid #A7E0C7;
  border-radius: 16px;
  padding: 15px;
  margin-top: 10px; /* Space from the AI message bubble */
  margin-left: 60px; /* Align with AI message content, considering avatar space */
  max-width: calc(75% - 60px); /* Adjust based on message max-width and avatar */
  align-self: flex-start;
  box-shadow: 0 4px 12px rgba(61, 110, 89, 0.1);
}

.confirmation-header {
  display: flex;
  align-items: center;
  font-weight: bold;
  margin-bottom: 10px;
  color: #3D6E59;
}

.confirmation-header .el-icon {
  margin-right: 8px;
  color: #5DAF8E;
}

.confirmation-content .el-form-item {
  margin-bottom: 12px;
}

.confirmation-actions {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* Style for form elements in transaction confirmation */
:deep(.el-input__wrapper), 
:deep(.el-select .el-input__wrapper),
:deep(.el-date-editor.el-input__wrapper) {
  border-radius: 12px;
  border: 1px solid #A7E0C7;
  background-color: #FFFFFF;
}

:deep(.el-input__wrapper:hover),
:deep(.el-select .el-input__wrapper:hover),
:deep(.el-date-editor.el-input__wrapper:hover) {
  border-color: #5DAF8E;
}

:deep(.el-button) {
  border-radius: 20px;
}

:deep(.el-button--primary) {
  background-color: #5DAF8E;
  border-color: #5DAF8E;
}

:deep(.el-button--primary:hover) {
  background-color: #3D6E59;
  border-color: #3D6E59;
}

/* Confirmed Transaction Card */
.confirmed-transaction {
  margin-top: 10px;
  margin-left: 60px; /* Align with AI message content */
  max-width: calc(75% - 60px);
  align-self: flex-start;
}

.transaction-card {
  background-color: #E8F6F0; /* Lighter mint for confirmation */
  border: 1px solid #A7E0C7;
  border-radius: 16px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(61, 110, 89, 0.1);
}

.transaction-card-header {
  display: flex;
  align-items: center;
  font-weight: bold;
  color: #3D6E59;
  margin-bottom: 8px;
  font-size: 0.9em;
}

.transaction-card-header .el-icon {
  margin-right: 8px;
  font-size: 0.9em;
  color: #5DAF8E;
}

.transaction-card-content .transaction-type {
  margin-bottom: 8px;
}

/* Style for tags in transaction card */
:deep(.el-tag.el-tag--success) {
  background-color: #F0F9EB;
  color: #3CB371;
  border-color: #3CB371;
}

:deep(.el-tag.el-tag--danger) {
  background-color: #FFF0F0;
  color: #FF6B6B;
  border-color: #FF6B6B;
}

.transaction-card-content .transaction-amount {
  font-size: 1.1em;
  font-weight: bold;
  color: #3D6E59;
  margin-bottom: 8px;
}

.transaction-details {
  font-size: 0.85em;
  color: #3D6E59;
  margin-bottom: 8px;
}

.transaction-details > div {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.transaction-details .el-icon {
  margin-right: 6px;
  color: #5DAF8E;
  font-size: 0.9em;
}

.transaction-description {
  font-size: 0.85em;
  color: #3D6E59;
  font-style: italic;
}

/* Input Area */
.chat-input-container {
  padding: 15px 20px;
  background-color: #fff;
  border-top: 2px solid #A7E0C7;
  box-shadow: 0 -2px 8px rgba(61, 110, 89, 0.05);
}

.chat-input-container :deep(.el-input__wrapper) {
  border-radius: 24px;
  border: 1px solid #A7E0C7;
  background-color: #F0FBF7;
  transition: all 0.3s ease;
}

.chat-input-container :deep(.el-input__wrapper:focus-within) {
  border-color: #5DAF8E;
  box-shadow: 0 0 0 1px #5DAF8E;
}

.chat-input-container :deep(.el-input__inner) {
  height: 48px;
  color: #3D6E59;
}

.chat-input-container :deep(.el-button) {
  background-color: #5DAF8E;
  color: white;
  border-color: #5DAF8E;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-input-container :deep(.el-button:hover) {
  background-color: #3D6E59;
  border-color: #3D6E59;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
  .message {
    max-width: 90%;
  }
  .transaction-confirmation,
  .confirmed-transaction {
    margin-left: 50px;
    max-width: calc(90% - 50px);
  }
  .chat-messages {
    padding: 15px;
  }
  .chat-input-container {
    padding: 10px 15px;
  }
}
</style> 