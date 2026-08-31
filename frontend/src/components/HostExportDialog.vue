<template>
  <el-dialog
    v-model="visible"
    title="导出主机资产数据"
    width="860px"
    class="pro-form-dialog host-export-modal"
    align-center
    destroy-on-close
    :close-on-click-modal="false"
  >
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div class="form-header-avatar" style="background: rgba(37, 99, 235, 0.1); color: #2563eb;">
            <Download :size="20" />
          </div>
          <div>
            <div style="font-size: 16px; font-weight: 700; color: #0f172a;">导出主机资产清单</div>
          </div>
        </div>
      </div>
    </template>

    <div class="export-dialog-content">
      <!-- 1. 导出设置面板 -->
      <div class="export-config-panel">
        <div class="panel-section">
          <div class="section-label">
            <Layers :size="14" style="color: #2563eb;" /> 导出范围与格式
          </div>
          <div class="config-row">
            <div class="config-item">
              <span class="sub-label">导出范围：</span>
              <el-radio-group v-model="exportScope" size="small" @change="refreshPreviewData">
                <el-radio-button value="all">
                  全部环境
                </el-radio-button>
                <el-radio-button
                  v-for="env in (metaConfig?.environments || [])"
                  :key="env.key"
                  :value="env.key"
                >
                  {{ env.label }}
                </el-radio-button>
                <el-radio-button v-if="selectedIds && selectedIds.length > 0" value="selected">
                  已选主机 ({{ selectedIds.length }} 台)
                </el-radio-button>
              </el-radio-group>
            </div>

            <div class="config-item">
              <span class="sub-label">文件格式：</span>
              <el-radio-group v-model="exportFormat" size="small">
                <el-radio-button value="xlsx">Excel (.xlsx)</el-radio-button>
                <el-radio-button value="csv">CSV (.csv)</el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </div>

        <!-- 2. 自定义列勾选区 -->
        <div class="panel-section" style="margin-top: 14px;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
            <div class="section-label">
              <SlidersHorizontal :size="14" style="color: #2563eb;" /> 选择导出的数据列
              <span style="font-size: 11.5px; color: #64748b; font-weight: normal; margin-left: 6px;">
                (已选 <b style="color: #2563eb;">{{ selectedColumns.length }}</b> / {{ allColumns.length }} 列)
              </span>
            </div>
            <!-- 快捷预设按钮组 -->
            <div class="preset-btn-group">
              <el-button link type="primary" size="small" @click="selectAllColumns">全选</el-button>
              <el-divider direction="vertical" />
              <el-button link type="primary" size="small" @click="invertColumns">反选</el-button>
              <el-divider direction="vertical" />
              <el-button link type="primary" size="small" @click="selectDefaultColumns">常用默认列</el-button>
              <el-divider direction="vertical" />
              <el-button link type="primary" size="small" @click="selectHardwareColumns">硬件规格列</el-button>
            </div>
          </div>

          <!-- 列选择卡片容器 -->
          <div class="column-chips-container">
            <el-checkbox-group v-model="selectedColumns" size="small">
              <el-checkbox
                v-for="col in allColumns"
                :key="col.key"
                :label="col.key"
                class="col-checkbox-tag"
                border
              >
                {{ col.label }}
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </div>
      </div>

      <!-- 3. 数据实时预览表格区 -->
      <div class="preview-section" style="margin-top: 16px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
          <div style="font-size: 13px; font-weight: 700; color: #0f172a; display: flex; align-items: center; gap: 8px;">
            <Eye :size="14" style="color: #10b981;" /> 实时导出数据预览
            <el-button v-if="selectedColumns.length > 0" link type="primary" size="small" :loading="previewLoading" @click="refreshPreviewData" title="刷新最新数据">
              <RotateCw :size="12" style="margin-right: 2px;" /> 刷新数据
            </el-button>
          </div>
          <div v-if="selectedColumns.length > 0" style="font-size: 12px; color: #64748b;">
            共匹配 <b style="color: #2563eb;">{{ previewTotal }}</b> 条记录
          </div>
        </div>

        <!-- 未勾选任何列时的空状态展示 -->
        <div v-if="selectedColumns.length === 0" style="padding: 28px 16px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; text-align: center;">
          <SlidersHorizontal :size="26" style="color: #94a3b8; margin: 0 auto 6px; display: block;" />
          <div style="font-size: 13px; font-weight: 600; color: #475569;">未勾选任何导出字段</div>
          <div style="font-size: 11.5px; color: #94a3b8; margin-top: 3px;">请在上方勾选需要导出的数据列以生成预览与文件</div>
        </div>

        <!-- 预览表格 -->
        <div v-else class="preview-table-wrapper" v-loading="previewLoading">
          <el-table
            :data="previewList"
            size="small"
            border
            stripe
            max-height="220px"
            style="width: 100%; font-size: 12px;"
            empty-text="暂无匹配数据"
          >

            <el-table-column
              v-for="colKey in activeColumnsKeys"
              :key="colKey"
              :prop="colKey"
              :label="getColumnLabel(colKey)"
              :min-width="getColumnMinWidth(colKey)"
              :align="colKey === 'index' ? 'center' : (['env', 'status'].includes(colKey) ? 'center' : 'left')"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <!-- 针对特殊列的美化展示 -->
                <span v-if="colKey === 'index'" style="color: #64748b; font-weight: 600;">{{ row.index }}</span>
                <span v-else-if="colKey === 'hostname'" style="font-weight: 600; color: #0f172a;">{{ row.hostname }}</span>
                <span v-else-if="colKey === 'private_ip'" style="font-family: 'JetBrains Mono'; color: #2563eb; font-weight: 600;">{{ row.private_ip }}</span>
                <span v-else-if="colKey === 'env'" class="env-tag" :class="getRawEnvClass(row._raw?.env)">{{ row.env }}</span>
                <span v-else-if="colKey === 'status'">
                  <span class="preview-status-pill" :style="getStatusPillStyle(row._raw?.status)">
                    {{ row.status }}
                  </span>
                </span>
                <span v-else style="color: #334155;">{{ row[colKey] || '' }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 预览表格分页条 -->
        <div v-if="selectedColumns.length > 0 && previewTotal > 0" style="display: flex; justify-content: flex-end; margin-top: 8px;">
          <el-pagination
            v-model:current-page="previewPage"
            v-model:page-size="previewPageSize"
            :page-sizes="[5, 10, 20]"
            :total="previewTotal"
            size="small"
            layout="total, sizes, prev, pager, next"
            @size-change="refreshPreviewData"
            @current-change="refreshPreviewData"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div style="font-size: 12px; color: #64748b;">
          导出文件：<b style="color: #0f172a;">服务器资产清单.{{ exportFormat }}</b>
          （包含 {{ selectedColumns.length }} 个字段）
        </div>
        <div style="display: flex; gap: 8px;">
          <el-button @click="visible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="exporting"
            :disabled="selectedColumns.length === 0 || previewTotal === 0"
            @click="executeExport"
          >
            <Download :size="14" style="margin-right: 4px;" /> 立即导出并下载
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Layers, SlidersHorizontal, Eye, RotateCw } from 'lucide-vue-next'
import OpsApi from '../api'
import {
  HOST_EXPORT_COLUMNS,
  formatHostExportRow,
  getStatusStyle
} from '../utils'

const props = defineProps({
  metaConfig: { type: Object, required: true }
})

const visible = ref(false)
const exporting = ref(false)
const previewLoading = ref(false)

const allColumns = HOST_EXPORT_COLUMNS
const selectedColumns = ref(HOST_EXPORT_COLUMNS.filter(c => c.default).map(c => c.key))

const exportFormat = ref('xlsx')
const exportScope = ref('all') // 'all' | 'selected' | '{env.key}'
const selectedIds = ref([])
const currentFilters = reactive({})

// 预览数据与分页
const previewPage = ref(1)
const previewPageSize = ref(10)
const rawHostsData = ref([])
const previewTotal = ref(0)

// 打开弹窗方法
const open = (options = {}) => {
  const { filters = {}, ids = [] } = options
  Object.assign(currentFilters, filters)
  selectedIds.value = ids || []
  previewPage.value = 1

  if (selectedIds.value.length > 0) {
    exportScope.value = 'selected'
  } else if (filters.env) {
    exportScope.value = filters.env
  } else {
    exportScope.value = 'all'
  }

  // 重置默认勾选列（若为空）
  if (selectedColumns.value.length === 0) {
    selectDefaultColumns()
  }

  visible.value = true
  refreshPreviewData()
}

// 勾选中的有效列
const activeColumnsKeys = computed(() => {
  // 按照 allColumns 的定义顺序排列，保证列顺序自然稳定
  return allColumns.filter(c => selectedColumns.value.includes(c.key)).map(c => c.key)
})

// 格式化后的预览行
const previewList = computed(() => {
  return rawHostsData.value.map((h, i) => {
    const globalIdx = (previewPage.value - 1) * previewPageSize.value + i
    const formatted = formatHostExportRow(h, props.metaConfig, globalIdx)
    return {
      ...formatted,
      _raw: h
    }
  })
})

const getColumnLabel = (key) => {
  const col = allColumns.find(c => c.key === key)
  return col ? col.label : key
}

const getColumnMinWidth = (key) => {
  const col = allColumns.find(c => c.key === key)
  return col ? `${col.minWidth || 120}` : '120'
}

const getRawEnvClass = (env) => {
  return env || 'prod'
}

const getStatusPillStyle = (status) => {
  const st = getStatusStyle(status, props.metaConfig)
  return {
    backgroundColor: st.backgroundColor,
    color: st.color,
    borderColor: st.borderColor
  }
}

// 预览表格跨行智能合并公网 IP (与导出及列表展示一致)
const previewSpanMethod = ({ row, column, rowIndex }) => {
  if (column && (column.property === 'public_ip' || column.label === '外网IP' || column.label === '外网 IP')) {
    const pubIp = (row.public_ip || '').trim()
    if (!pubIp || pubIp === '-') return { rowspan: 1, colspan: 1 }

    const items = previewList.value
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

// 快捷操作
const selectAllColumns = () => {
  selectedColumns.value = allColumns.map(c => c.key)
}

const invertColumns = () => {
  const current = new Set(selectedColumns.value)
  selectedColumns.value = allColumns.filter(c => !current.has(c.key)).map(c => c.key)
}

const selectDefaultColumns = () => {
  selectedColumns.value = allColumns.filter(c => c.default).map(c => c.key)
}

const selectHardwareColumns = () => {
  const hwKeys = ['index', 'hostname', 'private_ip', 'cpu_cores', 'memory_gb', 'disk_gb', 'arch', 'os', 'kernel_version', 'status', 'env']
  selectedColumns.value = allColumns.filter(c => hwKeys.includes(c.key)).map(c => c.key)
}

// 刷新预览数据
const refreshPreviewData = async () => {
  previewLoading.value = true
  try {
    const params = {
      page: previewPage.value,
      size: previewPageSize.value,
      sort_by: currentFilters.sort_by || 'id',
      sort_order: currentFilters.sort_order || 'desc',
      _t: Date.now()
    }

    if (exportScope.value === 'selected' && selectedIds.value.length > 0) {
      // 勾选主机预览
      const res = await OpsApi.getHosts({ page: 1, size: 500, sort_by: currentFilters.sort_by || 'id', sort_order: currentFilters.sort_order || 'desc' })
      const allFetched = res.data.items || []
      const matched = allFetched.filter(h => selectedIds.value.includes(h.id))
      previewTotal.value = matched.length
      const start = (previewPage.value - 1) * previewPageSize.value
      rawHostsData.value = matched.slice(start, start + previewPageSize.value)
    } else {
      // 指定环境或全量
      if (exportScope.value && exportScope.value !== 'all') {
        params.env = exportScope.value
      }
      if (currentFilters.keyword) params.keyword = currentFilters.keyword
      if (currentFilters.status) params.status = currentFilters.status
      if (currentFilters.arch) params.arch = currentFilters.arch
      if (currentFilters.cluster_id) params.cluster_id = currentFilters.cluster_id

      const res = await OpsApi.getHosts(params)
      rawHostsData.value = res.data.items || []
      previewTotal.value = res.data.total || 0
    }
  } catch (e) {
    ElMessage.error('加载预览数据失败')
  } finally {
    previewLoading.value = false
  }
}

// 执行导出
const executeExport = async () => {
  if (selectedColumns.value.length === 0) {
    ElMessage.warning('请至少选择一个需要导出的数据列')
    return
  }

  exporting.value = true
  try {
    const params = {
      format: exportFormat.value,
      columns: activeColumnsKeys.value.join(','),
      sort_by: currentFilters.sort_by || 'id',
      sort_order: currentFilters.sort_order || 'desc'
    }

    let envLabel = ''
    if (exportScope.value === 'selected' && selectedIds.value.length > 0) {
      params.ids = selectedIds.value.join(',')
      envLabel = '_已选主机'
    } else if (exportScope.value && exportScope.value !== 'all') {
      params.env = exportScope.value
      const foundEnv = (props.metaConfig?.environments || []).find(e => e.key === exportScope.value)
      envLabel = `_${foundEnv ? foundEnv.label : exportScope.value}`
    } else {
      if (currentFilters.keyword) params.keyword = currentFilters.keyword
      if (currentFilters.status) params.status = currentFilters.status
      if (currentFilters.arch) params.arch = currentFilters.arch
      if (currentFilters.cluster_id) params.cluster_id = currentFilters.cluster_id
      envLabel = '_全部环境'
    }

    const res = await OpsApi.exportAssetsBlob(params)
    const ext = exportFormat.value === 'csv' ? 'csv' : 'xlsx'
    const mimeType = ext === 'csv' ? 'text/csv;charset=utf-8;' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    const blob = new Blob([res.data], { type: mimeType })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `主机资产清单${envLabel}_${new Date().toISOString().slice(0, 10)}.${ext}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)

    ElMessage.success('主机资产清单导出下载成功！')
    visible.value = false
  } catch (e) {
    ElMessage.error('导出失败，请重试')
  } finally {
    exporting.value = false
  }
}

defineExpose({
  open
})
</script>

<style scoped>
.export-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.export-config-panel {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px 16px;
}

.section-label {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 6px;
}

.config-row {
  display: flex;
  align-items: center;
  gap: 28px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sub-label {
  font-size: 12.5px;
  color: #475569;
  font-weight: 600;
}

.preset-btn-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.column-chips-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
  padding: 10px;
  background: #ffffff;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  max-height: 120px;
  overflow-y: auto;
}

.col-checkbox-tag {
  margin-right: 0 !important;
  margin-bottom: 0 !important;
}

.preview-table-wrapper {
  background: #ffffff;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.preview-status-pill {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid transparent;
}
</style>
