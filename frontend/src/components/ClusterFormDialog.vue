<template>
  <el-dialog v-model="visible" width="540px" class="pro-form-dialog" top="5vh" append-to-body destroy-on-close>
    <template #header>
      <div style="display: flex; align-items: center; gap: 12px;">
        <div class="form-header-avatar" style="background: #ffffff; border: 1px solid #e2e8f0; padding: 4px;">
          <span v-html="getMiddlewareLogo(form.cluster_type, 24)" style="display: flex; align-items: center; justify-content: center;"></span>
        </div>
        <div>
          <div style="font-size: 16px; font-weight: 700; color: #0f172a;">
            {{ isEdit ? '编辑集群' : '新增集群' }}
          </div>
        </div>
      </div>
    </template>

    <el-form :model="form" label-position="top" class="pro-modal-form">
      <el-form-item label="集群名称" required>
        <el-input v-model="form.name" placeholder="如 生产 Redis"></el-input>
      </el-form-item>

      <div class="form-row-2col">
        <el-form-item label="组件类型" required>
          <el-select v-model="form.cluster_type" placeholder="选择类型" style="width: 100%;">
            <el-option v-for="ct in metaConfig.cluster_types" :key="ct.key"
              :label="ct.label" :value="ct.key" />
          </el-select>
        </el-form-item>
        <el-form-item label="环境" required>
          <el-select v-model="form.env" placeholder="选择环境" style="width: 100%;">
            <el-option v-for="env in metaConfig.environments" :key="env.key" :label="env.label" :value="env.key" />
          </el-select>
        </el-form-item>
      </div>

      <div class="form-row-2col">
        <el-form-item label="服务端口">
          <el-input v-model="form.port" placeholder="如 6443"></el-input>
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="form.version" placeholder="如 v1.28.2"></el-input>
        </el-form-item>
      </div>

      <el-form-item label="用途" style="margin-top: 4px;">
        <el-input type="textarea" v-model="form.description" rows="2" placeholder="选填"></el-input>
      </el-form-item>
    </el-form>

    <template #footer>
      <div style="display: flex; justify-content: flex-end; gap: 8px;">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import OpsApi from '../api'
import { getMiddlewareLogo } from '../utils'

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
  cluster_type: '',
  port: '',
  version: '',
  env: '',
  description: ''
})

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
    form.value = {
      id: null,
      name: '',
      cluster_type: '',
      port: '',
      version: '',
      env: '',
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
  if (!form.value.cluster_type || !form.value.env) {
    ElMessage.warning('请选择组件类型和环境')
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
