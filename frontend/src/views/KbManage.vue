<template>
  <div class="page">
    <div class="top-actions">
      <el-button size="small" type="primary" plain @click="goToChat">知识库问答</el-button>
    </div>
    
    <h1>知识库管理</h1>
    
    <!-- 知识库管理区域 -->
    <div class="kb-management">
      <div class="kb-header">
        <h2>知识库列表</h2>
        <div class="kb-actions">
          <el-input
            v-model="newKbName"
            size="small"
            placeholder="新知识库名称"
            style="width: 180px"
          />
          <el-button size="small" type="primary" @click="handleCreateKb">新建知识库</el-button>
        </div>
      </div>
      
      <div class="kb-list">
        <el-card
          v-for="kb in kbList"
          :key="kb.kb_id"
          :class="['kb-card', { active: selectedKb === kb.kb_id }]"
          @click="selectKb(kb.kb_id)"
        >
          <div class="kb-card-content">
            <div class="kb-info">
              <div class="kb-icon">
                <img src="@/assets/database-icon.png" alt="kb-icon"/>
              </div>
              <div class="kb-name">{{ kb.kb_name }}</div>
            </div>
            <el-button
              link
              type="danger"
              size="small"
              @click.stop="handleDeleteKb(kb.kb_id, kb.kb_name)"
            >
              删除
            </el-button>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 文档管理区域 -->
    <div v-if="selectedKb" class="doc-management">
      <div class="doc-header">
        <h2>文档管理 - {{ selectedKbName }}</h2>
        <div class="doc-actions">
          <el-button type="primary" @click="loadDocs">刷新列表</el-button>
          <el-button type="success" @click="uploadVisible = true">导入文档</el-button>
          <el-button type="info" plain @click="exampleVisible = true">查看示例</el-button>
        </div>
      </div>
      
      <el-table
        v-loading="loading"
        :data="docs"
        size="small"
        stripe
        style="width: 100%; margin-top: 16px"
      >
        <el-table-column prop="id" label="文档 ID" width="280" />
        <el-table-column prop="content_preview" label="内容预览" show-overflow-tooltip />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openView(row.id)">查看</el-button>
            <el-button link type="primary" size="small" @click="openEdit(row.id)">编辑</el-button>
            <el-button link type="danger" size="small" @click="confirmDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadDocs"
        />
      </div>
    </div>
    
    <div v-else class="empty-state">
      <div class="empty-icon">📚</div>
      <p>请选择或创建一个知识库</p>
    </div>

    <!-- 查看全文对话框 -->
    <el-dialog v-model="viewVisible" title="文档内容" width="70%" destroy-on-close>
      <div class="doc-content">{{ currentDetail?.content }}</div>
      <template #footer>
        <el-button @click="viewVisible = false">关闭</el-button>
        <el-button type="primary" @click="openEdit(currentDetail?.id); viewVisible = false">编辑</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editVisible" title="编辑文档" width="70%" destroy-on-close @closed="editDocId = null; editContent = ''">
      <el-input
        v-model="editContent"
        type="textarea"
        :rows="12"
        placeholder="文档内容"
      />
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 导入文档对话框 -->
    <el-dialog v-model="uploadVisible" title="导入文档" width="700px" destroy-on-close @closed="resetUpload">
      <el-tabs v-model="uploadTab">
        <el-tab-pane label="上传文件" name="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            :limit="10"
            accept=".txt,.json,.jsonl,.doc,.docx"
            drag
            multiple
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 TXT、JSON、JSONL、DOC、DOCX 格式，单个文件不超过 10MB，最多 10 个文件
              </div>
            </template>
          </el-upload>
        </el-tab-pane>
        
        <el-tab-pane label="直接输入" name="text">
          <el-input
            v-model="directText"
            type="textarea"
            :rows="12"
            placeholder="直接输入文本内容（最多 50000 字符）"
            maxlength="50000"
            show-word-limit
          />
        </el-tab-pane>
      </el-tabs>
      
      <div v-if="uploading" class="upload-progress">
        <el-progress :percentage="uploadProgress" :status="uploadStatus" />
        <div class="upload-stage">{{ uploadStage }}</div>
      </div>

      <template #footer>
        <el-button @click="uploadVisible = false" :disabled="uploading">取消</el-button>
        <el-button type="primary" @click="submitUpload" :loading="uploading">
          {{ uploading ? '导入中...' : '开始导入' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 格式示例对话框 -->
    <el-dialog v-model="exampleVisible" title="文件格式示例" width="800px" destroy-on-close>
      <el-tabs v-model="exampleTab">
        <el-tab-pane label="JSONL 格式（推荐）" name="jsonl">
          <div class="example-section">
            <h4>格式 1: 嵌套 documents 数组（推荐用于医学文档）</h4>
            <p class="example-desc">每行一个 JSON 对象，包含 documents 数组，支持 id、title、content 字段</p>
            <pre class="code-block">{{ jsonlExample }}</pre>
            
            <h4>格式 2: 题库格式</h4>
            <p class="example-desc">适合导入问答题库</p>
            <pre class="code-block">{{ jsonlQuestionExample }}</pre>
            
            <h4>格式 3: 简单格式</h4>
            <p class="example-desc">最简单的格式，直接提供内容</p>
            <pre class="code-block">{{ jsonlSimpleExample }}</pre>
            
            <el-alert type="info" :closable="false" style="margin-top: 15px">
              <template #title>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span>💡 提示</span>
                </div>
              </template>
              <div>
                • 推荐使用格式 1，结构清晰，便于管理<br>
                • 系统会自动保存 id 和 title 到元数据<br>
                • 如果同时提供 title 和 content，会组合为"标题\n\n内容"<br>
                • 示例文件：<code>python/demo/sample_documents.jsonl</code>
              </div>
            </el-alert>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="JSON 格式" name="json">
          <div class="example-section">
            <h4>列表格式</h4>
            <p class="example-desc">包含多个文档对象的数组</p>
            <pre class="code-block">{{ jsonExample }}</pre>
            
            <h4>对象格式</h4>
            <p class="example-desc">单个文档对象</p>
            <pre class="code-block">{{ jsonSingleExample }}</pre>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="TXT 格式" name="txt">
          <div class="example-section">
            <h4>纯文本格式</h4>
            <p class="example-desc">系统会自动按空行分段</p>
            <pre class="code-block">{{ txtExample }}</pre>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="Word 格式" name="word">
          <div class="example-section">
            <h4>Word 文档 (.doc / .docx)</h4>
            <p class="example-desc">系统会自动提取段落并按 500 字符切分</p>
            <div class="word-example">
              <div class="word-icon">📄</div>
              <div class="word-info">
                <p><strong>支持的格式：</strong>.doc、.docx</p>
                <p><strong>处理方式：</strong></p>
                <ul>
                  <li>提取所有段落文本</li>
                  <li>按 500 字符自动切分</li>
                  <li>保持段落完整性</li>
                  <li>生成向量并存储</li>
                </ul>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
      
      <template #footer>
        <el-button type="primary" @click="exampleVisible = false">知道了</el-button>
        <el-button @click="downloadSample">下载示例文件</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { UploadFilled } from '@element-plus/icons-vue';

const KB_CACHE_KEY = 'rag_selected_kb';
const route = useRoute();
const router = useRouter();
const API_BASE = import.meta.env.VITE_PY_API_BASE_URL || 'http://127.0.0.1:8000';

// 知识库管理
const kbList = ref([]);
const selectedKb = ref('');
const newKbName = ref('');

// 文档管理
const docs = ref([]);
const loading = ref(false);
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);

// 对话框
const viewVisible = ref(false);
const currentDetail = ref(null);
const editVisible = ref(false);
const editDocId = ref(null);
const editContent = ref('');
const saving = ref(false);

// 上传相关
const uploadVisible = ref(false);
const uploadTab = ref('file');
const fileList = ref([]);
const directText = ref('');
const uploading = ref(false);
const uploadProgress = ref(0);
const uploadStatus = ref('');
const uploadStage = ref('');
const uploadRef = ref(null);

// 示例对话框
const exampleVisible = ref(false);
const exampleTab = ref('jsonl');

// 计算属性
const selectedKbName = computed(() => {
  const kb = kbList.value.find(k => k.kb_id === selectedKb.value);
  return kb ? kb.kb_name : '';
});

// 格式示例
const jsonlExample = `{"documents": [{"id": "doc1", "title": "糖尿病视网膜病变概述", "content": "糖尿病视网膜病变是糖尿病最常见的微血管并发症之一..."}]}
{"documents": [{"id": "doc2", "title": "高血压的诊断标准", "content": "高血压是指收缩压≥140mmHg和/或舒张压≥90mmHg..."}]}`;

const jsonlQuestionExample = `{"question": "什么是气虚证？", "answer": "气虚证是中医学中的一个重要证候"}
{"question": "气虚证的主要表现？", "answer": "神疲乏力、气短懒言"}`;

const jsonlSimpleExample = `{"content": "气虚证是中医学中的一个重要证候"}
{"content": "气虚证的主要表现包括神疲乏力、气短懒言"}`;

const jsonExample = `[
  {"content": "气虚证是中医学中的一个重要证候"},
  {"content": "气虚证的主要表现包括神疲乏力、气短懒言"}
]`;

const jsonSingleExample = `{
  "content": "气虚证是中医学中的一个重要证候"
}`;

const txtExample = `气虚证是中医学中的一个重要证候。

气虚证的主要表现包括：
1. 神疲乏力
2. 气短懒言
3. 自汗`;

// 生命周期
onMounted(async () => {
  await loadKbList();
  const cached = localStorage.getItem(KB_CACHE_KEY);
  if (cached && kbList.value.some(k => k.kb_id === cached)) {
    selectedKb.value = cached;
  }
});

watch(selectedKb, (val) => {
  if (val) {
    localStorage.setItem(KB_CACHE_KEY, val);
    page.value = 1;
    loadDocs();
  }
});

// 导航
function goToChat() {
  router.push('/chat');
}

// 知识库管理函数
async function loadKbList() {
  try {
    const token = localStorage.getItem('token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const resp = await axios.get(`${API_BASE}/api/v1/knowledge-bases`, { headers });
    kbList.value = resp.data.knowledge_bases || [];
  } catch (e) {
    console.error('获取知识库列表失败', e);
    ElMessage.error('获取知识库列表失败');
  }
}

function selectKb(kbId) {
  selectedKb.value = kbId;
}

async function handleCreateKb() {
  const name = newKbName.value.trim();
  if (!name) {
    ElMessage.warning('请输入知识库名称');
    return;
  }
  try {
    const token = localStorage.getItem('token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const resp = await axios.post(`${API_BASE}/api/v1/knowledge-bases`, { kb_name: name }, { headers });
    newKbName.value = '';
    await loadKbList();
    // 设置选中的知识库为返回的 kb_id
    if (resp.data.kb_id) {
      selectedKb.value = resp.data.kb_id;
    }
    ElMessage.success('知识库创建成功');
  } catch (e) {
    console.error('创建知识库失败', e);
    ElMessage.error('创建失败：' + (e.response?.data?.detail || e.message));
  }
}

async function handleDeleteKb(kbId, kbName) {
  if (!confirm(`确定删除知识库 "${kbName}" 及其所有文档吗？`)) return;
  try {
    const token = localStorage.getItem('token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    await axios.delete(`${API_BASE}/api/v1/knowledge-bases/${kbId}`, { headers });
    await loadKbList();
    if (selectedKb.value === kbId) {
      selectedKb.value = '';
      docs.value = [];
    }
    ElMessage.success('知识库已删除');
  } catch (e) {
    console.error('删除知识库失败', e);
    ElMessage.error('删除失败：' + (e.response?.data?.detail || e.message));
  }
}

// 文档管理函数
async function loadDocs() {
  if (!selectedKb.value) return;
  loading.value = true;
  try {
    const token = localStorage.getItem('token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const [listResp, countResp] = await Promise.all([
      axios.get(`${API_BASE}/knowledge/docs`, {
        params: {
          kb_id: selectedKb.value,
          limit: pageSize.value,
          offset: (page.value - 1) * pageSize.value,
        },
        headers,
      }),
      axios.get(`${API_BASE}/knowledge/docs/count`, { params: { kb_id: selectedKb.value }, headers }),
    ]);
    docs.value = listResp.data || [];
    total.value = countResp.data?.count ?? 0;
  } catch (e) {
    console.error(e);
    docs.value = [];
    total.value = 0;
    ElMessage.error('加载文档列表失败');
  } finally {
    loading.value = false;
  }
}

async function openView(docId) {
  try {
    const token = localStorage.getItem('token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const resp = await axios.get(`${API_BASE}/knowledge/docs/detail`, {
      params: { kb_id: selectedKb.value, doc_id: docId },
      headers,
    });
    currentDetail.value = resp.data;
    viewVisible.value = true;
  } catch (e) {
    ElMessage.error('获取文档失败：' + (e.response?.data?.detail || e.message));
  }
}

async function openEdit(docId) {
  try {
    const token = localStorage.getItem('token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const resp = await axios.get(`${API_BASE}/knowledge/docs/detail`, {
      params: { kb_id: selectedKb.value, doc_id: docId },
      headers,
    });
    editDocId.value = resp.data.id;
    editContent.value = resp.data.content || '';
    editVisible.value = true;
  } catch (e) {
    ElMessage.error('获取文档失败：' + (e.response?.data?.detail || e.message));
  }
}

async function saveEdit() {
  if (!editDocId.value || editContent.value.trim() === '') return;
  saving.value = true;
  try {
    const token = localStorage.getItem('token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    await axios.put(`${API_BASE}/knowledge/docs/update`, {
      kb_id: selectedKb.value,
      doc_id: editDocId.value,
      content: editContent.value.trim(),
    }, { headers });
    ElMessage.success('保存成功');
    editVisible.value = false;
    await loadDocs();
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message));
  } finally {
    saving.value = false;
  }
}

async function confirmDelete(docId) {
  if (!confirm('确定删除这条文档吗？')) return;
  try {
    const token = localStorage.getItem('token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    await axios.delete(`${API_BASE}/knowledge/docs/delete`, {
      params: { kb_id: selectedKb.value, doc_id: docId },
      headers,
    });
    ElMessage.success('已删除');
    await loadDocs();
  } catch (e) {
    ElMessage.error('删除失败：' + (e.response?.data?.detail || e.message));
  }
}

// 上传相关函数
function handleFileChange(file, files) {
  fileList.value = files;
}

function resetUpload() {
  fileList.value = [];
  directText.value = '';
  uploadProgress.value = 0;
  uploadStatus.value = '';
  uploadStage.value = '';
  uploading.value = false;
}

async function submitUpload() {
  if (uploadTab.value === 'file') {
    if (fileList.value.length === 0) {
      ElMessage.warning('请选择要上传的文件');
      return;
    }
    await uploadFiles();
  } else {
    if (!directText.value.trim()) {
      ElMessage.warning('请输入文本内容');
      return;
    }
    await uploadText();
  }
}

async function uploadFiles() {
  uploading.value = true;
  uploadProgress.value = 0;
  uploadStatus.value = '';
  
  let successCount = 0;
  let failCount = 0;
  
  const token = localStorage.getItem('token');
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  
  for (let i = 0; i < fileList.value.length; i++) {
    const file = fileList.value[i];
    uploadStage.value = `正在处理文件 ${i + 1}/${fileList.value.length}: ${file.name}`;
    uploadProgress.value = Math.floor((i / fileList.value.length) * 100);
    
    try {
      const formData = new FormData();
      formData.append('kb_id', selectedKb.value);
      formData.append('file', file.raw);
      
      await axios.post(`${API_BASE}/knowledge/upload_file`, formData, {
        headers: headers,
      });
      
      successCount++;
    } catch (e) {
      failCount++;
      console.error(`文件 ${file.name} 导入失败:`, e);
    }
  }
  
  uploadProgress.value = 100;
  uploadStatus.value = failCount === 0 ? 'success' : 'warning';
  uploadStage.value = `导入完成：成功 ${successCount} 个，失败 ${failCount} 个`;
  
  setTimeout(() => {
    uploading.value = false;
    if (failCount === 0) {
      ElMessage.success(`成功导入 ${successCount} 个文件`);
      uploadVisible.value = false;
      loadDocs();
    } else {
      ElMessage.warning(`导入完成：成功 ${successCount} 个，失败 ${failCount} 个`);
    }
  }, 1500);
}

async function uploadText() {
  uploading.value = true;
  uploadProgress.value = 0;
  uploadStage.value = '正在处理文本内容...';
  
  try {
    const blob = new Blob([directText.value], { type: 'text/plain' });
    const file = new File([blob], 'direct_input.txt', { type: 'text/plain' });
    
    const formData = new FormData();
    formData.append('kb_id', selectedKb.value);
    formData.append('file', file);
    
    uploadProgress.value = 50;
    
    const token = localStorage.getItem('token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    
    await axios.post(`${API_BASE}/knowledge/upload_file`, formData, {
      headers: headers,
    });
    
    uploadProgress.value = 100;
    uploadStatus.value = 'success';
    uploadStage.value = '导入成功';
    
    setTimeout(() => {
      uploading.value = false;
      ElMessage.success('文本导入成功');
      uploadVisible.value = false;
      loadDocs();
    }, 1000);
  } catch (e) {
    uploadProgress.value = 100;
    uploadStatus.value = 'exception';
    uploadStage.value = '导入失败';
    uploading.value = false;
    ElMessage.error('文本导入失败：' + (e.response?.data?.detail || e.message));
  }
}

function downloadSample() {
  const sampleContent = `{"documents": [{"id": "doc1", "title": "糖尿病视网膜病变概述", "content": "糖尿病视网膜病变是糖尿病最常见的微血管并发症之一，主要由于长期高血糖导致视网膜微血管损伤。其早期表现通常包括微血管瘤、点状出血和硬性渗出。如果不及时治疗，可能逐渐发展为视网膜水肿甚至失明。"}]}
{"documents": [{"id": "doc2", "title": "高血压的诊断标准", "content": "高血压是指收缩压≥140mmHg和/或舒张压≥90mmHg。根据血压水平，高血压可分为1级（轻度）、2级（中度）和3级（重度）。诊断时需要在不同时间测量血压至少3次，排除白大衣高血压等情况。"}]}
{"documents": [{"id": "doc3", "title": "冠心病的危险因素", "content": "冠心病的主要危险因素包括：高血压、高血脂、糖尿病、吸烟、肥胖、缺乏运动、家族史等。其中，高血压、高血脂和糖尿病被称为冠心病的三大危险因素。控制这些危险因素对预防冠心病至关重要。"}]}`;
  
  const blob = new Blob([sampleContent], { type: 'application/jsonl' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'sample_documents.jsonl';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  
  ElMessage.success('示例文件已下载');
}
</script>

<style scoped>
.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.top-actions {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 20px;
}

h1 {
  font-size: 32px;
  font-weight: 600;
  margin: 0 0 24px 0;
  color: #303133;
}

h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #303133;
}

/* 知识库管理区域 */
.kb-management {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.kb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.kb-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.kb-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.kb-card {
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid #e4e7ed;
}

.kb-card:hover {
  border-color: #409eff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.kb-card.active {
  border-color: #409eff;
  background: #f0f9ff;
}

.kb-card-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kb-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.kb-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #eef2f7;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  flex-shrink: 0;
}

.kb-icon img {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.kb-name {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

/* 文档管理区域 */
.doc-management {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 24px;
}

.doc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.doc-actions {
  display: flex;
  gap: 12px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state p {
  font-size: 16px;
  margin: 0;
}

/* 对话框内容 */
.doc-content {
  white-space: pre-wrap;
  max-height: 60vh;
  overflow-y: auto;
  padding: 8px 0;
  line-height: 1.6;
}

/* 上传相关 */
.upload-progress {
  margin-top: 20px;
}

.upload-stage {
  margin-top: 10px;
  text-align: center;
  color: #606266;
  font-size: 14px;
}

.el-icon--upload {
  font-size: 67px;
  color: #409EFF;
  margin: 40px 0 16px;
}

.el-upload__text {
  color: #606266;
  font-size: 14px;
}

.el-upload__text em {
  color: #409EFF;
  font-style: normal;
}

/* 示例样式 */
.example-section {
  padding: 10px 0;
}

.example-section h4 {
  margin: 20px 0 10px 0;
  color: #303133;
  font-size: 15px;
  font-weight: 600;
}

.example-section h4:first-child {
  margin-top: 0;
}

.example-desc {
  margin: 5px 0 10px 0;
  color: #909399;
  font-size: 13px;
}

.code-block {
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #606266;
  margin: 0;
}

.word-example {
  display: flex;
  gap: 20px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-top: 10px;
}

.word-icon {
  font-size: 48px;
  line-height: 1;
}

.word-info {
  flex: 1;
}

.word-info p {
  margin: 8px 0;
  color: #606266;
  font-size: 14px;
}

.word-info ul {
  margin: 5px 0;
  padding-left: 20px;
  color: #606266;
  font-size: 13px;
}

.word-info ul li {
  margin: 3px 0;
}
</style>
