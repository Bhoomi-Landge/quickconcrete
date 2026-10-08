import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ContractorLayout } from '../components/ContractorLayout'
import { SiteForm, emptySiteForm, siteToForm } from '../components/SiteForm'
import { sitesApi } from '../services/api'

export function ContractorSiteFormPage({ mode }) {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = mode === 'edit'

  const [form, setForm] = useState(emptySiteForm())
  const [loading, setLoading] = useState(isEdit)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isEdit) return undefined
    let cancelled = false
    sitesApi
      .get(id)
      .then((data) => {
        if (!cancelled) setForm(siteToForm(data.site))
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
        await sitesApi.update(id, form)
        navigate(`/contractor/sites/${id}`)
      } else {
        const data = await sitesApi.create(form)
        navigate(`/contractor/sites/${data.site.id}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <ContractorLayout
      title={isEdit ? 'Edit site' : 'Add construction site'}
      subtitle={isEdit ? 'Update delivery location details.' : 'Save a site for future concrete deliveries.'}
    >
      <p className="breadcrumb">
        <Link to="/contractor/sites" className="link">
          Sites
        </Link>
        <span className="muted"> / {isEdit ? 'Edit' : 'New'}</span>
      </p>

      {loading ? (
        <p className="muted">Loading site…</p>
      ) : (
        <SiteForm
          form={form}
          onChange={setForm}
          onSubmit={handleSubmit}
          submitting={submitting}
          error={error}
          submitLabel={isEdit ? 'Save changes' : 'Add site'}
        />
      )}
    </ContractorLayout>
  )
}
