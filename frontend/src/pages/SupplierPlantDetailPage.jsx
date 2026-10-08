import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { SupplierLayout } from '../components/SupplierLayout'
import { supplierApi } from '../services/api'
import { formatInr } from '../utils/orderHelpers'

const GRADES = ['M20', 'M25', 'M30', 'M35', 'M40']

const EMPTY_PRODUCT = {
  grade: 'M20',
  price_per_m3: '',
  available_quantity: '',
  minimum_order_m3: '1',
  is_available: true,
}

export function SupplierPlantDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [plant, setPlant] = useState(null)
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [productForm, setProductForm] = useState(EMPTY_PRODUCT)
  const [addingProduct, setAddingProduct] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [editId, setEditId] = useState(null)
  const [editForm, setEditForm] = useState(null)
  const [savingEdit, setSavingEdit] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [plantRes, productsRes] = await Promise.all([
        supplierApi.getPlant(id),
        supplierApi.listPlantProducts(id),
      ])
      setPlant(plantRes.plant)
      setProducts(productsRes.products || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    load()
  }, [load])

  const handleAddProduct = async (event) => {
    event.preventDefault()
    setAddingProduct(true)
    setError('')
    try {
      await supplierApi.createPlantProduct(id, {
        grade: productForm.grade,
        price_per_m3: parseFloat(productForm.price_per_m3),
        available_quantity: parseFloat(productForm.available_quantity),
        minimum_order_m3: parseFloat(productForm.minimum_order_m3),
        is_available: productForm.is_available,
      })
      setProductForm(EMPTY_PRODUCT)
      setShowAddForm(false)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setAddingProduct(false)
    }
  }

  const startEdit = (product) => {
    setEditId(product.id)
    setEditForm({
      price_per_m3: String(product.price_per_m3),
      available_quantity: String(product.available_quantity),
      minimum_order_m3: String(product.minimum_order_m3 ?? 1),
      is_available: product.is_available,
    })
  }

  const saveEdit = async () => {
    setSavingEdit(true)
    setError('')
    try {
      await supplierApi.updateProduct(editId, {
        price_per_m3: parseFloat(editForm.price_per_m3),
        available_quantity: parseFloat(editForm.available_quantity),
        minimum_order_m3: parseFloat(editForm.minimum_order_m3),
        is_available: editForm.is_available,
      })
      setEditId(null)
      setEditForm(null)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setSavingEdit(false)
    }
  }

  const deactivate = async (product) => {
    if (!window.confirm(`Deactivate grade ${product.grade} at this plant?`)) return
    setError('')
    try {
      await supplierApi.updateProduct(product.id, { is_available: false })
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const deleteProduct = async (product) => {
    if (!window.confirm(`Delete grade ${product.grade} and its price from this plant?`)) return
    setError('')
    try {
      await supplierApi.deleteProduct(product.id)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const deletePlant = async () => {
    if (
      !window.confirm(
        `Delete plant "${plant.plant_name}" and all grades/prices? This cannot be undone.`,
      )
    ) {
      return
    }
    setError('')
    try {
      await supplierApi.deletePlant(id)
      navigate('/supplier/plants')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <SupplierLayout
      title={plant?.plant_name || 'Plant details'}
      subtitle="Concrete products and pricing for this plant."
      actions={
        plant && (
          <div className="header-actions">
            <Link to={`/supplier/plants/${id}/edit`} className="btn btn-secondary">
              Edit plant
            </Link>
            <button type="button" className="btn btn-danger" onClick={deletePlant}>
              Delete plant
            </button>
          </div>
        )
      }
    >
      <p className="breadcrumb">
        <Link to="/supplier/plants" className="link">
          Plants & Pricing
        </Link>
        <span className="muted"> / Details</span>
      </p>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <p className="muted">Loading…</p>
      ) : !plant ? (
        <p className="muted">Plant not found.</p>
      ) : (
        <>
          <section className="card detail-card">
            <dl className="detail-list">
              <div>
                <dt>Location</dt>
                <dd>
                  {plant.address}
                  <span className="muted block-text">
                    {plant.city} · {plant.pincode}
                  </span>
                </dd>
              </div>
              {plant.contact_phone && (
                <div>
                  <dt>Contact</dt>
                  <dd>{plant.contact_phone}</dd>
                </div>
              )}
              {plant.operating_hours && (
                <div>
                  <dt>Operating hours</dt>
                  <dd>{plant.operating_hours}</dd>
                </div>
              )}
            </dl>
          </section>

          <section className="card">
            <div className="card-title-row">
              <h3>Concrete products & pricing</h3>
              <button type="button" className="btn btn-primary btn-sm" onClick={() => setShowAddForm((v) => !v)}>
                {showAddForm ? 'Cancel' : '+ Add grade'}
              </button>
            </div>

            {showAddForm && (
              <form className="form product-inline-form" onSubmit={handleAddProduct}>
                <div className="form-row product-form-grid">
                  <label className="field">
                    <span>Grade</span>
                    <input
                      type="text"
                      list="common-grades"
                      required
                      value={productForm.grade}
                      onChange={(e) => setProductForm({ ...productForm, grade: e.target.value })}
                      placeholder="e.g. M-20"
                    />
                    <datalist id="common-grades">
                      {GRADES.map((g) => (
                        <option key={g} value={g} />
                      ))}
                    </datalist>
                  </label>
                  <label className="field">
                    <span>Price / m³ (₹)</span>
                    <input
                      type="number"
                      min="1"
                      step="1"
                      required
                      value={productForm.price_per_m3}
                      onChange={(e) => setProductForm({ ...productForm, price_per_m3: e.target.value })}
                    />
                  </label>
                  <label className="field">
                    <span>Available qty (m³)</span>
                    <input
                      type="number"
                      min="0"
                      step="0.5"
                      required
                      value={productForm.available_quantity}
                      onChange={(e) => setProductForm({ ...productForm, available_quantity: e.target.value })}
                    />
                  </label>
                  <label className="field">
                    <span>Min order (m³)</span>
                    <input
                      type="number"
                      min="0.5"
                      step="0.5"
                      required
                      value={productForm.minimum_order_m3}
                      onChange={(e) => setProductForm({ ...productForm, minimum_order_m3: e.target.value })}
                    />
                  </label>
                </div>
                <button type="submit" className="btn btn-primary btn-sm" disabled={addingProduct}>
                  {addingProduct ? 'Adding…' : 'Save product'}
                </button>
              </form>
            )}

            {products.length === 0 ? (
              <p className="muted empty-state">No concrete grades configured for this plant.</p>
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Grade</th>
                      <th>Price / m³</th>
                      <th>Available</th>
                      <th>Min order</th>
                      <th>Status</th>
                      <th aria-label="Actions" />
                    </tr>
                  </thead>
                  <tbody>
                    {products.map((product) =>
                      editId === product.id ? (
                        <tr key={product.id}>
                          <td>{product.grade}</td>
                          <td>
                            <input
                              className="table-input"
                              type="number"
                              value={editForm.price_per_m3}
                              onChange={(e) => setEditForm({ ...editForm, price_per_m3: e.target.value })}
                            />
                          </td>
                          <td>
                            <input
                              className="table-input"
                              type="number"
                              value={editForm.available_quantity}
                              onChange={(e) => setEditForm({ ...editForm, available_quantity: e.target.value })}
                            />
                          </td>
                          <td>
                            <input
                              className="table-input"
                              type="number"
                              value={editForm.minimum_order_m3}
                              onChange={(e) => setEditForm({ ...editForm, minimum_order_m3: e.target.value })}
                            />
                          </td>
                          <td>
                            <label className="checkbox-inline">
                              <input
                                type="checkbox"
                                checked={editForm.is_available}
                                onChange={(e) => setEditForm({ ...editForm, is_available: e.target.checked })}
                              />
                              Active
                            </label>
                          </td>
                          <td className="table-actions">
                            <div className="table-actions-inner">
                              <button type="button" className="btn btn-primary btn-sm" disabled={savingEdit} onClick={saveEdit}>
                                Save
                              </button>
                              <button type="button" className="btn btn-secondary btn-sm" onClick={() => setEditId(null)}>
                                Cancel
                              </button>
                            </div>
                          </td>
                        </tr>
                      ) : (
                        <tr key={product.id}>
                          <td>{product.grade}</td>
                          <td>{formatInr(product.price_per_m3)}</td>
                          <td>{product.available_quantity} m³</td>
                          <td>{product.minimum_order_m3 ?? 1} m³</td>
                          <td>
                            <span className={product.is_available ? 'status-badge status-delivered' : 'status-badge status-cancelled'}>
                              {product.is_available ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td className="table-actions">
                            <div className="table-actions-inner">
                              <button type="button" className="btn btn-secondary btn-sm" onClick={() => startEdit(product)}>
                                Edit
                              </button>
                              {product.is_available && (
                                <button type="button" className="btn btn-secondary btn-sm" onClick={() => deactivate(product)}>
                                  Deactivate
                                </button>
                              )}
                              <button type="button" className="btn btn-danger btn-sm" onClick={() => deleteProduct(product)}>
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </SupplierLayout>
  )
}
