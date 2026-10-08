const API_BASE = '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = data.error || data.message || 'Request failed'
    throw new Error(message)
  }

  return data
}

export const supplierApi = {
  summary: () => request('/supplier/summary'),
  listOrders: (view = 'all') => request(`/supplier/orders?view=${encodeURIComponent(view)}`),
  getOrder: (id) => request(`/supplier/orders/${id}`),
  acceptOrder: (id) =>
    request(`/supplier/orders/${id}/accept`, {
      method: 'POST',
    }),
  rejectOrder: (id) =>
    request(`/supplier/orders/${id}/reject`, {
      method: 'POST',
    }),
  updateStatus: (id, status) =>
    request(`/supplier/orders/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),
  listPlants: () => request('/supplier/plants'),
  getPlant: (id) => request(`/supplier/plants/${id}`),
  createPlant: (payload) =>
    request('/supplier/plants', { method: 'POST', body: JSON.stringify(payload) }),
  updatePlant: (id, payload) =>
    request(`/supplier/plants/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deletePlant: (id) => request(`/supplier/plants/${id}`, { method: 'DELETE' }),
  listPlantProducts: (plantId) => request(`/supplier/plants/${plantId}/products`),
  createPlantProduct: (plantId, payload) =>
    request(`/supplier/plants/${plantId}/products`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateProduct: (productId, payload) =>
    request(`/supplier/products/${productId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
  deleteProduct: (productId) => request(`/supplier/products/${productId}`, { method: 'DELETE' }),
}

export const ordersApi = {
  catalog: () => request('/orders/catalog'),
  marketplace: () => request('/orders/marketplace'),
  estimate: (payload) =>
    request('/orders/estimate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  create: (payload) =>
    request('/orders', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  list: () => request('/orders'),
  get: (id) => request(`/orders/${id}`),
}

export const sitesApi = {
  list: () => request('/sites'),
  get: (id) => request(`/sites/${id}`),
  create: (payload) =>
    request('/sites', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  update: (id, payload) =>
    request(`/sites/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  remove: (id) =>
    request(`/sites/${id}`, {
      method: 'DELETE',
    }),
}

export const authApi = {
  me: () => request('/auth/me'),
  login: (email, password) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  register: (payload) =>
    request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  logout: () =>
    request('/auth/logout', {
      method: 'POST',
    }),
}
