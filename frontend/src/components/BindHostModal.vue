<template>
  <el-dialog v-model="visible" :title="'绑定节点 · ' + (activeCluster?.name || '')" width="1160px" top="4vh" append-to-body destroy-on-close>
    <div class="bind-host-toolbar" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; background: #f8fafc; padding: 12px 16px; border-radius: 8px; border: 1px solid #e2e8f0;">
      <div class="bind-host-summary" style="display: flex; align-items: center; gap: 10px; font-size: 13px; color: #475569;">
        <span style="font-weight: 700; color: #0f172a; font-size: 14px;">目标集群: {{ activeCluster?.name }}</span>
        <span class="env-tag" :class="activeCluster?.env">{{ getEnvLabel(activeCluster?.env) }}</span>
        <div class="badge-kv">
          <span class="badge-kv-key">{{ activeCluster?.cluster_type }}</span>
          <span v-if="activeCluster?.version" class="badge-kv-val">{{ activeCluster.version }}</span>
        </div>
      </div>
      <div class="bind-host-filters" style="display: flex; gap: 8px; align-items: center;">
        <el-select v-model="bindEnvFilter" class="bind-host-env" placeholder="全部环境" size="small" style="width: 120px;" clearable>
          <el-option label="全部环境" value="" />
          <el-option v-for="env in metaConfig.environments" :key="env.key" :label="env.label" :value="env.key" />
        </el-select>
        <el-input v-model="bindKeyword" class="bind-host-search" placeholder="搜索主机名/IP/系统" size="small" clearable style="width: 200px;">
          <template #prefix><Search :size="13" style="color: #94a3b8;" /></template>
        </el-input>
      </div>
    </div>

    <!-- 绑定表格 (1:1 包含主机资产全部字段，固定表头与视口局部滚动) -->
    <el-table :data="filteredBindHosts" size="small" stripe border max-height="450px" style="width: 100%;" v-loading="loading">
      <el-table-column prop="_selected" label="加入集群" width="90" align="center" fixed="left" sortable>
        <template #default="{ row }">
          <el-checkbox v-model="row._selected" />
        </template>
      </el-table-column>

      <el-table-column prop="hostname" label="主机名" min-width="140" fixed="left" sortable>
        <template #default="{ row }">
          <span :style="{ fontWeight: row._selected ? '600' : 'normal', color: row._selected ? '#0f172a' : '#64748b' }">
            {{ row.hostname }}
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="private_ip" label="内网 IP" min-width="135" fixed="left" sortable>
        <template #default="{ row }">
          <span class="ip-code" @click="copyText(row.private_ip)" title="点击复制">{{ row.private_ip }}</span>
        </template>
      </el-table-column>

      <!-- 节点角色分配列 -->
      <el-table-column v-if="hasClusterRoles(activeCluster?.cluster_type)" prop="_role" label="节点角色" width="165" align="center" fixed="left">
        <template #default="{ row }">
          <div v-if="row._selected" style="display: flex; align-items: center; justify-content: center; gap: 4px;">
            <el-select v-model="row._role" size="small" placeholder="分配角色" style="width: 100%;">
              <el-option v-for="r in activeClusterRoles" :key="r.key" :label="r.key || r.label" :value="r.key" />
            </el-select>
          </div>
          <span v-else style="color: #cbd5e1; font-size: 11px;">未勾选</span>
        </template>
      </el-table-column>

      <el-table-column prop="env" label="环境" width="80" align="center" sortable>
        <template #default="{ row }">
          <span class="env-tag" :class="row.env">{{ getEnvLabel(row.env) }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="95" align="center" sortable>
        <template #default="{ row }">
          <span class="status-tag" :class="'status-tag-' + row.status">
            <span class="status-indicator" :class="'status-' + row.status"></span>
            {{ getStatusLabel(row.status) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="cpu_cores" label="CPU" width="75" align="center" sortable>
        <template #default="{ row }">{{ row.cpu_cores }} 核</template>
      </el-table-column>

      <el-table-column prop="memory_gb" label="内存" width="80" align="center" sortable>
        <template #default="{ row }">{{ formatStorageValue(row.memory_gb) }} {{ formatStorageUnit(row.memory_gb) }}</template>
      </el-table-column>

      <el-table-column prop="disk_gb" label="数据盘" width="90" align="center" sortable>
        <template #default="{ row }">{{ formatStorageValue(row.disk_gb) }} {{ formatStorageUnit(row.disk_gb) }}</template>
      </el-table-column>

      <el-table-column prop="os" label="操作系统" min-width="130" show-overflow-tooltip>
        <template #default="{ row }">
          <span style="font-size: 11.5px; color: #475569;">{{ row.os || '-' }}</span>
        </template>
      </el-table-column>

      <el-table-column label="已归属的其他集群/服务" min-width="220">
        <template #default="{ row }">
          <div style="display: flex; flex-wrap: wrap; gap: 4px; align-items: center;">
            <span v-if="row._selected" class="badge-kv" style="font-size: 10px; border-color: #93c5fd;">
              <span class="badge-kv-key" style="padding: 1px 6px; background: #2563eb;">{{ activeCluster?.name }}</span>
              <span v-if="row._role" class="badge-kv-val" style="padding: 1px 5px; color: #2563eb;">{{ row._role }}</span>
            </span>
            <span v-for="c in (row.clusters || []).filter(c => c.cluster_id !== activeCluster?.id)" :key="c.cluster_id" class="badge-kv" style="font-size: 10px;">
              <span class="badge-kv-key" style="padding: 1px 6px; background: #64748b;">{{ c.cluster_name }}</span>
              <span v-if="c.role" class="badge-kv-val" style="padding: 1px 5px; color: #64748b;">{{ c.role }}</span>
            </span>
            <span v-if="!row._selected && (!row.clusters || row.clusters.filter(c => c.cluster_id !== activeCluster?.id).length === 0)" style="color: #94a3b8; font-size: 11px;">未加入集群</span>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 13px; color: #64748b;">
          已勾选 <b style="color: #2563eb; font-size: 15px;">{{ selectedCount }}</b> 台主机加入该集群
        </div>
        <div>
          <el-button @click="visible = false">取消</el-button>
          <el-button type="primary" :loading="saving" :disabled="loading || loadFailed" @click="saveClusterNodes">保存绑定关系</el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { copyToClipboard } from '../utils/clipboard'
import { Search } from 'lucide-vue-next'
import OpsApi from '../api'
import { formatStorageValue, formatStorageUnit } from '../utils'

const props = defineProps({
  metaConfig: { type: Object, required: true }
})
const emit = defineEmits(['saved'])

const visible = ref(false)
const loading = ref(false)
const saving = ref(false)
const activeCluster = ref(null)
const bindEnvFilter = ref('')
const bindKeyword = ref('')
const allHostsList = ref([])
const loadFailed = ref(false)
let loadRequestId = 0

const getEnvLabel = (key) => {
  if (!props.metaConfig?.environments) return key
  const item = props.metaConfig.environments.find(e => e.key === key)
  return item ? item.label : key
}

const getStatusLabel = (key) => {
  if (!props.metaConfig?.host_statuses) return key
  const item = props.metaConfig.host_statuses.find(s => s.key === key)
  return item ? item.label : key
}

const hasClusterRoles = (type) => {
  if (!type || !props.metaConfig?.cluster_types) return false
  const ct = props.metaConfig.cluster_types.find(c => c.key === type)
  return ct && ct.roles && ct.roles.length > 0
}

const activeClusterRoles = computed(() => {
  if (!activeCluster.value?.cluster_type || !props.metaConfig?.cluster_types) return []
  const ct = props.metaConfig.cluster_types.find(c => c.key === activeCluster.value.cluster_type)
  return ct && ct.roles ? ct.roles : []
})

const filteredBindHosts = computed(() => {
  return allHostsList.value.filter(h => {
    const matchEnv = !bindEnvFilter.value || h.env === bindEnvFilter.value
    const kw = bindKeyword.value.trim().toLowerCase()
    const matchKw = !kw || h.hostname?.toLowerCase().includes(kw) || h.private_ip?.toLowerCase().includes(kw)
    return matchEnv && matchKw
  }).sort((a, b) => {
    if (a._selected === b._selected) return 0
    return a._selected ? -1 : 1
  })
})

const selectedCount = computed(() => {
  return allHostsList.value.filter(h => h._selected).length
})

const copyText = async (txt) => {
  if (!txt) return
  if (await copyToClipboard(txt)) {
    ElMessage.success(`已复制: ${txt}`)
  } else {
    ElMessage.error('复制失败，请检查浏览器剪贴板权限')
  }
}

const open = async (c) => {
  const requestId = ++loadRequestId
  activeCluster.value = c
  bindEnvFilter.value = c.env || ''
  bindKeyword.value = ''
  visible.value = true
  loading.value = true
  loadFailed.value = false
  allHostsList.value = []

  try {
    const first = await OpsApi.getHosts({ page: 1, size: 500, sort_by: 'id', sort_order: 'asc' })
    const hosts = [...(first.data?.items || [])]
    const pages = Math.ceil((first.data?.total || 0) / 500)
    for (let page = 2; page <= pages; page++) {
      const res = await OpsApi.getHosts({ page, size: 500, sort_by: 'id', sort_order: 'asc' })
      hosts.push(...(res.data?.items || []))
    }
    if (requestId !== loadRequestId) return
    const currentBoundMap = {}
    ;(c.nodes || []).forEach(n => {
      currentBoundMap[n.host_id] = n.role || ''
    })

    const list = hosts.map(h => ({
      ...h,
      _selected: currentBoundMap[h.id] !== undefined,
      _role: currentBoundMap[h.id] !== undefined ? currentBoundMap[h.id] : (activeClusterRoles.value[0]?.key || '')
    }))

    // 默认已选择的节点置顶排在最前
    list.sort((a, b) => {
      if (a._selected === b._selected) return a.id - b.id
      return a._selected ? -1 : 1
    })

    allHostsList.value = list
  } catch (e) {
    if (requestId === loadRequestId) {
      loadFailed.value = true
      ElMessage.error('加载主机列表失败，请重新打开后再保存')
    }
  } finally {
    if (requestId === loadRequestId) loading.value = false
  }
}

const saveClusterNodes = async () => {
  if (loading.value || loadFailed.value || !activeCluster.value) return
  const selectedNodes = allHostsList.value
    .filter(h => h._selected)
    .map(h => ({ host_id: h.id, role: h._role }))

  saving.value = true
  try {
    await OpsApi.bindClusterHosts(activeCluster.value.id, selectedNodes)
    ElMessage.success('主机资产绑定已保存更新')
    visible.value = false
    emit('saved')
  } catch (e) {
    ElMessage.error('保存节点失败')
  } finally {
    saving.value = false
  }
}

defineExpose({ open })
</script>
