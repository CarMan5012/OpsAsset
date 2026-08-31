<template>
  <el-dialog
    v-model="visible"
    width="580px"
    class="pro-form-dialog"
    top="5vh"
    append-to-body
    destroy-on-close
    :close-on-click-modal="false"
  >
    <template #header>
      <div style="display: flex; align-items: center; gap: 10px;">
        <div class="form-header-avatar" style="width: 34px; height: 34px; border-radius: 8px; background: #eff6ff; color: #2563eb; display: flex; align-items: center; justify-content: center;">
          <Globe :size="17" />
        </div>
        <div>
          <div style="font-size: 15.5px; font-weight: 700; color: #0f172a;">
            {{ isEdit ? '编辑域名资产' : '添加域名资产' }}
          </div>
        </div>
      </div>
    </template>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="pro-modal-form">
      <!-- 1. 域名 -->
      <el-form-item label="公网域名*" prop="domain_name">
        <el-input
          v-model="form.domain_name"
          placeholder="例如: www.hsh.139sc.com 或 api.example.com"
          clearable
          @blur="cleanDomainInput"
        >
          <template #prefix>
            <Globe :size="14" style="color: #94a3b8;" />
          </template>
        </el-input>
      </el-form-item>

      <!-- 2. 绑定公网IP (多选下拉 + 自定义输入) 与 服务端口 (2列排布) -->
      <div class="form-row-2col">
        <el-form-item label="绑定公网 IP (支持选择或回车输入多个 IPv4/IPv6)">
          <el-select
            v-model="form.public_ips"
            multiple
            filterable
            allow-create
            default-first-option
            collapse-tags
            collapse-tags-tooltip
            placeholder="请勾选或输入IP按回车"
            style="width: 100%;"
          >
            <el-option
              v-for="item in existingPublicIps"
              :key="item.ip"
              :label="item.ip"
              :value="item.ip"
            >
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 12.5px;">{{ item.ip }}</span>
                <span style="color: #64748b; font-size: 11.5px; margin-left: 8px;">{{ item.hostname }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="对外服务端口" prop="port">
          <el-input v-model="form.port" placeholder="如: 80, 443" clearable />
        </el-form-item>
      </div>

      <!-- 3. 所属环境 与 关联承载主机 (100% 联动字典配置) -->
      <div class="form-row-2col">
        <el-form-item label="所属运行环境*" prop="env">
          <el-select v-model="form.env" style="width: 100%;">
            <el-option
              v-for="env in envOptions"
              :key="env.key"
              :label="env.label"
              :value="env.key"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="关联承载主机 (支持多选2台及以上)">
          <el-select
            v-model="form.bound_host_ids"
            placeholder="可选择多台承载主机"
            multiple
            filterable
            collapse-tags
            collapse-tags-tooltip
            style="width: 100%;"
          >
            <el-option
              v-for="h in hostOptions"
              :key="h.id"
              :label="`${h.hostname} (${h.private_ip}${h.public_ip ? ' / 公网:' + h.public_ip : ''})`"
              :value="h.id"
            />
          </el-select>
        </el-form-item>
      </div>

      <!-- 4. 备注 -->
      <el-form-item label="业务备注说明" prop="notes" style="margin-bottom: 0;">
        <el-input
          v-model="form.notes"
          placeholder="例如: 阿里云DNS解析 / 核心双机网关 / SSL到期日等"
          clearable
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div style="display: flex; justify-content: flex-end; gap: 8px;">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存修改' : '确认添加' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Globe } from 'lucide-vue-next'
import OpsApi from '../api'

const props = defineProps({
  hostList: {
    type: Array,
    default: () => []
  },
  metaConfig: {
    type: Object,
    default: () => ({ environments: [] })
  }
})

const emit = defineEmits(['saved'])

const visible = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const currentId = ref(null)

const envOptions = computed(() => {
  if (props.metaConfig?.environments && props.metaConfig.environments.length > 0) {
    return props.metaConfig.environments
  }
  return [
    { key: 'prod', label: '生产环境' },
    { key: 'test', label: '测试环境' }
  ]
})

const form = reactive({
  domain_name: '',
  public_ips: [],
  port: '80, 443',
  env: 'prod',
  bound_host_ids: [],
  notes: ''
})

const rules = {
  domain_name: [
    { required: true, message: '请输入域名', trigger: 'blur' }
  ]
}

const hostOptions = computed(() => {
  return props.hostList || []
})

// 提取已有主机的公网 IP 列表，供多选下拉框选择
const existingPublicIps = computed(() => {
  const ips = []
  const seen = new Set()
  for (const h of hostOptions.value) {
    if (h.public_ip) {
      const parts = h.public_ip.split(/[,，;\s\n]+/)
      for (const p of parts) {
        const clean = p.trim()
        if (clean && !seen.has(clean)) {
          seen.add(clean)
          ips.push({
            ip: clean,
            hostname: h.hostname,
            env: h.env
          })
        }
      }
    }
  }
  return ips
})

const cleanDomainInput = () => {
  if (form.domain_name) {
    let s = form.domain_name.trim().toLowerCase()
    s = s.replace(/^https?:\/\//, '').split('/')[0].split(':')[0]
    form.domain_name = s
  }
}

const open = (row = null) => {
  const defaultEnv = envOptions.value[0]?.key || 'prod'
  if (row) {
    isEdit.value = true
    currentId.value = row.id
    form.domain_name = row.domain_name || ''
    form.public_ips = row.public_ip
      ? row.public_ip.split(/[,，;\s\n]+/).map(s => s.trim()).filter(Boolean)
      : []
    form.port = row.port || '80, 443'
    form.env = row.env || defaultEnv
    form.bound_host_ids = row.bound_host_ids?.length
      ? [...row.bound_host_ids]
      : (row.bound_host_id ? [row.bound_host_id] : [])
    form.notes = row.notes || ''
  } else {
    isEdit.value = false
    currentId.value = null
    form.domain_name = ''
    form.public_ips = []
    form.port = '80, 443'
    form.env = defaultEnv
    form.bound_host_ids = []
    form.notes = ''
  }
  visible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    cleanDomainInput()
    submitting.value = true
    try {
      const publicIpStr = (form.public_ips || []).join(', ')
      const payload = {
        domain_name: form.domain_name,
        public_ip: publicIpStr,
        port: form.port,
        env: form.env,
        bound_host_ids: form.bound_host_ids,
        bound_host_id: form.bound_host_ids.length ? form.bound_host_ids[0] : null,
        notes: form.notes
      }
      if (isEdit.value) {
        await OpsApi.updateDomain(currentId.value, payload)
        ElMessage.success('域名资产修改成功')
      } else {
        await OpsApi.createDomain(payload)
        ElMessage.success('域名资产添加成功')
      }
      visible.value = false
      emit('saved')
    } catch (e) {
      const msg = e.response?.data?.detail || e.message || '操作失败'
      ElMessage.error(msg)
    } finally {
      submitting.value = false
    }
  })
}

defineExpose({ open })
</script>
