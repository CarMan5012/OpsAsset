<template>
  <section class="tab-pane">
    <!-- 顶部吸顶操作栏 (Sticky Header，滚动时始终置顶保持可见) -->
    <!-- 顶部吸顶操作栏 (Sticky Header，滚动时始终置顶保持可见) -->
    <div class="ops-card"
      style="position: sticky; top: 0; z-index: 40; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.94); backdrop-filter: blur(12px); border-bottom: 2px solid #e2e8f0; padding: 14px 20px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);">
      <div style="display: flex; align-items: center; gap: 8px;">
        <Settings :size="18" style="color: #2563eb;" />
        <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin: 0;">
          资产模型与元数据字典配置
        </h3>
      </div>
      <div style="display: flex; gap: 10px; align-items: center;">
        <el-button @click="handleResetConfig" size="default">
          <RefreshCw :size="13" style="margin-right: 4px;" /> 恢复出厂默认
        </el-button>
        <el-button type="primary" size="default" :loading="saving" @click="handleSaveConfig" style="box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25);">
          <Save :size="14" style="margin-right: 4px;" /> 保存全部字典配置
        </el-button>
      </div>
    </div>

    <!-- 5 张元数据管理卡片 -->
    <div style="display: grid; grid-template-columns: 1fr; gap: 20px;">
      <!-- 1. 中间件与服务组件类型模板 (核心) -->
      <div class="ops-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <h4 style="font-size: 15px; font-weight: 700; color: #0f172a; margin: 0; display: flex; align-items: center; gap: 6px;">
            <Puzzle :size="16" style="color: #2563eb;" /> 中间件与服务组件类型模板
          </h4>
          <el-button type="primary" size="small" @click="openAddClusterTypeDialog">+ 新增组件类型</el-button>
        </div>

        <el-table :data="localConfig.cluster_types" stripe border style="width: 100%;">
          <el-table-column label="图标" width="65" align="center">
            <template #default="{ row }">
              <span v-html="getMiddlewareLogo(row.key, 20)" style="display: flex; align-items: center; justify-content: center;"></span>
            </template>
          </el-table-column>
          <el-table-column prop="key" label="系统标识 (Key)" width="140">
            <template #default="{ row }">
              <el-input v-model="row.key" size="small"></el-input>
            </template>
          </el-table-column>
          <el-table-column prop="label" label="页面显示名 (Label)" min-width="160">
            <template #default="{ row }">
              <el-input v-model="row.label" size="small"></el-input>
            </template>
          </el-table-column>
          <el-table-column prop="default_port" label="默认服务端口" width="160">
            <template #default="{ row }">
              <el-input v-model="row.default_port" size="small" placeholder="如: 6379"></el-input>
            </template>
          </el-table-column>
          <el-table-column label="节点角色清单" min-width="320">
            <template #default="{ row, $index }">
              <div style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center;">
                <el-tag v-for="(r, rIndex) in row.roles" :key="r.key" size="small" closable @close="removeRole(row, rIndex)"
                  :class="r.key.toLowerCase().includes('master') || r.key.toLowerCase().includes('primary') || r.key.includes('主') ? 'role-master' : 'role-worker'">
                  {{ r.label || r.key }}
                </el-tag>
                <el-button size="small" link type="primary" @click="promptAddRole(row)">+ 增加角色</el-button>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ $index }">
              <el-button link type="danger" size="small" @click="removeClusterType($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 2. 运行环境与状态配置 -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <!-- 运行环境 -->
        <div class="ops-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
            <h4 style="font-size: 14px; font-weight: 700; color: #0f172a; margin: 0; display: flex; align-items: center; gap: 6px;">
              <Globe :size="16" style="color: #2563eb;" /> 运行环境配置
            </h4>
            <el-button size="small" link type="primary" @click="addEnvironment">+ 新增环境</el-button>
          </div>
          <el-table :data="localConfig.environments" size="small" border stripe>
            <el-table-column prop="key" label="系统标识 (Key)" width="110">
              <template #default="{ row }">
                <el-input v-model="row.key" size="small"></el-input>
              </template>
            </el-table-column>
            <el-table-column prop="label" label="页面显示名 (Label)" min-width="120">
              <template #default="{ row }">
                <el-input v-model="row.label" size="small"></el-input>
              </template>
            </el-table-column>
            <el-table-column label="标签样式预览" width="110" align="center">
              <template #default="{ row }">
                <span class="env-tag" :class="row.key">{{ row.label || row.key }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="70" align="center">
              <template #default="{ $index }">
                <el-button link type="danger" size="small" @click="localConfig.environments.splice($index, 1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 主机状态 -->
        <div class="ops-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
            <h4 style="font-size: 14px; font-weight: 700; color: #0f172a; margin: 0; display: flex; align-items: center; gap: 6px;">
              <Activity :size="16" style="color: #10b981;" /> 主机状态配置
            </h4>
            <el-button size="small" link type="primary" @click="addHostStatus">+ 新增状态</el-button>
          </div>
          <el-table :data="localConfig.host_statuses" size="small" border stripe>
            <el-table-column prop="key" label="系统标识 (Key)" width="105">
              <template #default="{ row }">
                <el-input v-model="row.key" size="small" placeholder="如: online"></el-input>
              </template>
            </el-table-column>
            <el-table-column prop="label" label="页面显示名 (Label)" min-width="100">
              <template #default="{ row }">
                <el-input v-model="row.label" size="small" placeholder="如: 在线"></el-input>
              </template>
            </el-table-column>
            <el-table-column label="主题颜色" width="80" align="center">
              <template #default="{ row }">
                <el-color-picker v-model="row.color" size="small"
                  :predefine="['#10b981', '#ef4444', '#f59e0b', '#3b82f6', '#8b5cf6', '#06b6d4', '#ec4899', '#64748b']" />
              </template>
            </el-table-column>
            <el-table-column label="指示灯胶囊预览" width="130" align="center">
              <template #default="{ row }">
                <span class="status-tag"
                  :style="{
                    backgroundColor: row.color ? `${row.color}18` : 'rgba(100, 116, 139, 0.1)',
                    color: row.color || '#475569',
                    borderColor: row.color ? `${row.color}45` : 'rgba(100, 116, 139, 0.25)'
                  }">
                  <span class="status-indicator"
                    :style="{
                      backgroundColor: row.color || '#94a3b8',
                      boxShadow: row.color ? `0 0 0 2px ${row.color}33` : 'none'
                    }"></span>
                  {{ row.label || row.key || '未命名' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="65" align="center">
              <template #default="{ $index }">
                <el-button link type="danger" size="small" @click="localConfig.host_statuses.splice($index, 1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 3. CPU 架构与常见 OS 字典 -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <!-- CPU 架构 -->
        <div class="ops-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
            <h4 style="font-size: 14px; font-weight: 700; color: #0f172a; margin: 0; display: flex; align-items: center; gap: 6px;">
              <Cpu :size="16" style="color: #2563eb;" /> CPU 架构配置
            </h4>
            <el-button size="small" link type="primary" @click="addCpuArch">+ 新增架构</el-button>
          </div>
          <el-table :data="localConfig.cpu_architectures" size="small" border stripe>
            <el-table-column prop="key" label="系统标识 (Key)" width="120">
              <template #default="{ row }">
                <el-input v-model="row.key" size="small"></el-input>
              </template>
            </el-table-column>
            <el-table-column prop="label" label="页面显示名 (Label)" min-width="120">
              <template #default="{ row }">
                <el-input v-model="row.label" size="small"></el-input>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="70" align="center">
              <template #default="{ $index }">
                <el-button link type="danger" size="small" @click="localConfig.cpu_architectures.splice($index, 1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 常用操作系统列表 -->
        <div class="ops-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
            <h4 style="font-size: 14px; font-weight: 700; color: #0f172a; margin: 0; display: flex; align-items: center; gap: 6px;">
              <Terminal :size="16" style="color: #2563eb;" /> 常用操作系统列表
            </h4>
            <el-button size="small" link type="primary" @click="addOsItem">+ 新增系统</el-button>
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: 8px; max-height: 180px; overflow-y: auto; padding: 4px 0;">
            <el-tag v-for="(os, idx) in localConfig.common_os_list" :key="idx" size="default" closable
              @close="localConfig.common_os_list.splice(idx, 1)" style="font-size: 12px; font-weight: 500;">
              {{ os }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 弹窗 -->
    <AddClusterTypeDialog ref="addClusterTypeDialogRef" @add="handleAddClusterType" />
  </section>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Settings, RefreshCw, Save, Puzzle, Globe, Activity, Cpu, Terminal } from 'lucide-vue-next'
import OpsApi from '../api'
import { getMiddlewareLogo, serializeMetaConfigForBackend } from '../utils'
import AddClusterTypeDialog from '../components/AddClusterTypeDialog.vue'

const props = defineProps({
  metaConfig: { type: Object, required: true }
})
const emit = defineEmits(['saved'])

const saving = ref(false)
const addClusterTypeDialogRef = ref(null)

const localConfig = reactive({
  environments: [],
  host_statuses: [],
  cpu_architectures: [],
  cluster_types: [],
  common_os_list: []
})

watch(
  () => props.metaConfig,
  (val) => {
    if (val) {
      localConfig.environments = JSON.parse(JSON.stringify(val.environments || []))
      localConfig.host_statuses = JSON.parse(JSON.stringify(val.host_statuses || []))
      localConfig.cpu_architectures = JSON.parse(JSON.stringify(val.cpu_architectures || []))
      localConfig.cluster_types = JSON.parse(JSON.stringify(val.cluster_types || []))
      localConfig.common_os_list = JSON.parse(JSON.stringify(val.common_os_list || []))
    }
  },
  { immediate: true, deep: true }
)

const openAddClusterTypeDialog = () => {
  addClusterTypeDialogRef.value?.open()
}

const handleAddClusterType = (form) => {
  const roles = form.initialRoles
    ? form.initialRoles.split(/[,，\s]+/).filter(Boolean).map(r => ({ key: r, label: r }))
    : []
  localConfig.cluster_types.push({
    key: form.key,
    label: form.label,
    default_port: '',
    roles: roles
  })
  ElMessage.success(`已添加组件类型: ${form.label}`)
}

const removeClusterType = (index) => {
  localConfig.cluster_types.splice(index, 1)
}

const removeRole = (clusterTypeObj, rIndex) => {
  clusterTypeObj.roles.splice(rIndex, 1)
}

const promptAddRole = (clusterTypeObj) => {
  ElMessageBox.prompt('请输入要新增的角色标识（如: Master, Worker, Slave, Broker）:', `为 ${clusterTypeObj.label} 新增角色`, {
    confirmButtonText: '确定添加',
    cancelButtonText: '取消',
    inputPattern: /\S+/,
    inputErrorMessage: '角色名称不能为空'
  }).then(({ value }) => {
    const roleKey = value.trim()
    if (!clusterTypeObj.roles) clusterTypeObj.roles = []
    if (clusterTypeObj.roles.some(r => r.key === roleKey)) {
      ElMessage.warning('该角色已存在')
      return
    }
    clusterTypeObj.roles.push({ key: roleKey, label: roleKey })
    ElMessage.success(`角色 ${roleKey} 添加成功`)
  }).catch(() => {})
}

const addEnvironment = () => {
  localConfig.environments.push({ key: '', label: '' })
}

const addHostStatus = () => {
  localConfig.host_statuses.push({ key: '', label: '', color: '#10b981', type: 'success' })
}

const addCpuArch = () => {
  localConfig.cpu_architectures.push({ key: '', label: '' })
}

const addOsItem = () => {
  ElMessageBox.prompt('请输入新的操作系统全称（如: Debian 12, openEuler 22.03）:', '录入常用 OS', {
    confirmButtonText: '确定录入',
    cancelButtonText: '取消',
    inputPattern: /\S+/,
    inputErrorMessage: 'OS 名称不能为空'
  }).then(({ value }) => {
    const osName = value.trim()
    if (localConfig.common_os_list.includes(osName)) {
      ElMessage.warning('该 OS 已在列表中')
      return
    }
    localConfig.common_os_list.push(osName)
    ElMessage.success(`已录入 OS: ${osName}`)
  }).catch(() => {})
}

const handleSaveConfig = async () => {
  saving.value = true
  try {
    const payload = serializeMetaConfigForBackend({
      environments: localConfig.environments.filter(e => e.key && e.label),
      host_statuses: localConfig.host_statuses.filter(s => s.key && s.label),
      cpu_architectures: localConfig.cpu_architectures.filter(a => a.key && a.label),
      cluster_types: localConfig.cluster_types.filter(c => c.key && c.label),
      common_os_list: localConfig.common_os_list.filter(Boolean)
    })
    const res = await OpsApi.saveConfig(payload)
    ElMessage.success('字典元数据配置已成功保存并实时生效')
    emit('saved', res.data)
  } catch (e) {
    ElMessage.error('保存字典配置失败')
  } finally {
    saving.value = false
  }
}

const handleResetConfig = () => {
  ElMessageBox.confirm('确定要恢复出厂默认字典配置吗？所有自定义组件类型和角色将被重置。', '恢复默认警告', {
    confirmButtonText: '确认恢复',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await OpsApi.resetConfig()
      ElMessage.success('已成功恢复出厂默认配置')
      emit('saved', res.data)
    } catch (e) {
      ElMessage.error('恢复默认失败')
    }
  }).catch(() => {})
}
</script>
