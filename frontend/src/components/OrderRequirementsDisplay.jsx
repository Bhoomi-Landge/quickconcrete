import {
  formatWorkability,
  labelFor,
} from '../utils/orderRequirementLabels'

function hasAnyRequirement(order) {
  return (
    order.pump_required != null ||
    order.placement_method ||
    order.workability_test_type ||
    order.special_concrete_type
  )
}

export function OrderRequirementsDisplay({ order }) {
  if (!order || !hasAnyRequirement(order)) {
    return (
      <div className="detail-subsection">
        <h3 className="detail-subheading">Concrete requirements</h3>
        <p className="muted">No structured requirements recorded for this order.</p>
      </div>
    )
  }

  const workability = formatWorkability(order)

  return (
    <div className="detail-subsection">
      <h3 className="detail-subheading">Concrete requirements</h3>
      <dl className="detail-list">
        <div>
          <dt>Pump requirement</dt>
          <dd>{labelFor('pump_required', order.pump_required)}</dd>
        </div>
        {order.pump_required && (
          <>
            {order.pump_type && (
              <div>
                <dt>Pump type</dt>
                <dd>{labelFor('pump_type', order.pump_type)}</dd>
              </div>
            )}
            {order.pump_boom_reach_m != null && (
              <div>
                <dt>Boom reach</dt>
                <dd>{order.pump_boom_reach_m} m</dd>
              </div>
            )}
            {order.pump_pipeline_length_m != null && (
              <div>
                <dt>Pipeline length</dt>
                <dd>{order.pump_pipeline_length_m} m</dd>
              </div>
            )}
            {order.pump_instructions && (
              <div>
                <dt>Pump instructions</dt>
                <dd>{order.pump_instructions}</dd>
              </div>
            )}
          </>
        )}
        <div>
          <dt>Placing method</dt>
          <dd>
            {labelFor('placement_method', order.placement_method)}
            {order.placement_method === 'OTHER' && order.placement_method_other && (
              <span className="muted block-text">{order.placement_method_other}</span>
            )}
          </dd>
        </div>
        {workability && (
          <div>
            <dt>Workability</dt>
            <dd>{workability}</dd>
          </div>
        )}
        <div>
          <dt>Special concrete</dt>
          <dd>
            {labelFor('special_concrete_type', order.special_concrete_type)}
            {order.special_concrete_notes && (
              <span className="muted block-text">{order.special_concrete_notes}</span>
            )}
            {order.requested_concrete_temp_c != null && (
              <span className="muted block-text">
                Requested temperature: {order.requested_concrete_temp_c} °C
              </span>
            )}
          </dd>
        </div>
      </dl>
    </div>
  )
}
