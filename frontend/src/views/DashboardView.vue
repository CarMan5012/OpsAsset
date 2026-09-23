<template>
  <section class="tab-pane">
    <!-- 1. 顶部 5 大全局核心资产 KPI 胶囊栏 (Full-Width 5-Column Grid) -->
    <div class="dashboard-section" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px; margin-bottom: 28px;">
      <!-- KPI 1: 服务器总规模 -->
      <div class="ops-card kpi-card" style="padding: 16px 18px; display: flex; align-items: center; gap: 14px;">
        <div class="kpi-icon-box" style="background: #eff6ff; color: #2563eb; width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
          <Server :size="22" />
        </div>
        <div style="flex: 1; overflow: hidden;">
          <div style="font-size: 12px; font-weight: 500; color: #64748b; margin-bottom: 2px;">全网服务器总量</div>
          <div style="display: flex; align-items: baseline; gap: 6px;">
            <span style="font-size: 24px; font-weight: 700; color: #0f172a; font-family: var(--font-data);">
              {{ overview.total_hosts || 0 }}
            </span>
            <span style="font-size: 12px; color: #64748b;">台</span>
          </div>
          <div style="margin-top: 4px; display: flex; align-items: center; gap: 6px; font-size: 11.5px; flex-wrap: wrap;">
            <span style="color: #10b981; font-weight: 600;">● 在线 {{ totalOnlineHosts }}</span>
            <span v-if="totalOfflineHosts > 0" style="color: #ef4444; font-weight: 500;">● 离线 {{ totalOfflineHosts }}</span>
          </div>
        </div>
      </div>

      <!-- KPI 2: 公网域名与公网 IP 资产 (重点新增) -->
      <div
        class="ops-card kpi-card"
        style="padding: 16px 18px; display: flex; align-items: center; gap: 14px; cursor: pointer;"
        @click="$emit('select-domains')"
        title="点击跳转至公网域名台账"
      >
        <div class="kpi-icon-box" style="background: #e0f2fe; color: #0284c7; width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
          <Globe :size="22" />
        </div>
        <div style="flex: 1; overflow: hidden;">
          <div style="font-size: 12px; font-weight: 500; color: #64748b; margin-bottom: 2px; display: flex; align-items: center; justify-content: space-between;">
            <span>公网域名与 IP 资产</span>
            <span style="font-size: 11px; color: #0284c7; font-weight: 600;">详情 →</span>
          </div>
          <div style="display: flex; align-items: baseline; gap: 8px;">
            <span style="font-size: 24px; font-weight: 700; color: #0284c7; font-family: var(--font-data);">
              {{ overview.total_domains || 0 }}
            </span>
            <span style="font-size: 12px; color: #64748b;">域名</span>
            <span style="color: #cbd5e1;">|</span>
            <span style="font-size: 18px; font-weight: 700; color: #2563eb; font-family: var(--font-data);">
              {{ overview.total_public_ips || 0 }}
            </span>
            <span style="font-size: 12px; color: #64748b;">公网IP</span>
          </div>
          <div style="margin-top: 4px; display: flex; align-items: center; gap: 6px; font-size: 11px;">
            <span style="color: #10b981; font-weight: 600;">✔ 一致 {{ overview.matched_domains || 0 }}</span>
            <span v-if="overview.mismatched_domains > 0" style="color: #f59e0b; font-weight: 600;">⚠ 异常 {{ overview.mismatched_domains }}</span>
            <span v-if="overview.failed_domains > 0" style="color: #ef4444; font-weight: 600;">❌ 失败 {{ overview.failed_domains }}</span>
          </div>
        </div>
      </div>

      <!-- KPI 3: 服务与集群 -->
      <div class="ops-card kpi-card" style="padding: 16px 18px; display: flex; align-items: center; gap: 14px;">
        <div class="kpi-icon-box" style="background: #faf5ff; color: #7c3aed; width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
          <Layers :size="22" />
        </div>
        <div style="flex: 1; overflow: hidden;">
          <div style="font-size: 12px; font-weight: 500; color: #64748b; margin-bottom: 2px;">服务与集群总数</div>
          <div style="display: flex; align-items: baseline; gap: 6px;">
            <span style="font-size: 24px; font-weight: 700; color: #7c3aed; font-family: var(--font-data);">
              {{ overview.total_clusters || 0 }}
            </span>
            <span style="font-size: 12px; color: #64748b;">个</span>
          </div>
          <div style="margin-top: 4px; font-size: 11.5px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            纳管 <b>{{ uniqueClusterTypesCount }}</b> 类中间件组件
          </div>
        </div>
      </div>

      <!-- KPI 4: CPU 总核心数 -->
      <div class="ops-card kpi-card" style="padding: 16px 18px; display: flex; align-items: center; gap: 14px;">
        <div class="kpi-icon-box" style="background: #f0fdf4; color: #10b981; width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
          <Cpu :size="22" />
        </div>
        <div style="flex: 1; overflow: hidden;">
          <div style="font-size: 12px; font-weight: 500; color: #64748b; margin-bottom: 2px;">CPU 算力总量</div>
          <div style="display: flex; align-items: baseline; gap: 6px;">
            <span style="font-size: 24px; font-weight: 700; color: #10b981; font-family: var(--font-data);">
              {{ overview.total_cpu_cores || 0 }}
            </span>
            <span style="font-size: 12px; color: #64748b;">核</span>
          </div>
          <div style="margin-top: 4px; font-size: 11.5px; color: #64748b;">
            平均 {{ avgCpuPerHost }} 核/台 · {{ availableEnvs.length }} 个环境
          </div>
        </div>
      </div>

      <!-- KPI 5: 存储与内存总容量 -->
      <div class="ops-card kpi-card" style="padding: 16px 18px; display: flex; align-items: center; gap: 14px;">
        <div class="kpi-icon-box" style="background: #fffbeb; color: #f59e0b; width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
          <HardDrive :size="22" />
        </div>
        <div style="flex: 1; overflow: hidden;">
          <div style="font-size: 12px; font-weight: 500; color: #64748b; margin-bottom: 2px;">总内存与存储池</div>
          <div style="display: flex; align-items: baseline; gap: 6px;">
            <span style="font-size: 22px; font-weight: 700; color: #d97706; font-family: var(--font-data);">
              {{ formatStorageValue(overview.total_memory_gb) }}
            </span>
            <span style="font-size: 12px; color: #64748b; font-weight: 600;">{{ formatStorageUnit(overview.total_memory_gb) }} (RAM)</span>
          </div>
          <div style="margin-top: 4px; font-size: 11.5px; color: #64748b;">
            数据盘: <b>{{ formatStorageFull(totalDiskCapacity) }}</b>
          </div>
        </div>
      </div>
    </div>

    <div class="dashboard-attention" :class="{ 'is-clear': attentionCount === 0 }">
      <div class="dashboard-attention-title">
        <span class="attention-dot"></span>
        <strong>{{ attentionCount > 0 ? '需要关注' : '运行正常' }}</strong>
        <span>{{ attentionCount > 0 ? `共 ${attentionCount} 项` : '当前没有离线主机、维护中主机或域名解析异常' }}</span>
      </div>
      <div v-if="attentionCount > 0" class="dashboard-attention-items">
        <span v-if="totalOfflineHosts > 0">离线主机 <b>{{ totalOfflineHosts }}</b></span>
        <span v-if="totalMaintenanceHosts > 0">维护中 <b>{{ totalMaintenanceHosts }}</b></span>
        <button v-if="dnsIssueCount > 0" type="button" @click="$emit('select-domains')">域名解析异常 <b>{{ dnsIssueCount }}</b> →</button>
      </div>
    </div>

    <!-- 2. 环境资源对比 -->
    <div class="dashboard-section" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 360px), 1fr)); gap: 18px; margin-bottom: 28px;">
      <div v-for="env in availableEnvs" :key="env.key"
        class="ops-card env-card env-summary" :class="env.key">
        <div class="env-summary-head">
          <strong>{{ env.label }}</strong>
          <span>在线 <b>{{ getEnvStats(env.key).online_count || 0 }}</b> / {{ getEnvStats(env.key).host_count || 0 }} 台</span>
        </div>
        <div class="env-summary-track"><span :style="{ width: getEnvOnlineRate(env.key) + '%' }"></span></div>
        <div class="env-summary-metrics">
          <div><span>CPU</span><strong>{{ getEnvStats(env.key).total_cpu_cores || 0 }} 核</strong></div>
          <div><span>内存</span><strong>{{ formatStorageFull(getEnvStats(env.key).total_memory_gb) || '0 GB' }}</strong></div>
          <div><span>存储</span><strong>{{ formatStorageFull(getEnvStats(env.key).total_disk_gb) || '0 GB' }}</strong></div>
        </div>
      </div>
    </div>

    <!-- 3. 公网资产全景看板 (公网 IP 资产池 + 核心公网域名资产) -->
    <div class="dashboard-section" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 440px), 1fr)); gap: 18px; margin-bottom: 28px;">
      <!-- 面板 1: 公网 IP 资产池 -->
      <div class="ops-card" style="padding: 18px 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <Network :size="16" style="color: #2563eb;" />
            <span style="font-size: 14.5px; font-weight: 700; color: #0f172a;">公网 IP</span>
            <span style="font-size: 12px; color: #64748b;">(共 {{ (overview.public_ip_details || []).length }} 个)</span>
          </div>
        </div>

        <div v-if="(overview.public_ip_details || []).length > 0" style="display: flex; flex-wrap: wrap; gap: 8px; padding: 2px;">
          <div
            v-for="item in (overview.public_ip_details || []).slice(0, 5)"
            :key="item.ip"
            class="pub-ip-chip"
            @click="copyText(item.ip)"
            :title="`点击复制 IP | 主机: ${item.hostname} (${getEnvLabel(item.env)})`"
          >
            <span :class="item.is_ipv6 ? 'badge-ip-v6' : 'badge-ip-v4'" style="font-size: 9.5px; font-weight: 700; padding: 0 4px; border-radius: 2px; line-height: 14px;">
              {{ item.is_ipv6 ? 'v6' : 'v4' }}
            </span>
            <span style="font-family: var(--font-data); font-size: 12px; font-weight: 600; color: #0f172a;">
              {{ item.ip }}
            </span>
            <span style="font-size: 11px; color: #64748b; border-left: 1px solid #cbd5e1; padding-left: 5px;">
              {{ item.hostname }}
            </span>
            <span class="env-tag" :class="item.env" style="font-size: 9.5px; padding: 0 4px; line-height: 14px;">
              {{ getEnvLabel(item.env) }}
            </span>
          </div>
        </div>
        <button v-if="(overview.public_ip_details || []).length > 5" class="dashboard-more" type="button" @click="$emit('select-hosts')">查看全部 {{ overview.public_ip_details.length }} 个 →</button>
        <div v-if="!(overview.public_ip_details || []).length" style="text-align: center; padding: 24px 0; color: #94a3b8; font-size: 12.5px;">
          暂未发现配置公网 IP 的服务器
        </div>
      </div>

      <!-- 面板 2: 公网域名解析概况 -->
      <div class="ops-card" style="padding: 18px 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <Globe :size="16" style="color: #0284c7;" />
            <span style="font-size: 14.5px; font-weight: 700; color: #0f172a;">域名解析</span>
            <span style="font-size: 12px; color: #64748b;">(共 {{ (overview.domains_summary || []).length }} 个)</span>
          </div>
          <el-button size="small" type="primary" link @click="$emit('select-domains')">
            查看全部 →
          </el-button>
        </div>

        <div v-if="(overview.domains_summary || []).length > 0" style="display: flex; flex-direction: column; gap: 8px;">
          <div
            v-for="d in prioritizedDomains"
            :key="d.id"
            class="domain-summary-item"
            @click="$emit('select-domains')"
          >
            <div style="display: flex; align-items: center; gap: 8px; overflow: hidden; flex: 1; min-width: 0;">
              <Globe :size="14" style="color: #0284c7; flex-shrink: 0;" />
              <span style="font-weight: 600; color: #0f172a; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" :title="d.domain_name">
                {{ d.domain_name }}
              </span>
              <span class="env-tag" :class="d.env" style="font-size: 9.5px; padding: 0 4px; line-height: 14px; flex-shrink: 0;">
                {{ getEnvLabel(d.env) }}
              </span>
            </div>

            <div style="display: flex; align-items: center; gap: 8px; flex-shrink: 0;">
              <span v-if="d.public_ip" style="font-family: var(--font-data); font-size: 11px; color: #475569;" :title="'绑定IP: ' + d.public_ip">
                {{ d.public_ip.split(/[,，;\s]+/)[0] }}{{ d.public_ip.includes(',') ? ' 等' : '' }}
              </span>
              <el-tag v-if="d.resolve_status === 'matched'" type="success" size="small" effect="light" style="font-weight: 600;">
                ✔ 一致
              </el-tag>
              <el-tag v-else-if="d.resolve_status === 'mismatched'" type="warning" size="small" effect="light" style="font-weight: 600;">
                ⚠ 不一致
              </el-tag>
              <el-tag v-else-if="d.resolve_status === 'failed'" type="danger" size="small" effect="light" style="font-weight: 600;">
                ❌ 失败
              </el-tag>
              <el-tag v-else type="info" size="small" effect="light">
                未检测
              </el-tag>
            </div>
          </div>
        </div>
        <div v-else style="text-align: center; padding: 24px 0; color: #94a3b8; font-size: 12.5px;">
          暂无录入的公网域名资产
        </div>
      </div>
    </div>

    <div class="ops-card dashboard-clusters">
      <div class="dashboard-clusters-header">
        <div class="dashboard-clusters-title"><Layers :size="17" /> 服务与集群 <span>{{ filteredClusters.length }} 个</span></div>
        <div class="dashboard-clusters-actions">
          <el-select v-model="selectedEnvFilter" aria-label="筛选环境" size="small" style="width: 118px">
            <el-option label="全部环境" value="" />
            <el-option v-for="env in availableEnvs" :key="env.key" :label="env.label" :value="env.key" />
          </el-select>
          <el-select v-model="selectedTypeFilter" aria-label="筛选组件" size="small" style="width: 130px">
            <el-option label="全部组件" value="" />
            <el-option v-for="t in dynamicClusterTypes" :key="t.type" :label="`${t.type} (${t.count})`" :value="t.type" />
          </el-select>
          <el-button size="small" type="primary" link @click="$emit('select-cluster')">管理集群 →</el-button>
        </div>
      </div>
      <div v-if="filteredClusters.length" class="dashboard-cluster-grid">
        <button v-for="c in visibleClusters" :key="`${c.name}-${c.env}`" type="button" class="dashboard-cluster-item" @click="handleClusterClick(c)">
          <span v-html="getMiddlewareLogo(c.cluster_type, 20)" class="dashboard-cluster-logo"></span>
          <span class="dashboard-cluster-details"><strong :title="c.name">{{ c.name }}</strong><small>{{ getEnvLabel(c.env) }} · {{ c.cluster_type }}</small></span>
          <span class="dashboard-cluster-nodes">{{ c.node_count }} 节点</span>
        </button>
      </div>
      <div v-else class="dashboard-empty">暂无符合条件的集群</div>
      <button v-if="filteredClusters.length > 6" class="dashboard-more" type="button" @click="showAllClusters = !showAllClusters">
        {{ showAllClusters ? '收起' : `展开其余 ${filteredClusters.length - 6} 个` }} {{ showAllClusters ? '↑' : '↓' }}
      </button>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Server, Layers, Cpu, HardDrive, Network, Globe } from 'lucide-vue-next'
import { getMiddlewareLogo, formatStorageValue, formatStorageUnit, formatStorageFull, getEnvLabel as getEnvLabelUtil } from '../utils'

const props = defineProps({
  overview: { type: Object, required: true },
  metaConfig: { type: Object, required: true }
})
const emit = defineEmits(['select-cluster', 'select-domains', 'select-hosts'])

const selectedEnvFilter = ref('')
const selectedTypeFilter = ref('')
const showAllClusters = ref(false)
watch(selectedEnvFilter, () => { selectedTypeFilter.value = ''; showAllClusters.value = false })
watch(selectedTypeFilter, () => { showAllClusters.value = false })

const availableEnvs = computed(() => {
  return props.metaConfig?.environments || []
})

const getEnvStats = (envKey) => {
  return props.overview?.envs?.[envKey] || {
    host_count: 0,
    online_count: 0,
    offline_count: 0,
    maintenance_count: 0,
    total_cpu_cores: 0,
    total_memory_gb: 0,
    total_disk_gb: 0
  }
}

const getEnvOnlineRate = (envKey) => {
  const s = getEnvStats(envKey)
  const total = Number(s?.host_count || 0)
  if (total === 0) return 0
  const online = Number(s?.online_count || 0)
  return Math.min(100, Math.round((online / total) * 100))
}

const avgCpuPerHost = computed(() => {
  const totalH = Number(props.overview?.total_hosts || 0)
  if (totalH === 0) return 0
  const totalC = Number(props.overview?.total_cpu_cores || 0)
  return Math.round(totalC / totalH)
})

const totalOnlineHosts = computed(() => {
  if (props.overview?.envs) {
    return Object.values(props.overview.envs).reduce((sum, s) => sum + Number(s.online_count || 0), 0)
  }
  return 0
})

const totalOfflineHosts = computed(() => {
  return Object.values(props.overview?.envs || {}).reduce((sum, s) => sum + Number(s.offline_count || 0), 0)
})

const totalMaintenanceHosts = computed(() => Object.values(props.overview?.envs || {}).reduce((sum, s) => sum + Number(s.maintenance_count || 0), 0))
const dnsIssueCount = computed(() => (props.overview?.domains_summary || []).filter(d => ['mismatched', 'failed'].includes(d.resolve_status)).length)
const attentionCount = computed(() => totalOfflineHosts.value + totalMaintenanceHosts.value + dnsIssueCount.value)
const prioritizedDomains = computed(() => [...(props.overview?.domains_summary || [])]
  .sort((a, b) => Number(['mismatched', 'failed'].includes(b.resolve_status)) - Number(['mismatched', 'failed'].includes(a.resolve_status)))
  .slice(0, 4))

const totalDiskCapacity = computed(() => {
  if (props.overview?.envs) {
    return Object.values(props.overview.envs).reduce((sum, s) => sum + Number(s.total_disk_gb || 0), 0)
  }
  return 0
})

const uniqueClusterTypesCount = computed(() => {
  const list = props.overview?.cluster_distribution || []
  const types = new Set(list.map(c => c.cluster_type).filter(Boolean))
  return types.size || (props.metaConfig?.cluster_types?.length || 0)
})

const dynamicClusterTypes = computed(() => {
  let list = props.overview?.cluster_distribution || []
  if (selectedEnvFilter.value) {
    list = list.filter(c => c.env === selectedEnvFilter.value)
  }
  const map = {}
  list.forEach(c => {
    const t = c.cluster_type || 'Other'
    map[t] = (map[t] || 0) + 1
  })
  return Object.keys(map).map(k => ({ type: k, count: map[k] })).sort((a, b) => b.count - a.count)
})

const filteredClusters = computed(() => {
  let list = props.overview?.cluster_distribution || []
  if (selectedEnvFilter.value) {
    list = list.filter(c => c.env === selectedEnvFilter.value)
  }
  if (selectedTypeFilter.value) {
    list = list.filter(c => c.cluster_type === selectedTypeFilter.value)
  }
  return list
})

const visibleClusters = computed(() => showAllClusters.value ? filteredClusters.value : filteredClusters.value.slice(0, 6))

const getEnvLabel = (key) => {
  return getEnvLabelUtil(key, props.metaConfig)
}

const copyText = (text) => {
  if (!text) return
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success(`已复制公网 IP: ${text}`)
  }).catch(() => {
    ElMessage.info(`公网 IP: ${text}`)
  })
}

const handleClusterClick = (c) => {
  emit('select-cluster', c)
}
</script>

<style scoped>
.dashboard-attention{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:24px;padding:13px 18px;border:1px solid #fed7aa;border-radius:10px;background:#fffaf3;color:#9a3412}
.dashboard-attention.is-clear{border-color:#bbf7d0;background:#f7fef9;color:#166534}
.dashboard-attention-title,.dashboard-attention-items{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.dashboard-attention-title strong{font-size:14px}
.dashboard-attention-title span:last-child{font-size:12px;color:#64748b}
.attention-dot{width:8px;height:8px;border-radius:50%;background:#f97316}
.is-clear .attention-dot{background:#22c55e}
.dashboard-attention-items{font-size:12px}
.dashboard-attention-items button,.dashboard-more{border:0;background:none;color:#2563eb;font:inherit;font-weight:600;cursor:pointer;padding:0}
.dashboard-attention-items button:hover,.dashboard-more:hover{text-decoration:underline}
.env-summary{padding:18px 20px}
.env-summary-head{display:flex;justify-content:space-between;align-items:center;gap:12px;color:#0f172a}
.env-summary-head strong{font-size:15px}
.env-summary-head span{color:#64748b;font-size:12px}
.env-summary-head b{color:#0f172a;font-size:17px}
.env-summary-track{height:5px;background:#e2e8f0;border-radius:10px;margin:15px 0 16px;overflow:hidden}
.env-summary-track span{display:block;height:100%;background:#2563eb;border-radius:10px}
.env-summary.test .env-summary-track span{background:#10b981}
.env-summary-metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.env-summary-metrics div{display:flex;flex-direction:column;gap:4px;min-width:0}
.env-summary-metrics span{color:#64748b;font-size:11px}
.env-summary-metrics strong{color:#334155;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dashboard-more{display:block;margin:16px auto 0;font-size:12px}
.dashboard-clusters{padding:20px;margin-bottom:24px}
.dashboard-clusters-header,.dashboard-clusters-actions{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.dashboard-clusters-header{justify-content:space-between;margin-bottom:16px}
.dashboard-clusters-title{display:flex;align-items:center;gap:7px;color:#0f172a;font-size:15px;font-weight:700}
.dashboard-clusters-title svg{color:#7c3aed}
.dashboard-clusters-title span{color:#64748b;font-size:12px;font-weight:400}
.dashboard-cluster-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.dashboard-cluster-logo{display:flex;align-items:center;flex-shrink:0}
.dashboard-cluster-details{display:flex;flex:1;min-width:0;flex-direction:column;gap:3px;text-align:left}
.dashboard-cluster-details strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;color:#0f172a}
.dashboard-cluster-details small{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11px;color:#64748b}
.dashboard-cluster-nodes{font-size:12px;color:#2563eb;white-space:nowrap}
.dashboard-empty{padding:30px;text-align:center;color:#94a3b8;font-size:13px}
@media(max-width:1100px){.dashboard-cluster-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:680px){.dashboard-cluster-grid{grid-template-columns:1fr}.dashboard-clusters-actions{width:100%}.dashboard-attention{align-items:flex-start}.env-summary-metrics{gap:6px}}
.bg-prod-bar {
  background: #2563eb;
}
.bg-test-bar {
  background: #10b981;
}

.kpi-card {
  transition: all 0.2s ease;
  border: 1px solid #e2e8f0;
}
.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.pub-ip-chip {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 5px 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.pub-ip-chip:hover {
  background: #eff6ff;
  border-color: #93c5fd;
  transform: translateY(-1px);
}

.badge-ip-v4 {
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
}
.badge-ip-v6 {
  background: #fdf4ff;
  color: #a855f7;
  border: 1px solid #f0abfc;
}

.domain-summary-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 8px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.15s ease;
}
.domain-summary-item:hover {
  background: #ffffff;
  border-color: #93c5fd;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
}

.env-filter-chip {
  padding: 3px 9px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s ease;
}
.env-filter-chip:hover {
  color: #0f172a;
}
.env-filter-chip.active {
  background: #ffffff;
  color: #2563eb;
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.dashboard-cluster-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s ease;
  cursor: pointer;
}
.dashboard-cluster-item:hover {
  background: #ffffff;
  border-color: #93c5fd;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.08);
  transform: translateY(-1px);
}
</style>
