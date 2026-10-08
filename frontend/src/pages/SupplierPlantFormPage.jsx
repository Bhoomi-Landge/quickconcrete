import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { PlantForm, emptyPlantForm, plantToForm } from '../components/PlantForm'
import { SupplierLayout } from '../components/SupplierLayout'
import { supplierApi } from '../services/api'

export function SupplierPlantFormPage({ mode }) {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = mode === 'edit'

  const [form, setForm] = useState(emptyPlantForm())
  const [loading, setLoading] = useState(isEdit)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isEdit) return undefined
    let cancelled = false
    supplierApi
      .getPlant(id)
      .then((data) => {
        if (!cancelled) setForm(plantToForm(data.plant))
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [id, isEdit])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      if (isEdit) {
        await supplierApi.updatePlant(id, form)
        navigate(`/supplier/plants/${id}`)
      } else {
        const data = await supplierApi.createPlant(form)
        navigate(`/supplier/plants/${data.plant.id}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <SupplierLayout
      title={isEdit ? 'Edit plant' : 'Add plant'}
      subtitle="Plant location and contact details for dispatch."
    >
      <p className="breadcrumb">
        <Link to="/supplier/plants" className="link">
          Plants & Pricing
        </Link>
        <span className="muted"> / {isEdit ? 'Edit' : 'New'}</span>
      </p>
      {loading ? (
        <p className="muted">Loading plant…</p>
      ) : (
        <PlantForm
          form={form}
          onChange={setForm}
          onSubmit={handleSubmit}
          submitting={submitting}
          error={error}
          submitLabel={isEdit ? 'Save changes' : 'Add plant'}
        />
      )}
    </SupplierLayout>
  )
}
