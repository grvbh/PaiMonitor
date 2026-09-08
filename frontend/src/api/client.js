import axios from 'axios'

const client = axios.create({ baseURL: '/api' })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export async function login(email, password) {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  const res = await client.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  localStorage.setItem('token', res.data.access_token)
  localStorage.setItem('role', res.data.role)
  return res.data
}

export function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
}

export function getRole() {
  return localStorage.getItem('role')
}

export function isAuthed() {
  return !!localStorage.getItem('token')
}

export const listDevices = () => client.get('/devices/').then((r) => r.data)
export const getDevice = (id) => client.get(`/devices/${id}`).then((r) => r.data)
export const createDevice = (payload) => client.post('/devices/', payload).then((r) => r.data)

export const listImages = (deviceId, params = {}) =>
  client.get(`/images/device/${deviceId}`, { params }).then((r) => r.data)

export const getDensity = (deviceId, granularity = 'day') =>
  client.get(`/analytics/density/${deviceId}`, { params: { granularity } }).then((r) => r.data)

export const getSummary = (deviceId) =>
  client.get(`/analytics/summary/${deviceId}`).then((r) => r.data)

export default client
