<template>
  <section class="tab-pane">
    <!-- 1. 顶部 5 大全局核心资产 KPI 胶囊栏 (Full-Width 5-Column Grid) -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-bottom: 20px;">
      <!-- KPI 1: 服务器总规模 -->
      <div class="ops-card kpi-card" style="padding: 16px 18px; display: flex; align-items: center; gap: 14px;">
        <div class="kpi-icon-box" style="background: #eff6ff; color: #2563eb; width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
          <Server :size="22" />
        </div>
        <div style="flex: 1; overflow: hidden;">
          <div style="font-size: 12px; font-weight: 500; color: #64748b; margin-bottom: 2px;">全网服务器总量</div>
          <div style="display: flex; align-items: baseline; gap: 6px;">
            <span style="font-size: 24px; font-weight: 700; color: #0f172a; font-family: 'JetBrains Mono', monospace;">
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
            <span style="font-size: 24px; font-weight: 700; color: #0284c7; font-family: 'JetBrains Mono', monospace;">
              {{ overview.total_domains || 0 }}
            </span>
            <span style="font-size: 12px; color: #64748b;">域名</span>
            <span style="color: #cbd5e1;">|</span>
            <span style="font-size: 18px; font-weight: 700; color: #2563eb; font-family: 'JetBrains Mono', monospace;">
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
            <span style="font-size: 24px; font-weight: 700; color: #7c3aed; font-family: 'JetBrains Mono', monospace;">
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
            <span style="font-size: 24px; font-weight: 700; color: #10b981; font-family: 'JetBrains Mono', monospace;">
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
            <span style="font-size: 22px; font-weight: 700; color: #d97706; font-family: 'JetBrains Mono', monospace;">
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

    <!-- 2. 环境资源对比卡片 (自适应全部动态环境，展示公网IP分布) -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 16px; margin-bottom: 20px;">
      <div v-for="env in availableEnvs" :key="env.key"
        class="ops-card env-card" :class="env.key" style="padding: 18px 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 15px; font-weight: 700; color: #0f172a;">{{ env.label }}</span>
            <span class="env-tag" :class="env.key">{{ env.label.replace('环境', '') }}</span>
          </div>
          <div style="font-size: 12.5px; color: #64748b; display: flex; align-items: center; gap: 6px;">
            <span>在线 <b style="color: #0f172a;">{{ getEnvStats(env.key).online_count || 0 }}</b> / <b style="color: #0f172a;">{{ getEnvStats(env.key).host_count || 0 }}</b> 台</span>
            <span v-if="getEnvStats(env.key).public_ip_count > 0" style="color: #2563eb; font-weight: 600; font-size: 11.5px;">(🌐 {{ getEnvStats(env.key).public_ip_count }} 公网)</span>
          </div>
        </div>

        <!-- 在线率健康度指示条 -->
        <div style="background: #f1f5f9; height: 6px; border-radius: 3px; overflow: hidden; margin-bottom: 16px;">
          <div :style="{ width: getEnvOnlineRate(env.key) + '%' }"
            :class="env.key === 'prod' ? 'bg-prod-bar' : 'bg-test-bar'"
            style="height: 100%; border-radius: 3px; transition: width 0.4s ease;"></div>
        </div>

        <!-- 3 列指标 -->
        <div class="metric-row" style="margin-top: 0;">
          <div class="metric-box">
            <div class="metric-val" :style="{ color: env.key === 'prod' ? '#dc2626' : '#059669' }" style="font-family: 'JetBrains Mono', monospace;">
              {{ getEnvStats(env.key).total_cpu_cores || 0 }} <span style="font-size: 11px; font-weight: normal; color: #64748b;">核</span>
            </div>
            <div class="metric-lbl">{{ env.label }} CPU</div>
          </div>
          <div class="metric-box">
            <div class="metric-val" style="font-family: 'JetBrains Mono', monospace;">
              {{ formatStorageValue(getEnvStats(env.key).total_memory_gb) }} <span style="font-size: 11px; font-weight: normal; color: #64748b;">{{ formatStorageUnit(getEnvStats(env.key).total_memory_gb) }}</span>
            </div>
            <div class="metric-lbl">{{ env.label }} 内存</div>
          </div>
          <div class="metric-box">
            <div class="metric-val" style="font-family: 'JetBrains Mono', monospace;">
              {{ formatStorageValue(getEnvStats(env.key).total_disk_gb) }} <span style="font-size: 11px; font-weight: normal; color: #64748b;">{{ formatStorageUnit(getEnvStats(env.key).total_disk_gb) }}</span>
            </div>
            <div class="metric-lbl">{{ env.label }} 存储</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 3. 公网资产全景看板 (公网 IP 资产池 + 核心公网域名资产) -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(440px, 1fr)); gap: 16px; margin-bottom: 20px;">
      <!-- 面板 1: 公网 IP 资产池 -->
      <div class="ops-card" style="padding: 18px 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <Network :size="16" style="color: #2563eb;" />
            <span style="font-size: 14.5px; font-weight: 700; color: #0f172a;">全网公网 IP 资产池</span>
            <span style="font-size: 12px; color: #64748b;">(共 {{ (overview.public_ip_details || []).length }} 个)</span>
          </div>
        </div>

        <div v-if="(overview.public_ip_details || []).length > 0" style="display: flex; flex-wrap: wrap; gap: 8px; max-height: 210px; overflow-y: auto; padding: 2px;">
          <div
            v-for="item in overview.public_ip_details"
            :key="item.ip"
            class="pub-ip-chip"
            @click="copyText(item.ip)"
            :title="`点击复制 IP | 主机: ${item.hostname} (${getEnvLabel(item.env)})`"
          >
            <span :class="item.is_ipv6 ? 'badge-ip-v6' : 'badge-ip-v4'" style="font-size: 9.5px; font-weight: 700; padding: 0 4px; border-radius: 2px; line-height: 14px;">
              {{ item.is_ipv6 ? 'v6' : 'v4' }}
            </span>
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600; color: #0f172a;">
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
        <div v-else style="text-align: center; padding: 24px 0; color: #94a3b8; font-size: 12.5px;">
          暂未发现配置公网 IP 的服务器
        </div>
      </div>

      <!-- 面板 2: 公网域名解析概况 -->
      <div class="ops-card" style="padding: 18px 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <Globe :size="16" style="color: #0284c7;" />
            <span style="font-size: 14.5px; font-weight: 700; color: #0f172a;">公网域名解析台账概览</span>
            <span style="font-size: 12px; color: #64748b;">(共 {{ (overview.domains_summary || []).length }} 个)</span>
          </div>
          <el-button size="small" type="primary" link @click="$emit('select-domains')">
            管理域名资产 →
          </el-button>
        </div>

        <div v-if="(overview.domains_summary || []).length > 0" style="display: flex; flex-direction: column; gap: 8px; max-height: 210px; overflow-y: auto; padding-right: 4px;">
          <div
            v-for="d in overview.domains_summary"
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
              <span v-if="d.public_ip" style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #475569;" :title="'绑定IP: ' + d.public_ip">
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

    <!-- 4. 服务与集群拓扑全景矩阵 (全宽展示，支持环境与组件双重过滤) -->
    <div class="ops-card" style="margin-bottom: 24px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px;">
        <!-- 左侧: 标题 + 环境选择胶囊组 -->
        <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
          <h3 style="font-size: 15px; font-weight: 700; color: #0f172a; margin: 0; display: flex; align-items: center; gap: 6px;">
            <Layers :size="16" style="color: #7c3aed;" /> 各服务与集群节点分布
          </h3>
          <span style="font-size: 12px; color: #64748b;">
            ({{ filteredClusters.length }} / {{ (overview.cluster_distribution || []).length }})
          </span>

          <!-- 环境单选胶囊 -->
          <div style="display: flex; gap: 4px; align-items: center; background: #f1f5f9; padding: 3px; border-radius: 6px; margin-left: 4px;">
            <div class="env-filter-chip" :class="{ active: selectedEnvFilter === '' }" @click="selectedEnvFilter = ''">
              全部环境
            </div>
            <div v-for="env in availableEnvs" :key="env.key"
              class="env-filter-chip" :class="{ active: selectedEnvFilter === env.key }"
              @click="selectedEnvFilter = (selectedEnvFilter === env.key ? '' : env.key)">
              {{ env.label }}
            </div>
          </div>
        </div>

        <!-- 右侧: 中间件类型选择胶囊组 -->
        <div style="display: flex; gap: 5px; flex-wrap: wrap; align-items: center;">
          <div class="cluster-chip" :class="{ active: selectedTypeFilter === '' }" @click="selectedTypeFilter = ''">
            <span>全部组件</span>
            <span class="chip-count">{{ currentEnvTotalClusters }}</span>
          </div>
          <div v-for="t in dynamicClusterTypes" :key="t.type"
            class="cluster-chip" :class="{ active: selectedTypeFilter === t.type }"
            @click="selectedTypeFilter = (selectedTypeFilter === t.type ? '' : t.type)">
            <span v-html="getMiddlewareLogo(t.type, 14)" style="display: flex; align-items: center;"></span>
            <span>{{ t.type }}</span>
            <span class="chip-count">{{ t.count }}</span>
          </div>
        </div>
      </div>

      <!-- 自适应集群网格卡片 -->
      <div v-if="filteredClusters.length > 0"
        style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; max-height: 480px; overflow-y: auto; padding-right: 4px;">
        <div v-for="c in filteredClusters" :key="c.name"
          class="dashboard-cluster-item"
          @click="handleClusterClick(c)">
          <div style="display: flex; align-items: center; gap: 10px; overflow: hidden; flex: 1; min-width: 0;">
            <span v-html="getMiddlewareLogo(c.cluster_type, 20)" style="display: flex; align-items: center; flex-shrink: 0;"></span>
            <div style="overflow: hidden; display: flex; flex-direction: column; min-width: 0; flex: 1;">
              <span style="font-size: 13.5px; font-weight: 600; color: #0f172a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" :title="c.name">
                {{ c.name }}
              </span>
              <div style="display: flex; gap: 5px; align-items: center; margin-top: 3px; white-space: nowrap; overflow: hidden;">
                <span v-if="c.env" class="env-tag" :class="c.env" style="font-size: 10.5px; padding: 0 5px; line-height: 16px; flex-shrink: 0;">
                  {{ getEnvLabel(c.env) }}
                </span>
                <span style="font-size: 11px; color: #64748b; font-weight: 500; flex-shrink: 0;">{{ c.cluster_type }}</span>
                <span v-if="c.version"
                  style="font-size: 10.5px; font-family: 'JetBrains Mono', monospace; color: #2563eb; background: #eff6ff; border: 1px solid #dbeafe; padding: 0.5px 5px; border-radius: 3px; font-weight: 600; line-height: 15px; max-width: 110px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;"
                  :title="'版本: ' + c.version">
                  {{ c.version }}
                </span>
              </div>
            </div>
          </div>

          <div style="display: flex; align-items: center; gap: 6px; flex-shrink: 0; margin-left: 8px;">
            <span style="font-size: 12.5px; font-weight: 700; color: #2563eb; background: #eff6ff; padding: 3px 9px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">
              {{ c.node_count }} 节点
            </span>
          </div>
        </div>
      </div>

      <div v-else style="text-align: center; padding: 36px 0; color: #94a3b8; font-size: 13px;">
        暂无符合筛选条件的服务与集群
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Server, Layers, Cpu, HardDrive, Network, Globe } from 'lucide-vue-next'
import { getMiddlewareLogo, formatStorageValue, formatStorageUnit, formatStorageFull, getEnvLabel as getEnvLabelUtil } from '../utils'

const props = defineProps({
  overview: { type: Object, required: true },
  metaConfig: { type: Object, required: true }
})
const emit = defineEmits(['select-cluster', 'select-domains'])

const selectedEnvFilter = ref('')
const selectedTypeFilter = ref('')

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
  const total = Number(props.overview?.total_hosts || 0)
  return Math.max(0, total - totalOnlineHosts.value)
})

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

const currentEnvTotalClusters = computed(() => {
  let list = props.overview?.cluster_distribution || []
  if (selectedEnvFilter.value) {
    list = list.filter(c => c.env === selectedEnvFilter.value)
  }
  return list.length
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
