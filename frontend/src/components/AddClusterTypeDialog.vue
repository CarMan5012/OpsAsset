<template>
  <el-dialog v-model="visible" title="新增中间件/服务组件类型" width="460px" top="8vh" append-to-body destroy-on-close>
    <el-form :model="form" label-width="100px">
      <el-form-item label="类型标识*" required>
        <el-input v-model="form.key" placeholder="如: ClickHouse, Doris, Hadoop"></el-input>
      </el-form-item>
      <el-form-item label="组件全称*" required>
        <el-input v-model="form.label" placeholder="如: ClickHouse, Apache Doris"></el-input>
      </el-form-item>
      <el-form-item label="初始角色">
        <el-input v-model="form.initialRoles" placeholder="选填，多角色用逗号隔开；留空则默认无角色"></el-input>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleSave">添加</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['add'])

const visible = ref(false)
const form = ref({
  key: '',
  label: '',
  initialRoles: ''
})

const open = () => {
  form.value = { key: '', label: '', initialRoles: '' }
  visible.value = true
}

const handleSave = () => {
  if (!form.value.key || !form.value.label) {
    ElMessage.warning('类型标识与组件全称为必填')
    return
  }
  emit('add', { ...form.value })
  visible.value = false
}

defineExpose({ open })
</script>
