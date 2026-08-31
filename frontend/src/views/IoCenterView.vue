<template>
  <section class="tab-pane">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
      <!-- 批量导入卡片 -->
      <div class="ops-card">
        <h3 style="font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 14px; display: flex; align-items: center; gap: 6px;">
          <FileSpreadsheet :size="18" style="color: #10b981;" /> 批量导入主机资产
        </h3>

        <div style="margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between;">
          <el-checkbox v-model="importOverwrite" label="遇到已存在内网IP时覆盖更新"></el-checkbox>
          <el-button type="primary" link :loading="downloadingTemplate" @click="handleDownloadTemplate">
            <Download :size="13" style="margin-right: 4px;" /> 下载标准 Excel 模板
          </el-button>
        </div>

        <!-- 文件选择区 -->
        <div class="upload-zone" @click="triggerFileInput">
          <input type="file" ref="fileInputRef" style="display: none" accept=".xlsx,.xls,.csv" @change="handleFileSelected">
          <div style="margin-bottom: 8px;">
            <UploadCloud :size="38" style="color: #2563eb;" />
          </div>
          <div style="color: #0f172a; font-weight: 600;">
            {{ selectedFile ? selectedFile.name : '点击选择或拖拽 Excel / CSV 文件到此处' }}
          </div>
          <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
            支持格式：.xlsx, .xls, .csv (最大 10MB)
          </div>
        </div>

        <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
          <el-button type="primary" :disabled="!selectedFile" :loading="importing" @click="executeImport">
            开始导入并解析
          </el-button>
        </div>

        <!-- 导入结果展示 -->
        <div v-if="importResult" style="margin-top: 20px; padding: 14px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
          <h4 style="font-size: 14px; font-weight: 700; color: #059669; margin-bottom: 8px;">导入报告：</h4>
          <div style="display: flex; gap: 16px; font-size: 13px;">
            <span>总行数: <b>{{ importResult.total_rows }}</b></span>
            <span style="color: #059669;">新增: <b>{{ importResult.inserted_count }}</b></span>
            <span style="color: #2563eb;">更新: <b>{{ importResult.updated_count }}</b></span>
            <span style="color: #dc2626;">失败: <b>{{ importResult.failed_count }}</b></span>
          </div>
          <div v-if="importResult.errors && importResult.errors.length > 0" style="margin-top: 10px; max-height: 140px; overflow-y: auto;">
            <div style="font-size: 12px; color: #dc2626; margin-bottom: 4px; font-weight: 600;">解析与导入明细异常:</div>
            <div v-for="(err, idx) in importResult.errors" :key="idx" style="font-size: 11.5px; color: #dc2626; font-family: monospace; line-height: 1.5;">
              • {{ typeof err === 'object' ? `第 ${err.row || idx + 1} 行: ${err.message || JSON.stringify(err)}` : err }}
            </div>
          </div>
        </div>
      </div>

      <!-- 批量导出卡片 -->
      <div class="ops-card" style="display: flex; flex-direction: column;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px;">
          <h3 style="font-size: 15px; font-weight: 700; color: #0f172a; display: flex; align-items: center; gap: 6px; margin: 0;">
            <Download :size="18" style="color: #2563eb;" /> 批量导出主机数据
          </h3>
          <el-button type="primary" link @click="openExportModal">
            <Maximize2 :size="13" style="margin-right: 4px;" /> 打开独立导出弹窗
          </el-button>
        </div>

        <!-- 筛选与格式栏 -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 12px;">
          <div>
            <div style="font-size: 12px; color: #475569; font-weight: 600; margin-bottom: 4px;">过滤导出环境：</div>
            <el-select v-model="exportParams.env" placeholder="全部环境 (默认全量)" clearable @change="fetchPreviewData" style="width: 100%;">
              <el-option label="全部环境" value="" />
              <el-option v-for="env in metaConfig.environments" :key="env.key" :label="env.label" :value="env.key" />
            </el-select>
          </div>

          <div>
            <div style="font-size: 12px; color: #475569; font-weight: 600; margin-bottom: 4px;">导出文件格式：</div>
            <el-radio-group v-model="exportParams.format" size="default" style="margin-top: 2px;">
              <el-radio value="xlsx">Excel (.xlsx)</el-radio>
              <el-radio value="csv">CSV (.csv)</el-radio>
            </el-radio-group>
          </div>
        </div>

        <!-- 导出列勾选区域 -->
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; margin-bottom: 14px;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
            <div style="font-size: 12.5px; font-weight: 700; color: #0f172a; display: flex; align-items: center; gap: 4px;">
              <SlidersHorizontal :size="13" style="color: #2563eb;" /> 选择导出的数据列
              <span style="font-size: 11px; color: #64748b; font-weight: normal;">
                (已选 <b style="color: #2563eb;">{{ selectedColumns.length }}</b> / {{ allColumns.length }} 列)
              </span>
            </div>
            <div style="display: flex; gap: 4px; font-size: 12px;">
              <el-button link type="primary" size="small" @click="selectAllColumns">全选</el-button>
              <el-divider direction="vertical" />
              <el-button link type="primary" size="small" @click="invertColumns">反选</el-button>
              <el-divider direction="vertical" />
              <el-button link type="primary" size="small" @click="selectDefaultColumns">常用默认</el-button>
            </div>
          </div>

          <div style="display: flex; flex-wrap: wrap; gap: 6px; max-height: 85px; overflow-y: auto;">
            <el-checkbox-group v-model="selectedColumns" size="small">
              <el-checkbox
                v-for="col in allColumns"
                :key="col.key"
                :label="col.key"
                border
                style="margin: 2px !important;"
              >
                {{ col.label }}
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </div>

        <!-- 实时数据预览 -->
        <div style="margin-bottom: 12px; flex: 1;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
            <div style="font-size: 12.5px; font-weight: 700; color: #0f172a; display: flex; align-items: center; gap: 6px;">
              <Eye :size="13" style="color: #10b981;" /> 实时导出数据预览
              <el-button link type="primary" size="small" :loading="previewLoading" @click="fetchPreviewData" title="刷新最新数据">
                <RotateCw :size="12" style="margin-right: 2px;" /> 刷新数据
              </el-button>
            </div>
            <div style="font-size: 11.5px; color: #64748b;">
              共匹配 <b style="color: #2563eb;">{{ previewTotal }}</b> 台主机，展示前 {{ previewList.length }} 条 (按最新时间排序)
            </div>
          </div>

          <div style="border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden;" v-loading="previewLoading">
            <el-table
              :data="previewList"
              size="small"
              stripe
              border
              max-height="165px"
              style="width: 100%; font-size: 11.5px;"
              empty-text="暂无匹配数据"
            >

              <el-table-column
                v-for="colKey in activeColumnsKeys"
                :key="colKey"
                :prop="colKey"
                :label="getColumnLabel(colKey)"
                :min-width="getColumnMinWidth(colKey)"
                show-overflow-tooltip
              />
            </el-table>
          </div>
        </div>

        <!-- 底部导出操作 -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: auto; padding-top: 10px; border-top: 1px solid #f1f5f9;">
          <div style="font-size: 12px; color: #64748b;">
            即将导出 <b style="color: #2563eb;">{{ previewTotal }}</b> 台主机，<b style="color: #0f172a;">{{ selectedColumns.length }}</b> 个字段
          </div>
          <el-button
            type="primary"
            :loading="exporting"
            :disabled="selectedColumns.length === 0 || previewTotal === 0"
            @click="handleExport"
          >
            <Download :size="14" style="margin-right: 4px;" /> 立即导出并下载
          </el-button>
        </div>
      </div>
    </div>

    <!-- 独立高级导出弹窗 -->
    <HostExportDialog ref="hostExportDialogRef" :meta-config="metaConfig" />
  </section>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { FileSpreadsheet, Download, UploadCloud, SlidersHorizontal, Eye, Maximize2, RotateCw } from 'lucide-vue-next'
import OpsApi from '../api'
import HostExportDialog from '../components/HostExportDialog.vue'
import {
  HOST_EXPORT_COLUMNS,
  formatHostExportRow
} from '../utils'

const props = defineProps({
  metaConfig: { type: Object, required: true }
})
const emit = defineEmits(['data-changed'])

const importOverwrite = ref(true)
const selectedFile = ref(null)
const importing = ref(false)
const exporting = ref(false)
const downloadingTemplate = ref(false)
const importResult = ref(null)
const fileInputRef = ref(null)
const hostExportDialogRef = ref(null)

const allColumns = HOST_EXPORT_COLUMNS
const selectedColumns = ref(HOST_EXPORT_COLUMNS.filter(c => c.default).map(c => c.key))

const exportParams = reactive({
  env: '',
  format: 'xlsx'
})

// 预览数据
const rawPreviewHosts = ref([])
const previewTotal = ref(0)
const previewLoading = ref(false)

const activeColumnsKeys = computed(() => {
  return allColumns.filter(c => selectedColumns.value.includes(c.key)).map(c => c.key)
})

const previewList = computed(() => {
  return rawPreviewHosts.value.map((h, i) => formatHostExportRow(h, props.metaConfig, i))
})

const getColumnLabel = (key) => {
  const col = allColumns.find(c => c.key === key)
  return col ? col.label : key
}

const getColumnMinWidth = (key) => {
  const col = allColumns.find(c => c.key === key)
  return col ? `${col.minWidth || 110}` : '110'
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

const fetchPreviewData = async () => {
  previewLoading.value = true
  try {
    const params = {
      page: 1,
      size: 5,
      sort_by: 'id',
      sort_order: 'desc',
      _t: Date.now()
    }
    if (exportParams.env) params.env = exportParams.env
    const res = await OpsApi.getHosts(params)
    rawPreviewHosts.value = res.data.items || []
    previewTotal.value = res.data.total || 0
  } catch (e) {
    // 忽略预览获取异常
  } finally {
    previewLoading.value = false
  }
}

const openExportModal = () => {
  hostExportDialogRef.value?.open({
    filters: { env: exportParams.env }
  })
}

const handleDownloadTemplate = async () => {
  downloadingTemplate.value = true
  try {
    const res = await OpsApi.downloadTemplateBlob()
    const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = '主机资产导入模板.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
    ElMessage.success('导入模板下载成功')
  } catch (e) {
    window.open(OpsApi.getTemplateUrl(), '_blank')
  } finally {
    downloadingTemplate.value = false
  }
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileSelected = (e) => {
  if (e.target.files && e.target.files[0]) {
    selectedFile.value = e.target.files[0]
  }
}

const executeImport = async () => {
  if (!selectedFile.value) return
  importing.value = true
  importResult.value = null
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    const res = await OpsApi.importAssets(formData, importOverwrite.value)
    importResult.value = res.data
    ElMessage.success(`导入完成：新增 ${res.data.inserted_count} 台，更新 ${res.data.updated_count} 台`)
    selectedFile.value = null
    if (fileInputRef.value) fileInputRef.value.value = ''
    emit('data-changed')
    fetchPreviewData()
  } catch (e) {
    const msg = e.response?.data?.detail || e.message || '导入失败，请检查文件格式'
    ElMessage.error(msg)
  } finally {
    importing.value = false
  }
}

const handleExport = async () => {
  if (selectedColumns.value.length === 0) {
    ElMessage.warning('请至少选择一个导出数据列')
    return
  }

  exporting.value = true
  try {
    const params = {
      format: exportParams.format,
      columns: activeColumnsKeys.value.join(',')
    }
    if (exportParams.env) params.env = exportParams.env

    const res = await OpsApi.exportAssetsBlob(params)
    const ext = exportParams.format === 'csv' ? 'csv' : 'xlsx'
    const mimeType = ext === 'csv' ? 'text/csv;charset=utf-8;' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    const blob = new Blob([res.data], { type: mimeType })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `服务器资产清单_${exportParams.env || 'all'}_${new Date().toISOString().slice(0, 10)}.${ext}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
    ElMessage.success('资产清单导出下载成功')
  } catch (e) {
    const params = {
      format: exportParams.format,
      columns: activeColumnsKeys.value.join(',')
    }
    if (exportParams.env) params.env = exportParams.env
    window.open(OpsApi.getExportUrl(params), '_blank')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  fetchPreviewData()
})
</script>
