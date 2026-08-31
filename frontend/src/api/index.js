import axios from 'axios'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000
})

export const OpsApi = {
  // 仪表盘
  getDashboard: () => http.get('/dashboard/overview'),
  getClusterDistribution: () => http.get('/dashboard/cluster-distribution'),

  // 主机管理
  getHosts: (params) => http.get('/hosts', { params }),
  createHost: (data) => http.post('/hosts', data),
  updateHost: (id, data) => http.put(`/hosts/${id}`, data),
  deleteHost: (id) => http.delete(`/hosts/${id}`),
  batchDeleteHosts: (hostIds) => http.post('/hosts/batch-delete', { host_ids: hostIds }),

  // 集群与服务管理
  getClusters: (params) => http.get('/clusters', { params }),
  createCluster: (data) => http.post('/clusters', data),
  updateCluster: (id, data) => http.put(`/clusters/${id}`, data),
  deleteCluster: (id) => http.delete(`/clusters/${id}`),
  bindClusterHosts: (clusterId, nodes) => http.post(`/clusters/${clusterId}/bind-hosts`, { nodes }),

  // 导入与导出
  importAssets: (formData, overwrite = true) =>
    http.post(`/assets/import?overwrite=${overwrite}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  getExportUrl: (params = {}) => {
    const cleanParams = {}
    Object.keys(params).forEach(k => {
      if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
        cleanParams[k] = params[k]
      }
    })
    const query = new URLSearchParams(cleanParams).toString()
    return query ? `/api/assets/export?${query}` : '/api/assets/export'
  },
  downloadTemplateBlob: () => http.get('/assets/template', { responseType: 'blob' }),
  exportAssetsBlob: (params = {}) => {
    const cleanParams = {}
    Object.keys(params).forEach(k => {
      if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
        cleanParams[k] = params[k]
      }
    })
    return http.get('/assets/export', { params: cleanParams, responseType: 'blob' })
  },

  // 域名资产管理
  getDomains: (params) => http.get('/domains', { params }),
  createDomain: (data) => http.post('/domains', data),
  updateDomain: (id, data) => http.put(`/domains/${id}`, data),
  deleteDomain: (id) => http.delete(`/domains/${id}`),
  checkDomainDns: (id) => http.post(`/domains/${id}/check-dns`),
  checkAllDomainDns: () => http.post('/domains/check-all-dns'),

  // 元数据配置
  getConfig: () => http.get('/config/meta'),
  saveConfig: (data) => http.put('/config/meta', data),
  resetConfig: () => http.post('/config/meta/reset')
}

export default OpsApi
