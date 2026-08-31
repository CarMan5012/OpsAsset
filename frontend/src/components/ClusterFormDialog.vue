<template>
  <el-dialog v-model="visible" width="540px" class="pro-form-dialog" top="5vh" append-to-body destroy-on-close>
    <template #header>
      <div style="display: flex; align-items: center; gap: 12px;">
        <div class="form-header-avatar" style="background: #ffffff; border: 1px solid #e2e8f0; padding: 4px;">
          <span v-html="getMiddlewareLogo(form.cluster_type, 24)" style="display: flex; align-items: center; justify-content: center;"></span>
        </div>
        <div>
          <div style="font-size: 16px; font-weight: 700; color: #0f172a;">
            {{ isEdit ? '编辑服务/集群' : '创建新服务/集群' }}
          </div>
        </div>
      </div>
    </template>

    <el-form :model="form" label-position="top" class="pro-modal-form">
      <el-form-item label="服务/集群名称*" required>
        <el-input v-model="form.name" placeholder="如: 生产k8s核心集群、生产Redis主从"></el-input>
      </el-form-item>

      <div class="form-row-2col">
        <el-form-item label="组件/中间件类型*" required>
          <el-select v-model="form.cluster_type" @change="onClusterTypeChange" style="width: 100%;">
            <el-option v-for="ct in metaConfig.cluster_types" :key="ct.key"
              :label="ct.label === ct.key ? ct.label : `${ct.label} (${ct.key})`" :value="ct.key" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属运行环境*" required>
          <el-select v-model="form.env" style="width: 100%;">
            <el-option v-for="env in metaConfig.environments" :key="env.key" :label="env.label" :value="env.key" />
          </el-select>
        </el-form-item>
      </div>

      <div class="form-row-2col">
        <el-form-item label="默认对外服务端口">
          <el-input v-model="form.port" placeholder="如: 6443, 30000-32767"></el-input>
        </el-form-item>
        <el-form-item label="软件版本号 (Version)">
          <el-input v-model="form.version" placeholder="如: v1.28.2, 7.2.4"></el-input>
        </el-form-item>
      </div>

      <el-form-item label="业务用途描述" style="margin-top: 4px;">
        <el-input type="textarea" v-model="form.description" rows="2" placeholder="用于哪些核心业务线、数据备份要求等"></el-input>
      </el-form-item>
    </el-form>

    <template #footer>
      <div style="display: flex; justify-content: flex-end; gap: 8px;">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ isEdit ? '保存更新' : '立即创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import OpsApi from '../api'
import { getMiddlewareLogo, getDefaultPortForType } from '../utils'

const props = defineProps({
  metaConfig: { type: Object, required: true }
})
const emit = defineEmits(['saved'])

const visible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const form = ref({
  id: null,
  name: '',
  cluster_type: 'K8s',
  port: '6443, 30000-32767',
  version: '',
  env: 'prod',
  description: ''
})

const onClusterTypeChange = (newType) => {
  const defaultPort = getDefaultPortForType(newType, props.metaConfig)
  if (defaultPort && !form.value.port) {
    form.value.port = defaultPort
  }
}

const open = (row = null) => {
  if (row) {
    isEdit.value = true
    form.value = {
      id: row.id,
      name: row.name || '',
      cluster_type: row.cluster_type || 'K8s',
      port: row.port || '',
      version: row.version || '',
      env: row.env || 'prod',
      description: row.description || ''
    }
  } else {
    isEdit.value = false
    const defaultType = props.metaConfig.cluster_types?.[0]?.key || 'K8s'
    const defaultEnv = props.metaConfig.environments?.[0]?.key || 'prod'
    const defaultPort = getDefaultPortForType(defaultType, props.metaConfig)
    form.value = {
      id: null,
      name: '',
      cluster_type: defaultType,
      port: defaultPort,
      version: '',
      env: defaultEnv,
      description: ''
    }
  }
  visible.value = true
}

const handleSave = async () => {
  if (!form.value.name) {
    ElMessage.warning('服务/集群名称为必填项')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await OpsApi.updateCluster(form.value.id, form.value)
      ElMessage.success('集群配置与版本更新成功')
    } else {
      await OpsApi.createCluster(form.value)
      ElMessage.success('新服务/集群创建成功')
    }
    visible.value = false
    emit('saved')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存集群失败')
  } finally {
    saving.value = false
  }
}

defineExpose({ open })
</script>
