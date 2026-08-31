<template>
  <el-dialog v-model="visible" :title="'服务与集群节点资产全景明细 - ' + (selectedViewCluster?.name || '')" width="1280px" top="3vh" append-to-body destroy-on-close>
    <!-- 顶部集群基本信息与 4 大核心指标卡 -->
    <div style="margin-bottom: 18px;">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
        <div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span v-html="getMiddlewareLogo(selectedViewCluster?.cluster_type, 20)" style="display: inline-flex; align-items: center;"></span>
            <span style="font-size: 17px; font-weight: 700; color: #0f172a;">{{ selectedViewCluster?.name }}</span>
          </div>
          <div style="color: #64748b; font-size: 13px; margin-top: 4px;">
            {{ selectedViewCluster?.description || '暂无业务描述' }}
          </div>
        </div>
        <div style="display: flex; gap: 8px; align-items: center; white-space: nowrap;">
          <span v-if="selectedViewCluster?.port" class="port-badge" :class="{ 'port-badge-range': isPortRange(selectedViewCluster?.port) }" style="font-size: 11px; padding: 2px 7px;">
            <DoorOpen :size="12" style="color: #0d9488;" />
            端口: {{ selectedViewCluster?.port }}
          </span>
          <span class="env-tag" :class="selectedViewCluster?.env">{{ getEnvLabel(selectedViewCluster?.env) }}</span>
          <div class="badge-kv">
            <span class="badge-kv-key">{{ selectedViewCluster?.cluster_type }}</span>
            <span v-if="selectedViewCluster?.version" class="badge-kv-val">{{ selectedViewCluster.version }}</span>
          </div>
        </div>
      </div>

      <!-- 4 张高精度资源汇总卡 -->
      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;">
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px;">
          <div style="font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 5px;"><Server :size="13" /> 关联节点总量</div>
          <div style="font-size: 20px; font-weight: 700; color: #2563eb; margin-top: 4px;">
            {{ selectedViewCluster?.nodes?.length || 0 }} <span style="font-size: 12px; color: #64748b; font-weight: normal;">台</span>
          </div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px;">
          <div style="font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 5px;"><Cpu :size="13" /> 集群 CPU 总核数</div>
          <div style="font-size: 20px; font-weight: 700; color: #0f172a; margin-top: 4px; font-family: 'JetBrains Mono', monospace;">
            {{ clusterSummary.totalCpu }} <span style="font-size: 12px; color: #64748b; font-weight: normal;">核</span>
          </div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px;">
          <div style="font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 5px;"><Database :size="13" /> 集群内存总容量</div>
          <div style="font-size: 20px; font-weight: 700; color: #0f172a; margin-top: 4px; font-family: 'JetBrains Mono', monospace;">
            {{ formatStorageFull(clusterSummary.totalMem) }}
          </div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px;">
          <div style="font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 5px;"><HardDrive :size="13" /> 集群数据盘总容量</div>
          <div style="font-size: 20px; font-weight: 700; color: #0f172a; margin-top: 4px; font-family: 'JetBrains Mono', monospace;">
            {{ formatStorageFull(clusterSummary.totalDisk) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 节点过滤栏与全量明细表格 -->
    <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
      <div style="font-weight: 600; font-size: 14px; color: #0f172a;">
        节点列表资产明细 (匹配到 {{ filteredViewNodes.length }} / {{ selectedViewCluster?.nodes?.length || 0 }} 台)
      </div>
      <div style="display: flex; gap: 8px; align-items: center;">
        <el-input v-model="keyword" placeholder="过滤主机名/内网IP/公网IP/系统" size="small" clearable style="width: 260px;">
          <template #prefix><Search :size="14" style="color: #94a3b8;" /></template>
        </el-input>
      </div>
    </div>

    <el-table :data="filteredViewNodes" stripe border max-height="460px" style="width: 100%;">
      <el-table-column type="index" label="#" width="50" align="center" fixed="left"></el-table-column>

      <el-table-column prop="hostname" label="主机名" min-width="150" fixed="left" sortable>
        <template #default="{ row }">
          <span style="font-weight: 600; color: #0f172a;">{{ row.hostname }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="private_ip" label="内网 IP" min-width="140" fixed="left" sortable>
        <template #default="{ row }">
          <span class="ip-code" @click="copyText(row.private_ip)" title="点击复制">{{ row.private_ip }}</span>
        </template>
      </el-table-column>

      <el-table-column v-if="hasClusterRoles(selectedViewCluster?.cluster_type)" prop="role" label="节点角色" width="130" align="center" fixed="left">
        <template #default="{ row }">
          <span v-if="row.role && row.role !== '无'" class="role-badge"
            :class="row.role.toLowerCase().includes('master') || row.role.toLowerCase().includes('primary') || row.role.includes('主') ? 'role-master' : 'role-worker'">
            {{ row.role }}
          </span>
          <span v-else style="color: #cbd5e1; font-size: 11px;">默认工作节点</span>
        </template>
      </el-table-column>

      <el-table-column prop="public_ip" label="外网 IP" min-width="160">
        <template #default="{ row }">
          <div v-if="parsePublicIps(row.public_ip).length > 0" style="display: flex; flex-direction: column; gap: 3px;">
            <span v-for="(ip, idx) in parsePublicIps(row.public_ip)" :key="idx" class="ip-code ip-code-public" @click="copyText(ip)" :title="'点击复制: ' + ip">
              {{ ip }}
            </span>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="open_ports" label="开放端口" min-width="200">
        <template #default="{ row }">
          <div v-if="getNodePorts(row).length > 0" style="display: flex; flex-wrap: wrap; gap: 4px;">
            <span v-for="(p, idx) in getNodePorts(row)" :key="idx" class="port-badge" :class="{ 'port-badge-range': isPortRange(p) }" @click="copyText(p)" :title="'点击复制: ' + p">
              {{ p }}
            </span>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="105" align="center">
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

      <el-table-column prop="cpu_cores" label="CPU" width="80" align="center" sortable>
        <template #default="{ row }">
          <div class="cell-box">
            <span v-if="row.cpu_cores && Number(row.cpu_cores) > 0">{{ row.cpu_cores }} 核</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="memory_gb" label="内存" width="85" align="center" sortable>
        <template #default="{ row }">
          <div class="cell-box">
            <span v-if="row.memory_gb && Number(row.memory_gb) > 0">{{ formatStorageFull(row.memory_gb) }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="disk_gb" label="数据盘" width="95" align="center" sortable>
        <template #default="{ row }">
          <div class="cell-box">
            <span v-if="row.disk_gb && Number(row.disk_gb) > 0">{{ formatStorageFull(row.disk_gb) }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="arch" label="架构" width="80" align="center">
        <template #default="{ row }">
          <div class="cell-box">
            <el-tag v-if="row.arch" size="small" :type="row.arch === 'arm64' ? 'warning' : 'info'">{{ getArchLabel(row.arch) }}</el-tag>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="os" label="操作系统" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">
          <div class="cell-box">
            <span v-if="row.os" style="font-size: 12px; color: #475569;">{{ row.os }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="kernel_version" label="内核版本" width="115" align="center">
        <template #default="{ row }">
          <div class="cell-box">
            <el-tooltip v-if="row.kernel_version" :content="row.kernel_version" placement="top" effect="dark">
              <span class="kernel-badge">{{ getCleanKernel(row.kernel_version) }}</span>
            </el-tooltip>
          </div>
        </template>
      </el-table-column>

    </el-table>

    <template #footer>
      <div style="display: flex; justify-content: flex-end; gap: 8px;">
        <el-button @click="visible = false">关闭</el-button>
        <el-button type="primary" plain @click="switchToBind">调整绑定节点</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { DoorOpen, Server, Cpu, Database, HardDrive, Search } from 'lucide-vue-next'
import {
  getMiddlewareLogo,
  formatStorageValue,
  formatStorageUnit,
  formatStorageFull,
  getCleanKernel,
  parsePublicIps,
  parsePorts,
  isPortRange,
  getStatusStyle,
  getEnvLabel as getEnvLabelUtil,
  getStatusLabel as getStatusLabelUtil,
  getArchLabel as getArchLabelUtil
} from '../utils'

const props = defineProps({
  metaConfig: { type: Object, required: true }
})
const emit = defineEmits(['switch-to-bind'])

const visible = ref(false)
const selectedViewCluster = ref(null)
const keyword = ref('')

const getNodePorts = (row) => {
  const set = new Set()
  if (row.open_ports) {
    parsePorts(row.open_ports).forEach(p => set.add(p))
  }
  if (selectedViewCluster.value?.port) {
    parsePorts(selectedViewCluster.value.port).forEach(p => set.add(p))
  }
  return Array.from(set)
}

const getEnvLabel = (key) => getEnvLabelUtil(key, props.metaConfig)
const getArchLabel = (key) => getArchLabelUtil(key, props.metaConfig)
const getStatusLabel = (key) => getStatusLabelUtil(key, props.metaConfig)

const formatCpuCell = (row) => {
  const v = Number(row.cpu_cores)
  return v > 0 ? `${v} 核` : ''
}

const formatMemCell = (row) => {
  const v = Number(row.memory_gb)
  return v > 0 ? formatStorageFull(v) : ''
}

const formatDiskCell = (row) => {
  const v = Number(row.disk_gb)
  return v > 0 ? formatStorageFull(v) : ''
}

const hasClusterRoles = (type) => {

  if (!type || !props.metaConfig?.cluster_types) return false
  const ct = props.metaConfig.cluster_types.find(c => c.key === type)
  return ct && ct.roles && ct.roles.length > 0
}

const clusterSummary = computed(() => {
  if (!selectedViewCluster.value?.nodes) return { totalCpu: 0, totalMem: 0, totalDisk: 0 }
  let totalCpu = 0
  let totalMem = 0
  let totalDisk = 0
  selectedViewCluster.value.nodes.forEach(n => {
    totalCpu += Number(n.cpu_cores) || 0
    totalMem += Number(n.memory_gb) || 0
    totalDisk += Number(n.disk_gb) || 0
  })
  return { totalCpu, totalMem, totalDisk }
})

const filteredViewNodes = computed(() => {
  if (!selectedViewCluster.value?.nodes) return []
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return selectedViewCluster.value.nodes
  return selectedViewCluster.value.nodes.filter(n => {
    return (
      n.hostname?.toLowerCase().includes(kw) ||
      n.private_ip?.toLowerCase().includes(kw) ||
      n.public_ip?.toLowerCase().includes(kw) ||
      n.os?.toLowerCase().includes(kw)
    )
  })
})

const copyText = (txt) => {
  if (!txt) return
  navigator.clipboard.writeText(txt).then(() => {
    ElMessage.success(`已复制: ${txt}`)
  })
}

const open = (cluster) => {
  selectedViewCluster.value = cluster
  keyword.value = ''
  visible.value = true
}

const switchToBind = () => {
  const c = selectedViewCluster.value
  visible.value = false
  if (c) {
    emit('switch-to-bind', c)
  }
}

defineExpose({ open })
</script>
