<template>
  <section class="tab-pane">
    <div class="ops-card">
      <!-- 顶部工具栏 -->
      <div class="filter-bar">
        <div class="filter-group">
          <div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-right: 8px; display: flex; align-items: center; gap: 6px;">
            <Globe :size="16" style="color: #2563eb;" /> 公网域名资产台账
          </div>
          <el-input
            v-model="filter.keyword"
            placeholder="搜索域名/公网IP/解析IP/主机/备注"
            clearable
            @input="pagination.page = 1"
            style="width: 260px;"
          >
            <template #prefix><Search :size="14" style="color: #94a3b8;" /></template>
          </el-input>
          <el-select v-model="filter.env" placeholder="全部环境" clearable style="width: 115px;">
            <el-option v-for="env in metaConfig.environments" :key="env.key" :label="env.label" :value="env.key" />
          </el-select>
          <el-select v-model="filter.resolve_status" placeholder="全部解析状态" clearable style="width: 135px;">
            <el-option label="✔ 一致" value="matched" />
            <el-option label="⚠ 不一致" value="mismatched" />
            <el-option label="❌ 解析失败" value="failed" />
          </el-select>
        </div>

        <div style="display: flex; align-items: center; gap: 10px;">
          <el-button :loading="checkingAll" @click="handleCheckAllDns">
            <RefreshCw :size="13" style="margin-right: 4px;" :class="{ 'spin-anim': checkingAll }" />
            一键比对解析 (IPv4/IPv6)
          </el-button>
          <el-button type="primary" @click="openCreateDialog">+ 添加域名资产</el-button>
        </div>
      </div>

      <!-- 域名列表表格 -->
      <div style="margin-top: 16px;">
        <el-table
          :data="pagedDomainList"
          stripe
          style="width: 100%"
          v-loading="loading"
          row-key="id"
        >
          <el-table-column prop="id" label="ID" width="65" align="center" />

          <!-- 1. 域名 -->
          <el-table-column prop="domain_name" label="公网域名" min-width="210" show-overflow-tooltip>
            <template #default="{ row }">
              <div style="display: flex; align-items: center; gap: 6px;">
                <Globe :size="15" style="color: #2563eb; flex-shrink: 0;" />
                <a
                  :href="`http://${row.domain_name}`"
                  target="_blank"
                  rel="noopener noreferrer"
                  style="color: #0f172a; font-weight: 700; text-decoration: none; display: flex; align-items: center; gap: 4px;"
                  title="点击在新窗口打开"
                >
                  {{ row.domain_name }}
                  <ExternalLink :size="12" style="color: #94a3b8;" />
                </a>
                <Copy
                  :size="12"
                  style="color: #94a3b8; cursor: pointer; margin-left: 2px;"
                  @click.stop="copyText(row.domain_name)"
                  title="复制域名"
                />
              </div>
            </template>
          </el-table-column>

          <!-- 2. 绑定的公网IP (支持多IP分行展示) -->
          <el-table-column label="配置绑定公网 IP" min-width="190">
            <template #default="{ row }">
              <div v-if="parseIps(row.public_ip).length > 0" style="display: flex; flex-direction: column; gap: 4px;">
                <div
                  v-for="(ip, idx) in parseIps(row.public_ip)"
                  :key="idx"
                  style="display: flex; align-items: center; gap: 5px;"
                >
                  <span
                    :class="isIpv6(ip) ? 'badge-ip-v6' : 'badge-ip-v4'"
                    style="font-size: 10px; font-weight: 700; padding: 1px 4px; border-radius: 3px; line-height: 1;"
                  >
                    {{ isIpv6(ip) ? 'IPv6' : 'IPv4' }}
                  </span>
                  <span style="font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600; color: #1e293b;">
                    {{ ip }}
                  </span>
                  <Copy
                    :size="11"
                    style="color: #94a3b8; cursor: pointer;"
                    @click.stop="copyText(ip)"
                    title="复制IP"
                  />
                </div>
              </div>
              <span v-else style="color: #94a3b8; font-size: 12px;">未配置绑定IP</span>
            </template>
          </el-table-column>

          <!-- 3. 实际解析 IP 与一致性校验 (IPv4 + IPv6 双栈) -->
          <el-table-column label="实际 DNS 解析 (IPv4 / IPv6)" min-width="250">
            <template #default="{ row }">
              <div style="display: flex; flex-direction: column; gap: 4px;">
                <!-- 解析出的各 IP 列表 -->
                <div v-if="parseIps(row.resolved_ip).length > 0" style="display: flex; flex-direction: column; gap: 3px;">
                  <div
                    v-for="(ip, idx) in parseIps(row.resolved_ip)"
                    :key="idx"
                    style="display: flex; align-items: center; gap: 5px;"
                  >
                    <span
                      :class="isIpv6(ip) ? 'badge-ip-v6' : 'badge-ip-v4'"
                      style="font-size: 10px; font-weight: 700; padding: 1px 4px; border-radius: 3px; line-height: 1;"
                    >
                      {{ isIpv6(ip) ? 'IPv6' : 'IPv4' }}
                    </span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #334155;">
                      {{ ip }}
                    </span>
                    <Copy
                      :size="11"
                      style="color: #94a3b8; cursor: pointer;"
                      @click.stop="copyText(ip)"
                      title="复制解析IP"
                    />
                  </div>
                </div>
                <div v-else-if="row.resolve_status === 'failed'" style="color: #ef4444; font-size: 12px;">
                  ❌ DNS未解析或不存在
                </div>
                <div v-else style="color: #94a3b8; font-size: 12px;">
                  待比对检测
                </div>

                <!-- 状态标签 -->
                <div style="margin-top: 2px;">
                  <el-tag
                    v-if="row.resolve_status === 'matched'"
                    type="success"
                    size="small"
                    effect="light"
                    style="font-weight: 600;"
                  >
                    ✔ 一致
                  </el-tag>
                  <el-tag
                    v-else-if="row.resolve_status === 'mismatched'"
                    type="warning"
                    size="small"
                    effect="light"
                    style="font-weight: 600;"
                  >
                    ⚠ 记录不匹配
                  </el-tag>
                  <el-tag
                    v-else-if="row.resolve_status === 'failed'"
                    type="danger"
                    size="small"
                    effect="light"
                    style="font-weight: 600;"
                  >
                    ❌ 失败
                  </el-tag>
                  <el-tag
                    v-else
                    type="info"
                    size="small"
                    effect="light"
                  >
                    未检测
                  </el-tag>
                </div>
              </div>
            </template>
          </el-table-column>

          <!-- 4. 关联承载主机 (支持多台分行合并单元格展示) -->
          <el-table-column label="关联承载主机" min-width="220">
            <template #default="{ row }">
              <div v-if="getDomainHosts(row).length > 0" style="display: flex; flex-direction: column; gap: 5px;">
                <div
                  v-for="h in getDomainHosts(row)"
                  :key="h.id"
                  class="host-card-item"
                >
                  <div style="display: flex; align-items: center; gap: 5px;">
                    <span class="status-dot-mini" :class="h.status || 'online'"></span>
                    <Server :size="13" style="color: #2563eb;" />
                    <span style="font-weight: 600; color: #0f172a; font-size: 12.5px;">{{ h.hostname }}</span>
                  </div>
                  <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #64748b; margin-top: 1px;">
                    内网: <span style="color: #334155; font-weight: 600;">{{ h.private_ip }}</span>
                    <span v-if="h.public_ip" style="color: #2563eb; margin-left: 6px;">公网: {{ h.public_ip }}</span>
                  </div>
                </div>
              </div>
              <span v-else style="color: #cbd5e1; font-size: 12px;">未关联主机</span>
            </template>
          </el-table-column>

          <!-- 5. 服务端口 -->
          <el-table-column prop="port" label="服务端口" width="115" align="center">
            <template #default="{ row }">
              <span class="port-badge">{{ row.port || '80, 443' }}</span>
            </template>
          </el-table-column>

          <!-- 6. 环境 -->
          <el-table-column prop="env" label="环境" width="90" align="center">
            <template #default="{ row }">
              <span class="env-tag" :class="row.env">{{ getEnvLabel(row.env) }}</span>
            </template>
          </el-table-column>

          <!-- 7. 备注 -->
          <el-table-column prop="notes" label="备注说明" min-width="130" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.notes" style="color: #475569; font-size: 12.5px;">{{ row.notes }}</span>
              <span v-else style="color: #cbd5e1;">-</span>
            </template>
          </el-table-column>

          <!-- 8. 操作 -->
          <el-table-column label="操作" width="180" align="center" fixed="right">
            <template #default="{ row }">
              <div style="display: flex; align-items: center; justify-content: center; gap: 6px;">
                <el-button
                  size="small"
                  type="primary"
                  link
                  :loading="checkingId === row.id"
                  @click="handleCheckSingleDns(row)"
                  title="实时发起 DNS 解析并校验一致性"
                >
                  比对解析
                </el-button>
                <el-button size="small" type="primary" link @click="openEditDialog(row)">编辑</el-button>
                <el-popconfirm
                  title="确认删除该域名资产吗？"
                  confirm-button-text="确定"
                  cancel-button-text="取消"
                  @confirm="handleDelete(row.id)"
                >
                  <template #reference>
                    <el-button size="small" type="danger" link>删除</el-button>
                  </template>
                </el-popconfirm>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 16px;">
          <span style="font-size: 13px; color: #64748b;">
            共计 <b>{{ filteredDomains.length }}</b> 个公网域名资产
          </span>
          <el-pagination
            v-if="filteredDomains.length > pagination.size"
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :total="filteredDomains.length"
            layout="prev, pager, next"
          />
        </div>
      </div>
    </div>

    <!-- 新建/编辑弹窗 -->
    <DomainFormDialog ref="formDialogRef" :host-list="hostList" :meta-config="metaConfig" @saved="onDomainSaved" />
  </section>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Globe, Search, RefreshCw, ExternalLink, Copy, Server } from 'lucide-vue-next'
import OpsApi from '../api'
import DomainFormDialog from '../components/DomainFormDialog.vue'

const props = defineProps({
  metaConfig: {
    type: Object,
    default: () => ({ environments: [] })
  }
})

const emit = defineEmits(['data-changed'])

const loading = ref(false)
const checkingAll = ref(false)
const checkingId = ref(null)
const domainList = ref([])
const hostList = ref([])
const formDialogRef = ref(null)

const filter = reactive({
  keyword: '',
  env: '',
  resolve_status: ''
})

const pagination = reactive({
  page: 1,
  size: 50
})

const getEnvLabel = (envKey) => {
  const found = props.metaConfig.environments?.find(e => e.key === envKey)
  return found ? found.label : (envKey === 'prod' ? '生产' : '测试')
}

const copyText = (text) => {
  if (!text) return
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success({ message: `已复制: ${text}`, duration: 1500 })
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const parseIps = (ipStr) => {
  if (!ipStr) return []
  return ipStr.split(/[,，;\s\n]+/).map(s => s.trim()).filter(Boolean)
}

const isIpv6 = (ip) => {
  return ip && ip.includes(':')
}

const getDomainHosts = (row) => {
  if (row.hosts && row.hosts.length > 0) {
    return row.hosts
  }
  if (row.host) {
    return [row.host]
  }
  return []
}

const filteredDomains = computed(() => {
  return domainList.value.filter(item => {
    if (filter.env && item.env !== filter.env) return false
    if (filter.resolve_status && item.resolve_status !== filter.resolve_status) return false
    if (filter.keyword) {
      const kw = filter.keyword.trim().toLowerCase()
      const matchName = (item.domain_name || '').toLowerCase().includes(kw)
      const matchIp = (item.public_ip || '').toLowerCase().includes(kw)
      const matchResolved = (item.resolved_ip || '').toLowerCase().includes(kw)
      const matchNotes = (item.notes || '').toLowerCase().includes(kw)
      const hosts = getDomainHosts(item)
      const matchHost = hosts.some(h => (h.hostname || '').toLowerCase().includes(kw) || (h.private_ip || '').includes(kw))
      if (!matchName && !matchIp && !matchResolved && !matchNotes && !matchHost) return false
    }
    return true
  })
})

const pagedDomainList = computed(() => {
  const start = (pagination.page - 1) * pagination.size
  return filteredDomains.value.slice(start, start + pagination.size)
})

const fetchHosts = async () => {
  try {
    const res = await OpsApi.getHosts({ page: 1, size: 500 })
    hostList.value = res.data?.items || []
  } catch (e) {
    console.error('加载主机列表失败:', e)
  }
}

const fetchDomains = async (silent = false) => {
  if (!silent) loading.value = true
  try {
    const res = await OpsApi.getDomains({ page: 1, size: 200 })
    domainList.value = res.data?.items || []
  } catch (e) {
    if (!silent) ElMessage.error('获取域名资产失败')
  } finally {
    loading.value = false
  }
}

const onDomainSaved = async () => {
  await fetchDomains()
  emit('data-changed')
}

const handleCheckSingleDns = async (row) => {
  checkingId.value = row.id
  try {
    const res = await OpsApi.checkDomainDns(row.id)
    const data = res.data
    row.resolved_ip = data.resolved_ip
    row.resolve_status = data.resolve_status
    if (data.is_matched) {
      ElMessage.success({ message: `${row.domain_name}: 解析正常 (IPv4/IPv6已比对)`, duration: 3000 })
    } else if (data.resolve_status === 'mismatched') {
      ElMessage.warning({ message: `${row.domain_name}: ${data.message}`, duration: 4000 })
    } else {
      ElMessage.error({ message: `${row.domain_name}: DNS解析失败`, duration: 2500 })
    }
  } catch (e) {
    ElMessage.error('比对解析失败')
  } finally {
    checkingId.value = null
  }
}

const handleCheckAllDns = async () => {
  checkingAll.value = true
  try {
    const res = await OpsApi.checkAllDomainDns()
    ElMessage.success(`已完成 ${res.data?.length || 0} 个域名的 IPv4/IPv6 实际解析比对`)
    await fetchDomains(true)
  } catch (e) {
    ElMessage.error('批量比对失败')
  } finally {
    checkingAll.value = false
  }
}

const openCreateDialog = () => {
  formDialogRef.value?.open()
}

const openEditDialog = (row) => {
  formDialogRef.value?.open(row)
}

const handleDelete = async (id) => {
  try {
    await OpsApi.deleteDomain(id)
    ElMessage.success('域名资产已删除')
    await fetchDomains()
    emit('data-changed')
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchHosts()
  fetchDomains()
})

defineExpose({ fetchDomains })
</script>

<style scoped>
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
.host-card-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 4px 8px;
  display: flex;
  flex-direction: column;
}
.status-dot-mini {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
}
.status-dot-mini.offline {
  background: #ef4444;
}
.status-dot-mini.maintenance {
  background: #f59e0b;
}
</style>
