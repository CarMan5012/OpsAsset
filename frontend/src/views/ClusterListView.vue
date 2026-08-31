<template>
  <section class="tab-pane">
    <div class="ops-card">
      <!-- 顶部工具栏: 标题、搜索、多维过滤与视图模式切换 -->
      <div class="filter-bar">
        <div class="filter-group">
          <div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-right: 8px; display: flex; align-items: center; gap: 6px;">
            <Layers :size="16" style="color: #2563eb;" /> 服务与集群拓扑
          </div>
          <el-input v-model="clusterFilter.keyword" placeholder="搜索服务与集群名称/描述" clearable
            @input="clusterPagination.page = 1" style="width: 220px;">
            <template #prefix><Search :size="14" style="color: #94a3b8;" /></template>
          </el-input>
          <el-select v-model="clusterFilter.env" placeholder="全部环境" clearable style="width: 115px;">
            <el-option v-for="env in metaConfig.environments" :key="env.key" :label="env.label" :value="env.key" />
          </el-select>
          <el-select v-model="clusterFilter.cluster_type" placeholder="全部组件" clearable style="width: 125px;">
            <el-option v-for="ct in metaConfig.cluster_types" :key="ct.key" :label="ct.label" :value="ct.key" />
          </el-select>
        </div>

        <div style="display: flex; align-items: center; gap: 12px;">
          <!-- 双视图模式切换单选按钮组 -->
          <el-radio-group v-model="clusterViewMode" size="default" class="view-mode-btn-group" @change="onViewModeChange">
            <el-radio-button label="table">
              <span style="display: inline-flex; align-items: center; gap: 4px;"><Table :size="13" /> 表格视图</span>
            </el-radio-button>
            <el-radio-button label="card">
              <span style="display: inline-flex; align-items: center; gap: 4px;"><LayoutGrid :size="13" /> 卡片视图</span>
            </el-radio-button>
          </el-radio-group>

          <el-button type="primary" @click="openCreateClusterDialog">+ 创建新服务/集群</el-button>
        </div>
      </div>

      <!-- 中间件分类快捷胶囊过滤栏 (带数量角标，点击一键筛选) -->
      <div v-if="clusterTypeChips.length > 0" class="cluster-chips-bar">
        <div class="cluster-chip" :class="{ active: clusterFilter.cluster_type === '' }" @click="selectClusterTypeChip('')">
          <span>全部组件</span>
          <span class="chip-count">{{ clusterList.length }}</span>
        </div>
        <div v-for="chip in clusterTypeChips" :key="chip.key"
          class="cluster-chip" :class="{ active: clusterFilter.cluster_type === chip.key }"
          @click="selectClusterTypeChip(chip.key)">
          <span v-html="getMiddlewareLogo(chip.key, 14)"></span>
          <span>{{ chip.label }}</span>
          <span class="chip-count">{{ chip.count }}</span>
        </div>
      </div>

      <!-- 1. 表格视图 (Table View - 高信息密度一览) -->
      <div v-if="clusterViewMode === 'table'" style="margin-top: 16px;">
        <el-table ref="clustersTableRef" :data="pagedClusterList" stripe style="width: 100%" v-loading="loading"
          @sort-change="handleClusterSortChange" :default-sort="{ prop: 'id', order: 'ascending' }">
          <el-table-column prop="id" label="ID" width="70" align="center" sortable="custom"></el-table-column>
          <el-table-column prop="name" label="集群/服务名称" min-width="180" show-overflow-tooltip sortable="custom">
            <template #default="{ row }">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span v-html="getMiddlewareLogo(row.cluster_type, 18)"></span>
                <b style="color: #0f172a; cursor: pointer;" @click="openViewNodesDialog(row)" title="点击查看节点明细">{{ row.name }}</b>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="cluster_type" label="类型 / 版本" min-width="180" sortable="custom">
            <template #default="{ row }">
              <div style="display: flex; align-items: center; gap: 6px; white-space: nowrap;">
                <el-tag size="small" type="info" style="font-weight: 600; font-family: 'JetBrains Mono';">
                  {{ getClusterTypeLabel(row.cluster_type) }}
                </el-tag>
                <span v-if="row.version" style="font-size: 11.5px; font-family: 'JetBrains Mono'; color: #2563eb; background: #eff6ff; border: 1px solid #dbeafe; padding: 1.5px 6px; border-radius: 4px; font-weight: 600;">
                  {{ row.version }}
                </span>
                <span v-else style="color: #94a3b8; font-size: 11px;">未填版本</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="port" label="服务端口" min-width="180" sortable="custom">
            <template #default="{ row }">
              <div v-if="parsePorts(row.port).length > 0" style="display: flex; flex-wrap: wrap; gap: 4px; align-items: center;">
                <span v-for="(p, pidx) in parsePorts(row.port)" :key="pidx"
                  class="port-badge" :class="{ 'port-badge-range': isPortRange(p) }"
                  @click="copyText(p)" :title="isPortRange(p) ? '点击复制端口范围: ' + p : '点击复制端口: ' + p">
                  {{ p }}
                </span>
              </div>
              <span v-else style="color: #cbd5e1; font-size: 12px;">未配置</span>
            </template>
          </el-table-column>
          <el-table-column prop="env" label="环境" width="95" align="center" sortable="custom">
            <template #default="{ row }">
              <span class="env-tag" :class="row.env">{{ getEnvLabel(row.env) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="node_count" label="关联节点" width="105" align="center" sortable="custom">
            <template #default="{ row }">
              <b style="color: #2563eb; font-size: 14px; cursor: pointer;" @click="openViewNodesDialog(row)" title="点击查看节点明细">
                {{ row.node_count || (row.nodes ? row.nodes.length : 0) }} 台
              </b>
            </template>
          </el-table-column>
          <el-table-column label="关联主机节点预览" min-width="320">
            <template #default="{ row }">
              <div v-if="row.nodes && row.nodes.length > 0" style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center; padding: 3px 0;">
                <div v-for="n in row.nodes.slice(0, 3)" :key="n.host_id"
                  style="font-size: 11.5px; background: #ffffff; padding: 3px 7px; border-radius: 4px; border: 1px solid #cbd5e1; display: inline-flex; align-items: center; gap: 5px; cursor: pointer; box-shadow: 0 1px 2px rgba(0,0,0,0.02);"
                  @click="openViewNodesDialog(row)" title="点击查看节点明细">
                  <span style="color: #0f172a; font-weight: 600; font-family: 'JetBrains Mono', monospace;">{{ n.hostname }}</span>
                  <span style="font-family: 'JetBrains Mono', monospace; font-size: 10.5px; color: #2563eb; background: #eff6ff; padding: 0 4px; border-radius: 3px;">{{ n.private_ip }}</span>
                </div>
                <el-button v-if="row.nodes.length > 3" link type="primary" size="small" @click="openViewNodesDialog(row)" style="font-weight: 600; font-size: 11.5px; padding: 0 2px;">
                  +{{ row.nodes.length - 3 }}台
                </el-button>
              </div>
              <span v-else style="color: #94a3b8; font-size: 12px;">未绑定节点</span>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" width="120" align="center">
            <template #default="{ row }">
              <span style="font-size: 11px; color: #64748b; font-family: 'JetBrains Mono';">
                {{ formatDateTime(row.updated_at || row.created_at).slice(5, 16) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="190" align="center" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openViewNodesDialog(row)">明细</el-button>
              <el-button link type="primary" size="small" @click="openBindNodeDialog(row)">调整节点</el-button>
              <el-divider direction="vertical" style="margin: 0 3px;"></el-divider>
              <el-button link type="primary" size="small" @click="openEditClusterDialog(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleDeleteCluster(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 2. 卡片视图 (Card View - 1:1 保持原版完整卡片细节) -->
      <div v-else style="margin-top: 16px;" v-loading="loading">
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(460px, 1fr)); gap: 20px; min-height: 200px;">
          <div v-for="c in pagedClusterList" :key="c.id" class="ops-card cluster-card"
            style="display: flex; flex-direction: column; justify-content: space-between; border-radius: 12px; padding: 20px 22px;">
            <div>
              <!-- 卡片头部: 标题与右侧标签组 -->
              <div style="display: flex; justify-content: space-between; align-items: center; gap: 14px;">
                <div style="flex: 1; min-width: 0;">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <span v-html="getMiddlewareLogo(c.cluster_type, 18)" style="display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; line-height: 1;"></span>
                    <h4 style="color: #0f172a; font-size: 16px; font-weight: 700; margin: 0; line-height: 1.2; word-break: break-all;" :title="c.name">
                      {{ c.name }}
                    </h4>
                    <!-- 悬浮解释业务描述 -->
                    <el-tooltip :content="c.description || '暂无业务描述'" placement="top" effect="dark">
                      <span style="display: inline-flex; align-items: center; justify-content: center; width: 15px; height: 15px; border-radius: 50%; background: #f1f5f9; color: #64748b; font-size: 10px; font-weight: 700; cursor: pointer; border: 1px solid #cbd5e1; font-family: monospace; line-height: 1; flex-shrink: 0;" title="悬停查看业务描述">
                        !
                      </span>
                    </el-tooltip>
                  </div>
                </div>
                <div style="display: flex; gap: 8px; align-items: center; flex-shrink: 0; white-space: nowrap;">
                  <span class="env-tag" :class="c.env">{{ getEnvLabel(c.env) }}</span>
                  <div class="badge-kv">
                    <span class="badge-kv-key">{{ c.cluster_type }}</span>
                    <span v-if="c.version" class="badge-kv-val">{{ c.version }}</span>
                  </div>
                </div>
              </div>

              <!-- 核心节点与服务端口指标条 -->
              <div style="margin-top: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 14px; display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #475569;">
                <div style="display: flex; align-items: center; gap: 6px;">
                  <span style="font-weight: 600; color: #0f172a;">关联节点: <b style="color: #2563eb; font-size: 14px;">{{ c.node_count || (c.nodes ? c.nodes.length : 0) }}</b> 台</span>
                </div>
                <div v-if="parsePorts(c.port).length > 0" style="display: flex; flex-wrap: wrap; gap: 4px; align-items: center;">
                  <span v-for="(p, pidx) in parsePorts(c.port)" :key="pidx"
                    class="port-badge" :class="{ 'port-badge-range': isPortRange(p) }"
                    @click="copyText(p)" :title="isPortRange(p) ? '点击复制端口范围: ' + p : '点击复制端口: ' + p">
                    {{ p }}
                  </span>
                </div>
              </div>

              <!-- 节点药丸预览: 主机名 + 内网 IP -->
              <div style="margin-top: 12px; min-height: 38px;">
                <div v-if="c.nodes && c.nodes.length > 0" style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">
                  <div v-for="n in c.nodes.slice(0, 8)" :key="n.host_id"
                    style="font-size: 12px; background: #ffffff; padding: 4px 9px; border-radius: 6px; border: 1px solid #cbd5e1; display: inline-flex; align-items: center; gap: 6px; cursor: pointer; transition: all 0.15s; box-shadow: 0 1px 2px rgba(0,0,0,0.03);"
                    @click="openViewNodesDialog(c)" title="点击查看节点详细配置与网络信息">
                    <span style="color: #0f172a; font-weight: 600; font-family: 'JetBrains Mono', monospace;">{{ n.hostname }}</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #2563eb; background: #eff6ff; padding: 1px 5px; border-radius: 3px;">{{ n.private_ip }}</span>
                    <span v-if="n.role && n.role !== '无'" class="role-badge"
                      :class="n.role.toLowerCase().includes('master') || n.role.toLowerCase().includes('primary') || n.role.includes('主') ? 'role-master' : 'role-worker'"
                      style="font-size: 10px; padding: 0 4px;">{{ n.role }}</span>
                  </div>
                  <el-button v-if="c.nodes.length > 8" link type="primary" size="small" @click="openViewNodesDialog(c)" style="font-weight: 600;">
                    +{{ c.nodes.length - 8 }} 台更多...
                  </el-button>
                </div>
                <div v-else style="color: #94a3b8; font-size: 12px; padding: 6px 0;">
                  尚未关联任何主机节点，可点击下方【调整节点】进行绑定
                </div>
              </div>
            </div>

            <!-- 卡片底部操作栏 -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f1f5f9; padding-top: 12px; margin-top: 16px;">
              <span style="font-size: 11px; color: #94a3b8; font-family: 'JetBrains Mono';">
                更新于: {{ formatDateTime(c.updated_at || c.created_at) }}
              </span>
              <div style="display: flex; gap: 4px; align-items: center;">
                <el-button link type="primary" size="small" @click="openViewNodesDialog(c)">查看明细</el-button>
                <el-button link type="primary" size="small" @click="openBindNodeDialog(c)">调整节点</el-button>
                <el-divider direction="vertical" style="margin: 0 4px;"></el-divider>
                <el-button link type="primary" size="small" @click="openEditClusterDialog(c)">编辑</el-button>
                <el-button link type="danger" size="small" @click="handleDeleteCluster(c)">删除</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空数据状态 -->
      <div v-if="filteredClusterList.length === 0 && !loading" style="padding: 40px 0; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; margin-top: 16px;">
        <el-empty description="暂无符合条件的服务或集群数据"></el-empty>
      </div>

      <!-- 分页器 -->
      <div v-if="filteredClusterList.length > 0"
        style="margin-top: 16px; display: flex; justify-content: space-between; align-items: center; background: #ffffff; padding: 10px 16px; border-radius: 8px; border: 1px solid #e2e8f0; flex-wrap: wrap; gap: 8px;">
        <div style="font-size: 13px; color: var(--text-sub);">
          共检索到 <b style="color: #2563eb;">{{ filteredClusterList.length }}</b> 个服务与集群
        </div>
        <el-pagination v-model:current-page="clusterPagination.page" v-model:page-size="clusterPagination.size"
          :page-sizes="[12, 24, 48, 100]" :total="filteredClusterList.length"
          layout="total, sizes, prev, pager, next, jumper"></el-pagination>
      </div>
    </div>

    <!-- 弹窗组件 -->
    <ClusterFormDialog ref="clusterFormDialogRef" :meta-config="metaConfig" @saved="handleClusterSaved" />
    <BindHostModal ref="bindHostModalRef" :meta-config="metaConfig" @saved="handleClusterSaved" />
    <ViewNodesModal ref="viewNodesModalRef" :meta-config="metaConfig" @switch-to-bind="openBindNodeDialog" />
  </section>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Layers, Search, Table, LayoutGrid } from 'lucide-vue-next'
import OpsApi from '../api'
import {
  formatDateTime,
  parsePorts,
  isPortRange,
  getMiddlewareLogo
} from '../utils'
import ClusterFormDialog from '../components/ClusterFormDialog.vue'
import BindHostModal from '../components/BindHostModal.vue'
import ViewNodesModal from '../components/ViewNodesModal.vue'

const props = defineProps({
  metaConfig: { type: Object, required: true },
  clusterList: { type: Array, required: true },
  loading: { type: Boolean, default: false }
})
const emit = defineEmits(['data-changed', 'refresh'])

const clusterViewMode = ref(localStorage.getItem('ops_asset_cluster_view_mode') || 'table')
const onViewModeChange = (val) => {
  localStorage.setItem('ops_asset_cluster_view_mode', val)
}

const clusterPagination = reactive({ page: 1, size: 12 })
const clusterSort = reactive({ prop: 'id', order: 'ascending' })
const clusterFilter = reactive({ keyword: '', env: '', cluster_type: '' })

const clusterFormDialogRef = ref(null)
const bindHostModalRef = ref(null)
const viewNodesModalRef = ref(null)

const getEnvLabel = (key) => {
  if (!props.metaConfig?.environments) return key
  const item = props.metaConfig.environments.find(e => e.key === key)
  return item ? item.label : key
}

const getClusterTypeLabel = (key) => {
  if (!props.metaConfig?.cluster_types) return key
  const item = props.metaConfig.cluster_types.find(c => c.key === key)
  return item ? item.label : key
}

const copyText = (txt) => {
  if (!txt) return
  navigator.clipboard.writeText(txt).then(() => {
    ElMessage.success(`已复制: ${txt}`)
  })
}

// 快捷分类胶囊列表
const clusterTypeChips = computed(() => {
  const rawList = props.clusterList || []
  const countMap = {}
  rawList.forEach(c => {
    if (c.cluster_type) {
      countMap[c.cluster_type] = (countMap[c.cluster_type] || 0) + 1
    }
  })

  const chips = []
  const seen = new Set()

  ;(props.metaConfig?.cluster_types || []).forEach(ct => {
    const count = countMap[ct.key] || 0
    if (count > 0) {
      chips.push({ key: ct.key, label: ct.label || ct.key, count })
      seen.add(String(ct.key).toLowerCase())
    }
  })

  Object.entries(countMap).forEach(([k, count]) => {
    if (!seen.has(String(k).toLowerCase()) && count > 0) {
      chips.push({ key: k, label: k, count })
    }
  })

  return chips
})

const selectClusterTypeChip = (key) => {
  if (clusterFilter.cluster_type === key) {
    clusterFilter.cluster_type = ''
  } else {
    clusterFilter.cluster_type = key
  }
  clusterPagination.page = 1
}

const handleClusterSortChange = ({ prop, order }) => {
  if (!order) {
    clusterSort.prop = 'id'
    clusterSort.order = 'ascending'
  } else {
    clusterSort.prop = prop || 'id'
    clusterSort.order = order || 'ascending'
  }
  clusterPagination.page = 1
}

// 过滤与排序后的集群列表
const filteredClusterList = computed(() => {
  const list = (props.clusterList || []).filter(c => {
    if (clusterFilter.env && c.env !== clusterFilter.env) return false
    if (clusterFilter.cluster_type && c.cluster_type !== clusterFilter.cluster_type) return false
    if (clusterFilter.keyword) {
      const kw = clusterFilter.keyword.trim().toLowerCase()
      const matchName = c.name?.toLowerCase().includes(kw)
      const matchType = c.cluster_type?.toLowerCase().includes(kw)
      const matchDesc = c.description?.toLowerCase().includes(kw)
      if (!matchName && !matchType && !matchDesc) return false
    }
    return true
  })

  if (clusterSort.prop) {
    const isDesc = clusterSort.order === 'descending'
    list.sort((a, b) => {
      if (clusterSort.prop === 'id') {
        const valA = Number(a.id) || 0
        const valB = Number(b.id) || 0
        return isDesc ? valB - valA : valA - valB
      } else if (clusterSort.prop === 'node_count') {
        const valA = Number(a.node_count ?? (a.nodes ? a.nodes.length : 0)) || 0
        const valB = Number(b.node_count ?? (b.nodes ? b.nodes.length : 0)) || 0
        return isDesc ? valB - valA : valA - valB
      } else {
        const valA = String(a[clusterSort.prop] || '').toLowerCase()
        const valB = String(b[clusterSort.prop] || '').toLowerCase()
        if (valA < valB) return isDesc ? 1 : -1
        if (valA > valB) return isDesc ? -1 : 1
        return 0
      }
    })
  }
  return list
})

// 分页切片
const pagedClusterList = computed(() => {
  const start = (clusterPagination.page - 1) * clusterPagination.size
  return filteredClusterList.value.slice(start, start + clusterPagination.size)
})

const openCreateClusterDialog = () => {
  clusterFormDialogRef.value?.open()
}

const openEditClusterDialog = (row) => {
  clusterFormDialogRef.value?.open(row)
}

const openBindNodeDialog = (cluster) => {
  bindHostModalRef.value?.open(cluster)
}

const openViewNodesDialog = (cluster) => {
  viewNodesModalRef.value?.open(cluster)
}

const handleClusterSaved = () => {
  emit('data-changed')
}

const handleDeleteCluster = (row) => {
  ElMessageBox.confirm(`确定要删除集群【${row.name}】吗？删除后其纳管节点的绑定关系将被解除。`, '删除确认', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await OpsApi.deleteCluster(row.id)
      ElMessage.success('集群删除成功')
      emit('data-changed')
    } catch (e) {
      ElMessage.error('删除集群失败')
    }
  }).catch(() => {})
}

const filterByClusterId = (clusterId) => {
  if (!clusterId) return
  const target = props.clusterList.find(c => c.id === clusterId)
  if (target) {
    clusterFilter.keyword = target.name
    clusterFilter.env = ''
    clusterFilter.cluster_type = ''
    clusterPagination.page = 1
    // 自动打开节点弹窗
    openViewNodesDialog(target)
  }
}

defineExpose({
  openCreateClusterDialog,
  openEditClusterDialog,
  openBindNodeDialog,
  openViewNodesDialog,
  filterByClusterId
})
</script>

