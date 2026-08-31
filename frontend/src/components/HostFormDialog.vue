<template>
  <el-dialog v-model="visible" width="680px" class="pro-form-dialog" top="4vh" append-to-body destroy-on-close>
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div class="form-header-avatar">
            <Server :size="18" />
          </div>
          <div>
            <div style="font-size: 16px; font-weight: 700; color: #0f172a;">
              {{ isEdit ? '编辑主机资产' : '录入新主机资产' }}
            </div>
          </div>
        </div>
        <span v-if="form.env" class="env-tag" :class="form.env">
          {{ getEnvLabel(form.env) }}
        </span>
      </div>
    </template>

    <el-form :model="form" label-position="top" class="pro-modal-form">
      <div class="form-section-title" style="display: flex; align-items: center; gap: 6px; font-weight: 700; color: #0f172a; margin-bottom: 12px;">
        <ShieldCheck :size="16" style="color: #2563eb;" /> 基础与网络标识
      </div>
      <div class="form-row-2col" style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 0;">
        <el-form-item label="主机名称 (Hostname)*" required>
          <el-input v-model="form.hostname" placeholder="如: k8s-master-01"></el-input>
        </el-form-item>
        <el-form-item label="所属运行环境*" required>
          <el-select v-model="form.env" style="width: 100%;">
            <el-option v-for="env in metaConfig.environments" :key="env.key" :label="env.label" :value="env.key" />
          </el-select>
        </el-form-item>
      </div>

      <div class="form-row-2col" style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 0;">
        <el-form-item label="内网 IP (自然唯一主键)*" required>
          <el-input v-model="form.private_ip" placeholder="如: 192.168.1.10" :disabled="isEdit"></el-input>
        </el-form-item>
        <el-form-item label="外网/公网 IP (支持填多个)">
          <el-input v-model="form.public_ip" placeholder="如: 120.55.1.1, 120.55.1.2"></el-input>
        </el-form-item>
      </div>

      <div class="form-row-2col" style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 0;">
        <el-form-item label="当前主机运行状态*" required>
          <el-select v-model="form.status" style="width: 100%;">
            <el-option v-for="st in metaConfig.host_statuses" :key="st.key" :label="st.label" :value="st.key">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span :style="{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: st.color || '#94a3b8' }"></span>
                <span>{{ st.label }}</span>
                <span style="color: #94a3b8; font-size: 11px; margin-left: auto;">{{ st.key }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="常用开放端口清单">
          <el-input v-model="form.open_ports" placeholder="如: 22, 80, 443, 6443, 30000-32767"></el-input>
        </el-form-item>
      </div>

      <div class="form-section-title" style="margin-top: 16px; display: flex; align-items: center; gap: 6px; font-weight: 700; color: #0f172a; margin-bottom: 12px;">
        <Cpu :size="16" style="color: #2563eb;" /> 硬件与操作系统规格
      </div>
      <!-- 硬件规格三列一行 -->
      <div class="form-row-3col" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 0;">
        <el-form-item label="CPU 核心数 (核)*" required>
          <el-input-number v-model="form.cpu_cores" :min="1" :max="1024" style="width: 100%;"></el-input-number>
        </el-form-item>
        <el-form-item label="物理内存 (GB)*" required>
          <el-input-number v-model="form.memory_gb" :min="1" :max="4096" style="width: 100%;"></el-input-number>
        </el-form-item>
        <el-form-item label="数据盘容量 (GB)*" required>
          <el-input-number v-model="form.disk_gb" :min="0" :max="100000" style="width: 100%;"></el-input-number>
        </el-form-item>
      </div>

      <!-- 架构与系统三列一行 -->
      <div class="form-row-3col" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 0;">
        <el-form-item label="CPU 架构*" required>
          <el-select v-model="form.arch" style="width: 100%;">
            <el-option v-for="a in metaConfig.cpu_architectures" :key="a.key" :label="a.label" :value="a.key" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作系统发行版">
          <el-select v-model="form.os" filterable allow-create default-first-option placeholder="选择或输入OS" style="width: 100%;">
            <el-option v-for="os in metaConfig.common_os_list" :key="os" :label="os" :value="os" />
          </el-select>
        </el-form-item>
        <el-form-item label="Linux 内核版本">
          <el-input v-model="form.kernel_version" placeholder="如: 5.15.0-89-generic" style="width: 100%;"></el-input>
        </el-form-item>
      </div>

      <el-form-item label="备注说明" style="margin-top: 4px;">
        <el-input type="textarea" v-model="form.notes" rows="2" placeholder="机房机架位、特殊用途说明等"></el-input>
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
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Server, ShieldCheck, Cpu } from 'lucide-vue-next'
import OpsApi from '../api'

const props = defineProps({
  metaConfig: { type: Object, required: true }
})
const emit = defineEmits(['saved'])

const visible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const form = ref({
  id: null,
  hostname: '',
  private_ip: '',
  public_ip: '',
  env: 'prod',
  status: 'online',
  cpu_cores: 4,
  memory_gb: 8,
  disk_gb: 100,
  os: 'CentOS 7.9',
  arch: 'amd64',
  kernel_version: '',
  open_ports: '22, 80, 443',
  notes: ''
})

const getEnvLabel = (envKey) => {
  if (!props.metaConfig?.environments) return envKey
  const item = props.metaConfig.environments.find(e => e.key === envKey)
  return item ? item.label : envKey
}

const open = (row = null) => {
  if (row) {
    isEdit.value = true
    form.value = {
      id: row.id,
      hostname: row.hostname || '',
      private_ip: row.private_ip || '',
      public_ip: row.public_ip || '',
      env: row.env || 'prod',
      status: row.status || 'online',
      cpu_cores: row.cpu_cores || 0,
      memory_gb: row.memory_gb || 0,
      disk_gb: row.disk_gb || 0,
      os: row.os || '',
      arch: row.arch || 'amd64',
      kernel_version: row.kernel_version || '',
      open_ports: row.open_ports || '',
      notes: row.notes || ''
    }
  } else {
    isEdit.value = false
    const defaultEnv = props.metaConfig.environments?.[0]?.key || 'prod'
    const defaultStatus = props.metaConfig.host_statuses?.[0]?.key || 'online'
    const defaultArch = props.metaConfig.cpu_architectures?.[0]?.key || 'amd64'
    const defaultOs = props.metaConfig.common_os_list?.[0] || 'CentOS 7.9'
    form.value = {
      id: null,
      hostname: '',
      private_ip: '',
      public_ip: '',
      env: defaultEnv,
      status: defaultStatus,
      cpu_cores: 4,
      memory_gb: 8,
      disk_gb: 100,
      os: defaultOs,
      arch: defaultArch,
      kernel_version: '',
      open_ports: '22, 80, 443',
      notes: ''
    }
  }
  visible.value = true
}

const handleSave = async () => {
  if (!form.value.hostname || !form.value.private_ip) {
    ElMessage.warning('主机名与内网IP为必填项')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await OpsApi.updateHost(form.value.id, form.value)
      ElMessage.success('主机资产更新成功')
    } else {
      await OpsApi.createHost(form.value)
      ElMessage.success('新增主机资产成功')
    }
    visible.value = false
    emit('saved')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存主机失败')
  } finally {
    saving.value = false
  }
}

defineExpose({ open })
</script>
