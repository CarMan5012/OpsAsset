/**
 * OpsAsset 前端工具函数库 (1:1 完整无损迁移)
 */

export function formatDateTime(str) {
  if (!str) return ''
  return String(str).replace('T', ' ').slice(0, 19)
}

export function formatStorageValue(gb) {
  if (gb === undefined || gb === null || gb === '' || isNaN(gb) || Number(gb) <= 0) return ''
  const num = Number(gb)
  if (num >= 1024) {
    const tb = num / 1024
    return tb % 1 === 0 ? tb.toFixed(0) : tb.toFixed(1)
  }
  return num
}

export function formatStorageUnit(gb) {
  if (gb === undefined || gb === null || gb === '' || isNaN(gb) || Number(gb) <= 0) return ''
  return Number(gb) >= 1024 ? 'TB' : 'GB'
}

export function formatStorageFull(gb) {
  if (gb === undefined || gb === null || gb === '' || isNaN(gb) || Number(gb) <= 0) return ''
  const val = formatStorageValue(gb)
  const unit = formatStorageUnit(gb)
  if (!val || Number(val) <= 0) return ''
  return `${val} ${unit}`
}



export function getCleanKernel(kernel) {
  if (!kernel) return ''
  const str = String(kernel).trim()
  if (!str || str === '-') return ''
  const match = str.match(/^(\d+(\.\d+)+)/)
  if (match && match[1]) {
    return match[1]
  }
  return str.replace(/(\.el\d+.*?|\.x86_64|\.aarch64)/, '').split('-')[0]
}

export function getShortKernel(kernel) {
  return getCleanKernel(kernel)
}

export function isIpv6(ip) {
  return ip && ip.includes(':')
}

export function parsePublicIps(raw) {
  if (!raw) return []
  return String(raw)
    .split(/[,，\s\n]+/)
    .map(s => s.trim())
    .filter(Boolean)
}

export function parsePorts(portStr) {
  if (!portStr) return []
  return String(portStr)
    .split(/[,，\s\n]+/)
    .map(p => p.trim())
    .filter(Boolean)
}

export function isPortRange(port) {
  if (!port) return false
  return String(port).includes('-')
}

export function getDefaultPortForType(type, metaConfig) {
  if (!type || !metaConfig || !metaConfig.cluster_types) return ''
  const item = metaConfig.cluster_types.find(c => c.key === type)
  return item && item.default_port ? item.default_port : ''
}

import { MIDDLEWARE_LOGOS } from './logos'

export function getMiddlewareLogo(type, size = 18) {
  if (!type) return ''
  const t = String(type).toLowerCase().trim()
  
  let key = t
  if (t === 'kubernetes') key = 'k8s'
  else if (t === 'elasticsearch') key = 'es'
  else if (t === 'mongo') key = 'mongodb'
  else if (t === 'pg') key = 'postgresql'

  const rawSvg = MIDDLEWARE_LOGOS[key] || MIDDLEWARE_LOGOS[t] || MIDDLEWARE_LOGOS['default']
  if (rawSvg) {
    return rawSvg.replace(/<svg\b([^>]*)>/, `<svg width="${size}" height="${size}" style="display: inline-block; vertical-align: middle;" $1>`)
  }
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>`
}

export function getStatusStyle(key, metaConfig) {
  if (!key) return { color: '#64748b', dotColor: '#94a3b8', backgroundColor: '#f8fafc', borderColor: '#cbd5e1' }
  const k = String(key).toLowerCase().trim()
  const list = metaConfig?.host_statuses || metaConfig?.statuses || []
  const item = list.find(s => String(s.key).toLowerCase() === k || s.label === key)

  let hex = ''
  if (item?.color) {
    hex = item.color
  } else if (item?.type) {
    const typeColorMap = {
      success: '#10b981',
      danger: '#ef4444',
      warning: '#f59e0b',
      info: '#64748b',
      primary: '#3b82f6'
    }
    hex = typeColorMap[item.type] || '#64748b'
  } else {
    const fallback = {
      'online': '#10b981',
      'running': '#10b981',
      'offline': '#ef4444',
      'stopped': '#64748b',
      'maintenance': '#f59e0b',
      'warning': '#f59e0b',
      'error': '#ef4444'
    }
    hex = fallback[k] || '#64748b'
  }

  return {
    color: hex,
    dotColor: hex,
    backgroundColor: hex.startsWith('#') && hex.length === 7 ? `${hex}18` : 'rgba(100, 116, 139, 0.1)',
    borderColor: hex.startsWith('#') && hex.length === 7 ? `${hex}45` : 'rgba(100, 116, 139, 0.25)'
  }
}

export function getEnvLabel(key, metaConfig) {
  if (!key) return '-'
  const k = String(key).toLowerCase().trim()
  const list = metaConfig?.environments || []
  const item = list.find(e => String(e.key).toLowerCase().trim() === k || String(e.label).toLowerCase().trim() === k)
  if (item && item.label) return item.label
  if (k === 'prod') return '生产环境'
  if (k === 'test') return '测试环境'
  return key
}

export function getStatusLabel(key, metaConfig) {
  if (!key) return '-'
  const k = String(key).toLowerCase().trim()
  const list = metaConfig?.host_statuses || metaConfig?.statuses || []
  const item = list.find(s => String(s.key).toLowerCase().trim() === k || String(s.label).toLowerCase().trim() === k)
  if (item && item.label) return item.label

  const fallbackMap = {
    'online': '在线',
    'running': '在线',
    'offline': '下线',
    'stopped': '下线',
    'maintenance': '维护中',
    'warning': '告警',
    'error': '故障'
  }
  return fallbackMap[k] || key
}

export function getArchLabel(key, metaConfig) {
  if (!key) return '-'
  const k = String(key).toLowerCase().trim()
  const list = metaConfig?.cpu_architectures || metaConfig?.architectures || []
  const item = list.find(a => String(a.key).toLowerCase().trim() === k || String(a.label).toLowerCase().trim() === k)
  return item && item.label ? item.label : key
}

export function getClusterTypeLabel(key, metaConfig) {
  if (!key) return '-'
  const k = String(key).toLowerCase().trim()
  const list = metaConfig?.cluster_types || []
  const item = list.find(c => String(c.key).toLowerCase().trim() === k || String(c.label).toLowerCase().trim() === k)
  return item && item.label ? item.label : key
}

export function getRoleLabel(roleKey, clusterType, metaConfig) {
  if (!roleKey) return ''
  const rk = String(roleKey).toLowerCase().trim()
  if (clusterType && metaConfig?.cluster_roles?.[clusterType]) {
    const rList = metaConfig.cluster_roles[clusterType]
    const rItem = rList.find(r => String(r.key).toLowerCase().trim() === rk || String(r.label).toLowerCase().trim() === rk)
    if (rItem && rItem.label) return rItem.label
  }
  return roleKey
}

export function normalizeMetaConfig(data = {}) {
  const environments = data.environments || []
  const rawStatuses = data.statuses || data.host_statuses || []
  const host_statuses = rawStatuses.map(s => {
    const fallbackColor = s.key === 'online' || s.key === 'running' ? '#10b981' : (s.key === 'offline' || s.key === 'stopped' || s.key === 'error' ? '#ef4444' : (s.key === 'maintenance' || s.key === 'warning' ? '#f59e0b' : '#64748b'))
    return {
      ...s,
      color: s.color || fallbackColor,
      type: s.type || 'info'
    }
  })
  const cpu_architectures = data.architectures || data.cpu_architectures || []
  const common_os_list = data.os_suggestions || data.common_os_list || []
  const cluster_roles = data.cluster_roles || {}
  const default_ports = data.default_middleware_ports || {}

  const cluster_types = (data.cluster_types || []).map(ct => {
    const key = ct.key
    const rawRoles = ct.roles || cluster_roles[key] || []
    const roles = (Array.isArray(rawRoles) ? rawRoles : []).map(r => {
      if (typeof r === 'string') return { key: r, label: r }
      return { key: r.key, label: r.key || r.label }
    })
    const default_port = ct.default_port || default_ports[key] || ''
    return {
      ...ct,
      roles: roles,
      default_port: default_port
    }
  })

  return {
    environments,
    statuses: host_statuses,
    host_statuses,
    architectures: cpu_architectures,
    cpu_architectures,
    os_suggestions: common_os_list,
    common_os_list,
    cluster_roles,
    default_middleware_ports: default_ports,
    cluster_types
  }
}

export function serializeMetaConfigForBackend(meta) {
  const cluster_roles = {}
  const default_ports = {}
  ;(meta.cluster_types || []).forEach(ct => {
    if (ct.key && ct.roles) {
      cluster_roles[ct.key] = ct.roles
    }
    if (ct.key && ct.default_port) {
      default_ports[ct.key] = ct.default_port
    }
  })

  const statuses = (meta.host_statuses || meta.statuses || []).map(s => ({
    key: s.key,
    label: s.label,
    type: s.type || 'info',
    color: s.color || '#10b981'
  }))

  return {
    environments: meta.environments || [],
    statuses: statuses,
    architectures: meta.cpu_architectures || meta.architectures || [],
    cluster_types: (meta.cluster_types || []).map(ct => ({
      key: ct.key,
      label: ct.label,
      default_port: ct.default_port || ''
    })),
    cluster_roles: cluster_roles,
    default_middleware_ports: default_ports,
    os_suggestions: meta.common_os_list || meta.os_suggestions || []
  }
}

// 主机资产全量可选导出列定义
export const HOST_EXPORT_COLUMNS = [
  { key: 'index', label: '序号', default: true, minWidth: 70 },
  { key: 'hostname', label: '主机名', default: true, minWidth: 150 },
  { key: 'private_ip', label: '内网IP', default: true, minWidth: 140 },
  { key: 'public_ip', label: '外网IP', default: true, minWidth: 150 },
  { key: 'open_ports', label: '开放端口', default: true, minWidth: 160 },
  { key: 'env', label: '环境', default: true, minWidth: 90 },
  { key: 'status', label: '状态', default: true, minWidth: 90 },
  { key: 'cpu_cores', label: 'CPU', default: true, minWidth: 80 },
  { key: 'memory_gb', label: '内存', default: true, minWidth: 90 },
  { key: 'disk_gb', label: '数据盘', default: true, minWidth: 90 },
  { key: 'arch', label: '架构', default: true, minWidth: 90 },
  { key: 'os', label: '操作系统', default: true, minWidth: 130 },
  { key: 'kernel_version', label: '内核版本', default: false, minWidth: 110 },
  { key: 'clusters', label: '所属服务', default: true, minWidth: 180 },
  { key: 'notes', label: '备注', default: true, minWidth: 120 },
  { key: 'created_at', label: '添加时间', default: false, minWidth: 140 },
  { key: 'updated_at', label: '修改时间', default: false, minWidth: 140 }
]

/**
 * 汇总主机自身开放端口与部署服务的端口集合
 */
export function getAllHostPorts(row) {
  if (!row) return []
  const portsSet = new Set()
  if (row.open_ports) {
    parsePorts(row.open_ports).forEach(p => portsSet.add(p))
  }
  if (Array.isArray(row.clusters)) {
    row.clusters.forEach(c => {
      if (c.port) {
        parsePorts(c.port).forEach(p => portsSet.add(p))
      }
    })
  }
  return Array.from(portsSet)
}

/**
 * 将主机原始数据转换为与主机资产列表完全一致的显示数据对象 (用于实时表格预览与导出一致性，空数据保持纯空白)
 */
export function formatHostExportRow(row, metaConfig, index) {
  if (!row) return {}
  
  // 1. 端口汇总
  const allPorts = getAllHostPorts(row)
  const portsDisplay = allPorts.length > 0 ? allPorts.join(', ') : (row.open_ports || '')

  // 2. 服务汇总 (与主机资产列表徽章完全一致: 如 K8s v1.19.11, Redis v7.0.12)
  const clustersList = []
  if (Array.isArray(row.clusters) && row.clusters.length > 0) {
    row.clusters.forEach(c => {
      const typeOrName = c.cluster_type || c.cluster_name || '服务'
      const rawV = c.cluster_version || c.version || ''
      const ver = rawV ? (String(rawV).startsWith('v') || String(rawV).startsWith('V') ? String(rawV) : `v${rawV}`) : ''
      clustersList.push(ver ? `${typeOrName} ${ver}` : typeOrName)
    })
  }
  const clustersDisplay = clustersList.length > 0 ? clustersList.join(', ') : ''

  const cpuStr = (row.cpu_cores !== undefined && row.cpu_cores !== null && row.cpu_cores !== '' && Number(row.cpu_cores) > 0) ? `${row.cpu_cores} 核` : ''
  const memStr = (row.memory_gb !== undefined && row.memory_gb !== null && row.memory_gb !== '' && Number(row.memory_gb) > 0) ? formatStorageFull(row.memory_gb) : ''
  const diskStr = (row.disk_gb !== undefined && row.disk_gb !== null && row.disk_gb !== '' && Number(row.disk_gb) > 0) ? formatStorageFull(row.disk_gb) : ''


  return {
    id: row.id,
    index: typeof index === 'number' ? index + 1 : (row.index !== undefined ? row.index : ''),
    hostname: row.hostname || '',
    private_ip: row.private_ip || '',
    public_ip: row.public_ip || '',
    open_ports: portsDisplay,
    env: row.env ? getEnvLabel(row.env, metaConfig) : '',
    status: row.status ? getStatusLabel(row.status, metaConfig) : '',
    cpu_cores: cpuStr,
    memory_gb: memStr,
    disk_gb: diskStr,
    arch: row.arch ? getArchLabel(row.arch, metaConfig) : '',
    os: row.os || '',
    kernel_version: row.kernel_version ? getCleanKernel(row.kernel_version) : '',
    clusters: clustersDisplay,
    notes: row.notes || '',
    created_at: formatDateTime(row.created_at) || '',
    updated_at: formatDateTime(row.updated_at || row.created_at) || ''
  }
}

