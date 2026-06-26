import { useState } from 'react'

const SEVERITY_STYLES = {
  danger:  { badge: 'bg-red-100 text-red-700',    border: 'border-red-200',   icon: '🔴', label: 'DANGER'  },
  warning: { badge: 'bg-amber-100 text-amber-700', border: 'border-amber-200', icon: '⚠️', label: 'WARNING' },
}

function InfoRow({ icon, label, children }) {
  return (
    <div className="mb-4 last:mb-0">
      <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-widest mb-1">
        {icon} {label}
      </p>
      <div className="text-sm text-gray-700 leading-relaxed">{children}</div>
    </div>
  )
}

function ChevronIcon({ open }) {
  return (
    <svg
      className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
      fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
    </svg>
  )
}

export default function InjuryFeedbackCard({ feedback }) {
  const {
    phase,
    severity,
    summary,
    feedback: feedbackText,
    cue,
    source,
    violated_rules,
    frame_image_url,
    injury_prone_frame_count,
  } = feedback

  const style    = SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.warning
  const [open, setOpen] = useState(true)

  return (
    <div className={`bg-white rounded-2xl shadow-sm border ${style.border} overflow-hidden`}>

      {/* Header — always visible, click to collapse */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-6 py-4 border-b border-gray-100 text-left hover:bg-gray-50/60 transition-colors"
      >
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wider mb-0.5">Phase</p>
          <h3 className="text-lg font-bold text-gray-900 capitalize">
            {phase.replace(/_/g, ' ')}
          </h3>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex flex-col items-end gap-1">
            <span className={`inline-flex items-center gap-1 text-xs font-bold px-3 py-1 rounded-full ${style.badge}`}>
              {style.icon} {style.label}
            </span>
            <span className="text-[11px] text-gray-400">
              {injury_prone_frame_count} frame{injury_prone_frame_count > 1 ? 's' : ''} flagged
            </span>
          </div>
          <ChevronIcon open={open} />
        </div>
      </button>

      {/* Collapsible body */}
      {open && (
        <div className="flex flex-col md:flex-row">
          {/* Frame image */}
          <div className="md:w-64 flex-shrink-0 bg-gray-900 flex items-center justify-center min-h-48">
            {frame_image_url ? (
              <img
                src={frame_image_url}
                alt={`Injury-prone frame — ${phase}`}
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="text-gray-600 text-sm text-center px-4">
                <svg className="w-10 h-10 mx-auto mb-2 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M15 10l4.553-2.069A1 1 0 0121 8.82V15.18a1 1 0 01-1.447.89L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
                </svg>
                No frame image
              </div>
            )}
          </div>

          {/* Feedback text */}
          <div className="flex-1 p-6">
            <InfoRow icon="📋" label="Violation">
              <span className="font-mono text-xs bg-gray-50 border border-gray-200 rounded px-2 py-1 block break-all">
                {violated_rules}
              </span>
            </InfoRow>

            <InfoRow icon="💬" label="Analysis">
              {summary}
            </InfoRow>

            <InfoRow icon="🩺" label="Corrective Feedback">
              {feedbackText}
            </InfoRow>

            <InfoRow icon="🎯" label="Coaching Cue">
              <span className="italic text-green-700 font-medium">"{cue}"</span>
            </InfoRow>

            <InfoRow icon="📚" label="Source">
              <span className="text-xs text-gray-500">{source}</span>
            </InfoRow>
          </div>
        </div>
      )}
    </div>
  )
}
