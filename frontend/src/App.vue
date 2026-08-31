<template>
  <el-config-provider :locale="zhCn">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="brand">
        <BrandLogo :size="34" />
        <div class="brand-title">资产管理系统</div>
      </div>
      <div class="nav-tabs">
        <button class="nav-tab-btn" :class="{ active: currentTab === 'dashboard' }" @click="switchTab('dashboard')">
          <LayoutDashboard :size="15" /> 资产概览
        </button>
        <button class="nav-tab-btn" :class="{ active: currentTab === 'hosts' }" @click="switchTab('hosts')">
          <Server :size="15" /> 主机资产
        </button>
        <button class="nav-tab-btn" :class="{ active: currentTab === 'clusters' }" @click="switchTab('clusters')">
          <Layers :size="15" /> 服务与集群
        </button>
        <button class="nav-tab-btn" :class="{ active: currentTab === 'domains' }" @click="switchTab('domains')">
          <Globe :size="15" /> 域名资产
        </button>
        <button class="nav-tab-btn" :class="{ active: currentTab === 'io' }" @click="switchTab('io')">
          <FileSpreadsheet :size="15" /> 导入导出
        </button>
        <button class="nav-tab-btn" :class="{ active: currentTab === 'config' }" @click="switchTab('config')">
          <Settings :size="15" /> 字典配置
        </button>
      </div>
      <div>
        <el-button type="primary" size="small" @click="refreshAll" :loading="globalRefreshing">
          <RefreshCw :size="13" style="margin-right: 4px;" :class="{ 'spin-anim': globalRefreshing }" /> 刷新数据
        </el-button>
      </div>
    </header>

    <!-- 主工作区 -->
    <main class="main-container">
      <!-- 1. 资产概览大盘 -->
      <DashboardView v-if="currentTab === 'dashboard'" :overview="overview" :meta-config="metaConfig"
        @select-cluster="switchTab('clusters')" @select-domains="switchTab('domains')" />

      <!-- 2. 主机资产管理 -->
      <HostListView v-if="currentTab === 'hosts'" ref="hostListViewRef" :meta-config="metaConfig" :cluster-list="clusterList"
        @filter-cluster="handleFilterClusterFromHost" @data-changed="refreshAll" />

      <!-- 3. 服务与集群管理 -->
      <ClusterListView v-if="currentTab === 'clusters'" ref="clusterListViewRef" :meta-config="metaConfig" :cluster-list="clusterList"
        :loading="clustersLoading" @data-changed="refreshAll" />

      <!-- 4. 域名资产管理 -->
      <DomainListView v-if="currentTab === 'domains'" ref="domainListViewRef" :meta-config="metaConfig"
        @data-changed="refreshAll" />

      <!-- 5. 导入导出中心 -->
      <IoCenterView v-if="currentTab === 'io'" :meta-config="metaConfig" @data-changed="refreshAll" />

      <!-- 6. 字典配置中心 -->
      <ConfigDictView v-if="currentTab === 'config'" :meta-config="metaConfig" @saved="handleConfigSaved" />
    </main>
  </el-config-provider>
</template>
<script setup>
import { ref, reactive, onMounted, defineAsyncComponent } from 'vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { ElMessage } from 'element-plus'
import { Server, LayoutDashboard, Layers, Globe, FileSpreadsheet, Settings, RefreshCw } from 'lucide-vue-next'
import OpsApi from './api'
import { normalizeMetaConfig } from './utils'
import BrandLogo from './components/BrandLogo.vue'

// 首屏大盘直接引入，非首屏大模块（主机管理/集群/域名/导入导出/字典）异步按需载入
import DashboardView from './views/DashboardView.vue'
const HostListView = defineAsyncComponent(() => import('./views/HostListView.vue'))
const ClusterListView = defineAsyncComponent(() => import('./views/ClusterListView.vue'))
const DomainListView = defineAsyncComponent(() => import('./views/DomainListView.vue'))
const IoCenterView = defineAsyncComponent(() => import('./views/IoCenterView.vue'))
const ConfigDictView = defineAsyncComponent(() => import('./views/ConfigDictView.vue'))

const currentTab = ref(window.location.hash ? window.location.hash.replace('#', '') : 'dashboard')
const globalRefreshing = ref(false)
const clustersLoading = ref(false)

const hostListViewRef = ref(null)
const clusterListViewRef = ref(null)
const domainListViewRef = ref(null)

const overview = ref({})
const clusterList = ref([])
const metaConfig = reactive({
  environments: [],
  host_statuses: [],
  cpu_architectures: [],
  cluster_types: [],
  common_os_list: []
})

const switchTab = (tab) => {
  currentTab.value = tab
  window.location.hash = tab
  if (tab === 'dashboard' && !overview.value.total_hosts) {
    fetchDashboard(true)
  } else if ((tab === 'hosts' || tab === 'clusters') && clusterList.value.length === 0) {
    fetchClusters(true)
  }
}

const fetchDashboard = async (silent = false) => {
  try {
    const [resOverview, resDist] = await Promise.all([
      OpsApi.getDashboard(),
      OpsApi.getClusterDistribution()
    ])
    const data = resOverview.data || {}
    data.cluster_distribution = resDist.data || []
    // 兼容 cluster_types / middleware_stats
    if (Array.isArray(data.cluster_types)) {
      data.middleware_stats = data.cluster_types.map(ct => ({
        type: ct.cluster_type,
        host_count: ct.count
      }))
    }
    overview.value = data
  } catch (e) {
    if (!silent) ElMessage.error('获取大盘数据失败')
  }
}

const fetchClusters = async (silent = false) => {
  if (!silent || clusterList.value.length === 0) clustersLoading.value = true
  try {
    const res = await OpsApi.getClusters()
    clusterList.value = res.data || []
  } catch (e) {
    if (!silent) ElMessage.error('获取集群列表失败')
  } finally {
    clustersLoading.value = false
  }
}

const fetchMetaConfig = async () => {
  try {
    const res = await OpsApi.getConfig()
    const normalized = normalizeMetaConfig(res.data || {})
    Object.assign(metaConfig, normalized)
  } catch (e) {
    console.error('加载字典配置失败:', e)
  }
}

const refreshAll = async () => {
  globalRefreshing.value = true
  try {
    await Promise.all([
      fetchMetaConfig(),
      fetchDashboard(true),
      fetchClusters(true)
    ])
    if (hostListViewRef.value?.fetchHosts) {
      await hostListViewRef.value.fetchHosts(true)
    }
    ElMessage.success('全站数据已同步刷新')
  } catch (e) {
    ElMessage.error('刷新失败')
  } finally {
    globalRefreshing.value = false
  }
}

const handleFilterClusterFromHost = (clusterId) => {
  switchTab('clusters')
  setTimeout(() => {
    if (clusterListViewRef.value?.filterByClusterId) {
      clusterListViewRef.value.filterByClusterId(clusterId)
    }
  }, 120)
}


const handleConfigSaved = async (newConfig) => {
  if (newConfig) {
    const normalized = normalizeMetaConfig(newConfig)
    Object.assign(metaConfig, normalized)
  }
  try {
    await Promise.all([
      fetchMetaConfig(),
      fetchDashboard(true),
      fetchClusters(true)
    ])
    if (hostListViewRef.value?.fetchHosts) {
      await hostListViewRef.value.fetchHosts(true)
    }
  } catch (e) {
    console.error('字典保存后同步数据异常:', e)
  }
}

onMounted(() => {
  fetchMetaConfig()
  const initialTab = currentTab.value
  if (initialTab === 'dashboard') {
    fetchDashboard(true)
  } else if (initialTab === 'hosts' || initialTab === 'clusters') {
    fetchClusters(true)
  }

  window.addEventListener('hashchange', () => {
    const hash = window.location.hash ? window.location.hash.replace('#', '') : 'dashboard'
    if (['dashboard', 'hosts', 'clusters', 'domains', 'io', 'config'].includes(hash)) {
      switchTab(hash)
    }
  })
})
</script>
