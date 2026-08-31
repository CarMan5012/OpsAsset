import { createApp } from 'vue'
import ElementPlus, { ElMessage } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import './assets/style.css'
import App from './App.vue'

// 优化 ElMessage 默认时长（轻快迅速）与防刷屏机制
if (ElMessage) {
  const origSuccess = ElMessage.success
  const origWarning = ElMessage.warning
  const origError = ElMessage.error
  const origInfo = ElMessage.info

  ElMessage.success = (options) => {
    if (typeof options === 'string') {
      return origSuccess({ message: options, duration: 1200, grouping: true, showClose: true })
    }
    return origSuccess({ duration: 1200, grouping: true, showClose: true, ...options })
  }

  ElMessage.warning = (options) => {
    if (typeof options === 'string') {
      return origWarning({ message: options, duration: 1800, grouping: true, showClose: true })
    }
    return origWarning({ duration: 1800, grouping: true, showClose: true, ...options })
  }

  ElMessage.error = (options) => {
    if (typeof options === 'string') {
      return origError({ message: options, duration: 2200, grouping: true, showClose: true })
    }
    return origError({ duration: 2200, grouping: true, showClose: true, ...options })
  }

  ElMessage.info = (options) => {
    if (typeof options === 'string') {
      return origInfo({ message: options, duration: 1200, grouping: true, showClose: true })
    }
    return origInfo({ duration: 1200, grouping: true, showClose: true, ...options })
  }
}

const app = createApp(App)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
