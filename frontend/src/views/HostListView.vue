<template>
  <section class="tab-pane">
    <div class="ops-card">
      <!-- 顶部筛选过滤工具栏 -->
      <div class="filter-bar">
        <div class="filter-group">
          <el-input v-model="hostFilter.keyword" placeholder="搜索主机名/IP/系统/备注" clearable
            @input="handleSearchInput" @clear="handleSearchInput" @keyup.enter="fetchHosts" style="width: 230px;">
            <template #prefix><Search :size="14" style="color: #94a3b8;" /></template>
          </el-input>
          <el-select v-model="hostFilter.env" placeholder="全部环境" clearable @change="fetchHosts" style="width: 110px;">
            <el-option v-for="env in metaConfig.environments" :key="env.key" :label="env.label" :value="env.key" />
          </el-select>
          <el-select v-model="hostFilter.status" placeholder="全部状态" clearable @change="fetchHosts" style="width: 110px;">
            <el-option v-for="st in metaConfig.host_statuses" :key="st.key" :label="st.label" :value="st.key" />
          </el-select>
          <el-select v-model="hostFilter.arch" placeholder="全部架构" clearable @change="fetchHosts" style="width: 110px;">
            <el-option v-for="a in metaConfig.cpu_architectures" :key="a.key" :label="a.label" :value="a.key" />
          </el-select>
          <el-select v-model="hostFilter.cluster_id" placeholder="按归属集群筛选" clearable @change="fetchHosts" style="width: 160px;">
            <el-option v-for="c in clusterList" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <el-button type="primary" @click="fetchHosts">查询</el-button>
          <el-button @click="resetHostFilter">重置</el-button>
        </div>

        <div style="display: flex; gap: 8px;">
          <el-button v-if="selectedHostIds.length > 0" type="danger" plain @click="handleBatchDelete">
            批量删除 ({{ selectedHostIds.length }})
          </el-button>
          <el-button type="success" plain @click="openExportDialog">
            <Download :size="14" style="margin-right: 4px;" />
            {{ selectedHostIds.length > 0 ? `导出选中 (${selectedHostIds.length})` : '导出资产' }}
          </el-button>
          <el-button type="primary" @click="openCreateHostDialog">
            + 新增主机
          </el-button>
        </div>
      </div>

      <!-- 主机表格 (所有字段独立展示，支持多维度排序与同公网IP跨行智能合并) -->
      <el-table :data="hostsData.items" style="width: 100%" max-height="calc(100vh - 245px)"
        :span-method="hostSpanMethod" @selection-change="handleSelectionChange" @sort-change="handleSortChange"
        :default-sort="{ prop: 'id', order: 'descending' }" v-loading="loading">
        
        <el-table-column type="selection" width="45" align="center" fixed="left"></el-table-column>
        
        <el-table-column type="index" label="#" width="55" align="center" fixed="left" :index="(i) => (hostsData.page - 1) * hostsData.size + i + 1">
          <template #default="{ $index }">
            <span style="font-family: 'JetBrains Mono'; font-size: 12px; color: #64748b; font-weight: 600;">
              {{ (hostsData.page - 1) * hostsData.size + $index + 1 }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="hostname" label="主机名" min-width="150" fixed="left" sortable="custom">
          <template #default="{ row }">
            <span style="font-weight: 600; color: #0f172a;">{{ row.hostname }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="private_ip" label="内网IP" min-width="155" fixed="left" sortable="custom">
          <template #default="{ row }">
            <span class="ip-code" @click="copyText(row.private_ip)" title="点击复制">{{ row.private_ip }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="public_ip" label="外网 IP" min-width="260" sortable="custom">
          <template #default="{ row }">
            <div v-if="parsePublicIps(row.public_ip).length > 0" class="public-ip-group-card">
              <span v-for="(ip, idx) in parsePublicIps(row.public_ip)" :key="idx" class="ip-code ip-code-public"
                @click="copyText(ip)" :title="'点击复制: ' + ip">
                {{ ip }}
              </span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="open_ports" label="开放端口" min-width="240" sortable="custom">
          <template #default="{ row }">
            <div v-if="getAllHostPorts(row).length > 0" style="display: flex; flex-wrap: wrap; gap: 4px; align-items: center;">
              <span v-for="(p, idx) in getAllHostPorts(row)" :key="idx"
                class="port-badge" :class="{ 'port-badge-range': isPortRange(p) }"
                @click="copyText(p)" :title="isPortRange(p) ? '点击复制端口范围: ' + p : '点击复制端口: ' + p">
                {{ p }}
              </span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="env" label="环境" width="95" align="center" sortable="custom">
          <template #default="{ row }">
            <span v-if="row.env" class="env-tag" :class="row.env" style="white-space: nowrap; display: inline-block;">{{ getEnvLabel(row.env) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="105" align="center" sortable="custom">
          <template #default="{ row }">
            <span v-if="row.status" class="status-tag"
              :style="{
                backgroundColor: getStatusStyle(row.status, metaConfig).backgroundColor,
                color: getStatusStyle(row.status, metaConfig).color,
                borderColor: getStatusStyle(row.status, metaConfig).borderColor
              }">
              <span class="status-indicator"
                :style="{
                  backgroundColor: getStatusStyle(row.status, metaConfig).dotColor,
                  boxShadow: '0 0 0 2px ' + getStatusStyle(row.status, metaConfig).color + '33'
                }"></span>
              {{ getStatusLabel(row.status) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="cpu_cores" label="CPU" width="80" align="center" sortable="custom">
          <template #default="{ row }">
            <span v-if="row.cpu_cores && row.cpu_cores > 0" style="font-family: 'JetBrains Mono'; font-weight: 600;">{{ row.cpu_cores }} 核</span>
          </template>
        </el-table-column>

        <el-table-column prop="memory_gb" label="内存" width="90" align="center" sortable="custom">
          <template #default="{ row }">
            <span v-if="row.memory_gb && row.memory_gb > 0" style="font-family: 'JetBrains Mono';">{{ formatStorageValue(row.memory_gb) }} {{ formatStorageUnit(row.memory_gb) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="disk_gb" label="数据盘" width="95" align="center" sortable="custom">
          <template #default="{ row }">
            <span v-if="row.disk_gb && row.disk_gb > 0" style="font-family: 'JetBrains Mono'; font-weight: 600;">{{ formatStorageValue(row.disk_gb) }} {{ formatStorageUnit(row.disk_gb) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="arch" label="架构" width="85" align="center" sortable="custom">
          <template #default="{ row }">
            <el-tag v-if="row.arch" size="small" :type="row.arch === 'arm64' ? 'warning' : 'info'" style="font-family: 'JetBrains Mono';">
              {{ getArchLabel(row.arch) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="os" label="操作系统" min-width="140" show-overflow-tooltip sortable="custom">
          <template #default="{ row }">
            <span v-if="row.os" style="font-size: 13px; font-weight: 500; color: #334155;">{{ row.os }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="kernel_version" label="内核版本" width="115" align="center" sortable="custom">
          <template #default="{ row }">
            <el-tooltip v-if="row.kernel_version" :content="row.kernel_version" placement="top" effect="dark">
              <span class="kernel-badge">{{ getCleanKernel(row.kernel_version) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column label="所属服务" min-width="260">
          <template #default="{ row }">
            <div v-if="row.clusters && row.clusters.length > 0" style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center;">
              <div
                v-for="c in row.clusters"
                :key="c.cluster_id"
                class="badge-stack"
                @mouseenter="(e) => handleServiceBadgeHover(e, c)"
                @click="emit('filter-cluster', c.cluster_id)"
              >
                <span v-html="getMiddlewareLogo(c.cluster_type, 16)"></span>
                <div class="badge-kv">
                  <span class="badge-kv-key">{{ c.cluster_type || c.cluster_name }}</span>
                  <span v-if="getServiceVersionLabel(c)" class="badge-kv-val badge-kv-version">{{ getServiceVersionLabel(c) }}</span>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="notes" label="备注" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.notes" style="color: #64748b; font-size: 12px;">{{ row.notes }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="updated_at" label="更新时间" width="120" align="center">
          <template #default="{ row }">
            <span style="font-size: 11px; color: #64748b; font-family: 'JetBrains Mono';">
              {{ formatDateTime(row.updated_at || row.created_at).slice(5, 16) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="115" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEditHostDialog(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDeleteHost(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页栏 -->
      <div style="margin-top: 16px; display: flex; justify-content: space-between; align-items: center; background: #ffffff; padding: 10px 16px; border-radius: 8px; border: 1px solid #e2e8f0; flex-wrap: wrap; gap: 8px;">
        <div style="font-size: 13px; color: var(--text-sub);">
          共检索到 <b style="color: #2563eb;">{{ hostsData.total }}</b> 台主机资产
        </div>
        <el-pagination v-model:current-page="hostsData.page" v-model:page-size="hostsData.size"
          :page-sizes="[10, 20, 50, 100]" :total="hostsData.total"
          layout="total, sizes, prev, pager, next, jumper" @size-change="handleSizeChange"
          @current-change="fetchHosts"></el-pagination>
      </div>
    </div>

    <!-- 全局单例服务悬停详情卡片 (彻底消除数百个 Popover 实例引起的 DOM 渲染卡顿) -->
    <el-popover
      :virtual-ref="hoveredServiceRef"
      virtual-triggering
      trigger="hover"
      placement="top-start"
      :width="280"
      :show-after="80"
      popper-class="service-card-popover"
    >
      <div v-if="hoveredCluster" class="service-popover-card">
        <div class="spc-header">
          <div class="spc-title-box">
            <span v-html="getMiddlewareLogo(hoveredCluster.cluster_type, 20)"></span>
            <span class="spc-name">{{ hoveredCluster.cluster_name || hoveredCluster.cluster_type }}</span>
          </div>
          <span v-if="hoveredCluster.env" class="env-tag" :class="hoveredCluster.env" style="font-size: 10px; padding: 1px 6px;">{{ getEnvLabel(hoveredCluster.env) }}</span>
        </div>

        <div class="spc-body">
          <div class="spc-row">
            <span class="spc-label">组件类型</span>
            <span class="spc-value">{{ hoveredCluster.cluster_type }}</span>
          </div>
          <div v-if="hoveredCluster.cluster_version || hoveredCluster.version" class="spc-row">
            <span class="spc-label">软件版本</span>
            <span class="spc-value spc-code">{{ hoveredCluster.cluster_version || hoveredCluster.version }}</span>
          </div>
          <div v-if="hoveredCluster.role && hoveredCluster.role !== '无'" class="spc-row">
            <span class="spc-label">节点角色</span>
            <span class="spc-role-tag">{{ hoveredCluster.role }}</span>
          </div>
          <div v-if="hoveredCluster.port" class="spc-row">
            <span class="spc-label">服务端口</span>
            <span class="spc-value spc-code">{{ hoveredCluster.port }}</span>
          </div>
          <div v-if="hoveredCluster.description" class="spc-row">
            <span class="spc-label">服务描述</span>
            <span class="spc-value" style="color: #64748b; font-size: 11.5px;">{{ hoveredCluster.description }}</span>
          </div>
        </div>

        <div class="spc-footer" @click="emit('filter-cluster', hoveredCluster.cluster_id)">
          <span>查看集群拓扑</span>
          <ChevronRight :size="14" />
        </div>
      </div>
    </el-popover>

    <!-- 新增/编辑主机弹窗 -->
    <HostFormDialog ref="hostFormDialogRef" :meta-config="metaConfig" @saved="fetchHosts" />

    <!-- 资产导出与实时预览弹窗 -->
    <HostExportDialog ref="hostExportDialogRef" :meta-config="metaConfig" />
  </section>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, ChevronRight, Download } from 'lucide-vue-next'
import OpsApi from '../api'
import {
  formatDateTime,
  formatStorageValue,
  formatStorageUnit,
  getShortKernel,
  getCleanKernel,
  parsePublicIps,
  parsePorts,
  isPortRange,
  getMiddlewareLogo,
  getStatusStyle,
  getEnvLabel as getEnvLabelUtil,
  getStatusLabel as getStatusLabelUtil,
  getArchLabel as getArchLabelUtil
} from '../utils'
import HostFormDialog from '../components/HostFormDialog.vue'
import HostExportDialog from '../components/HostExportDialog.vue'

const props = defineProps({
  metaConfig: { type: Object, required: true },
  clusterList: { type: Array, required: true }
})
const emit = defineEmits(['filter-cluster', 'data-changed'])

const loading = ref(false)
const hostFormDialogRef = ref(null)
const hostExportDialogRef = ref(null)
const selectedHostIds = ref([])

const openExportDialog = () => {
  hostExportDialogRef.value?.open({
    filters: hostFilter,
    ids: selectedHostIds.value
  })
}

// 单例虚拟 Popover 驱动状态
const hoveredServiceRef = ref()
const hoveredCluster = ref(null)

const handleServiceBadgeHover = (e, cluster) => {
  hoveredServiceRef.value = e.currentTarget
  hoveredCluster.value = cluster
}

const hostsData = reactive({
  total: 0,
  page: 1,
  size: 50,
  items: []
})

const hostFilter = reactive({
  keyword: '',
  env: '',
  status: '',
  arch: '',
  cluster_id: null,
  sort_by: 'id',
  sort_order: 'desc'
})

const getEnvLabel = (key) => getEnvLabelUtil(key, props.metaConfig)
const getArchLabel = (key) => getArchLabelUtil(key, props.metaConfig)
const getStatusLabel = (key) => getStatusLabelUtil(key, props.metaConfig)

const copyText = (txt) => {
  if (!txt) return
  navigator.clipboard.writeText(txt).then(() => {
    ElMessage.success(`已复制: ${txt}`)
  })
}

const getServiceVersionLabel = (c) => {
  const v = c.cluster_version || c.version || ''
  if (!v) return ''
  return v.startsWith('v') || v.startsWith('V') ? v : `v${v}`
}

const getServiceDetailTitle = (c) => {
  const parts = []
  if (c.cluster_name) parts.push(`服务: ${c.cluster_name}`)
  if (c.cluster_type) parts.push(`类型: ${c.cluster_type}`)
  if (c.cluster_version || c.version) parts.push(`版本: ${c.cluster_version || c.version}`)
  if (c.role && c.role !== '无') parts.push(`角色: ${c.role}`)
  if (c.port) parts.push(`端口: ${c.port}`)
  return parts.join(' | ')
}

const getAllHostPorts = (row) => {
  const portsSet = new Set()
  if (row.open_ports) {
    parsePorts(row.open_ports).forEach(p => portsSet.add(p))
  }
  if (Array.isArray(row.clusters)) {
    row.clusters.forEach(c => {
      if (c.port) {
        parsePorts(c.port).forEach(p => portsSet.add(p))
      }
    })
  }
  return Array.from(portsSet)
}

const getHostDisplayPorts = (row) => {
  const allPorts = getAllHostPorts(row)
  const raw = allPorts.join(', ')
  if (allPorts.length <= 4) {
    return { ports: allPorts, moreCount: 0, raw }
  }
  return {
    ports: allPorts.slice(0, 3),
    moreCount: allPorts.length - 3,
    raw
  }
}

// 跨行智能合并公网 IP
const hostSpanMethod = ({ row, column, rowIndex, columnIndex }) => {
  if (column && column.property === 'public_ip') {
    const pubIp = (row.public_ip || '').trim()
    if (!pubIp) return { rowspan: 1, colspan: 1 }

    const items = hostsData.items
    const prevRow = items[rowIndex - 1]
    if (prevRow && (prevRow.public_ip || '').trim() === pubIp) {
      return { rowspan: 0, colspan: 0 }
    }

    let rowspan = 1
    for (let i = rowIndex + 1; i < items.length; i++) {
      if ((items[i].public_ip || '').trim() === pubIp) {
        rowspan++
      } else {
        break
      }
    }
    return { rowspan, colspan: 1 }
  }
  return { rowspan: 1, colspan: 1 }
}

const handleSelectionChange = (selection) => {
  selectedHostIds.value = selection.map(item => item.id)
}

const handleSortChange = ({ prop, order }) => {
  if (!order) {
    hostFilter.sort_by = 'id'
    hostFilter.sort_order = 'desc'
  } else {
    hostFilter.sort_by = prop || 'id'
    hostFilter.sort_order = order === 'ascending' ? 'asc' : 'desc'
  }
  hostsData.page = 1
  fetchHosts()
}

const handleSizeChange = (val) => {
  hostsData.size = val
  hostsData.page = 1
  fetchHosts()
}

const resetHostFilter = () => {
  Object.assign(hostFilter, {
    keyword: '',
    env: '',
    status: '',
    arch: '',
    cluster_id: null,
    sort_by: 'id',
    sort_order: 'desc'
  })
  hostsData.page = 1
  fetchHosts()
}

let searchTimer = null
const handleSearchInput = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    hostsData.page = 1
    fetchHosts(true)
  }, 250)
}

const fetchHosts = async (silent = false) => {
  if (!silent || hostsData.items.length === 0) loading.value = true
  try {
    const params = {
      page: hostsData.page,
      size: hostsData.size,
      keyword: hostFilter.keyword || undefined,
      env: hostFilter.env || undefined,
      status: hostFilter.status || undefined,
      arch: hostFilter.arch || undefined,
      cluster_id: hostFilter.cluster_id || undefined,
      sort_by: hostFilter.sort_by || undefined,
      order: hostFilter.sort_order || undefined,
      sort_order: hostFilter.sort_order || undefined
    }
    const res = await OpsApi.getHosts(params)
    hostsData.total = res.data.total
    hostsData.items = res.data.items || []
  } catch (e) {
    if (!silent) ElMessage.error('获取主机列表失败')
  } finally {
    loading.value = false
  }
}

const openCreateHostDialog = () => {
  hostFormDialogRef.value?.open()
}

const openEditHostDialog = (row) => {
  hostFormDialogRef.value?.open(row)
}

const handleDeleteHost = (row) => {
  ElMessageBox.confirm(`确定要彻底删除主机【${row.hostname} (${row.private_ip})】吗？`, '危险删除确认', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await OpsApi.deleteHost(row.id)
      ElMessage.success('主机资产已彻底删除')
      fetchHosts()
      emit('data-changed')
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }).catch(() => {})
}

const handleBatchDelete = () => {
  if (selectedHostIds.value.length === 0) return
  ElMessageBox.confirm(`已选中 ${selectedHostIds.value.length} 台主机，确认批量删除吗？`, '批量删除警告', {
    confirmButtonText: '确认批量删除',
    cancelButtonText: '取消',
    type: 'danger'
  }).then(async () => {
    try {
      const res = await OpsApi.batchDeleteHosts(selectedHostIds.value)
      ElMessage.success(`批量删除成功，已删除 ${res.data.deleted_count} 台主机`)
      selectedHostIds.value = []
      fetchHosts()
      emit('data-changed')
    } catch (e) {
      ElMessage.error('批量删除失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  fetchHosts()
})

defineExpose({ fetchHosts })
</script>
