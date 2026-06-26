import { useEffect, useState } from 'react'

const CIRCUMFERENCE = 2 * Math.PI * 40  // r = 40  →  ≈ 251.3

export default function ClassificationCard({ classification }) {
  const { exercise, confidence, valid_frames, total_frames, votes } = classification
  const pct    = Math.round(confidence * 100)
  const isHigh = pct >= 70

  /* Animate the arc and bars in after mount */
  const [drawn, setDrawn] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setDrawn(true), 120)
    return () => clearTimeout(t)
  }, [])

  const arcOffset = drawn
    ? CIRCUMFERENCE - (pct / 100) * CIRCUMFERENCE
    : CIRCUMFERENCE

  const sortedVotes = Object.entries(votes).sort((a, b) => b[1] - a[1])
  const maxVotes    = sortedVotes[0]?.[1] || 1

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-start justify-between mb-4 gap-4">
        <div>
          <p className="text-xs font-semibold text-green-600 uppercase tracking-widest mb-1">
            Detected Exercise
          </p>
          <h2 className="text-3xl font-bold text-gray-900 capitalize">{exercise}</h2>
        </div>

        {/* Animated SVG confidence ring */}
        <div className="relative w-24 h-24 flex-shrink-0">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            {/* Track */}
            <circle cx="50" cy="50" r="40" fill="none" stroke="#f3f4f6" strokeWidth="8" />
            {/* Arc */}
            <circle
              cx="50" cy="50" r="40"
              fill="none"
              stroke={isHigh ? '#22c55e' : '#f59e0b'}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={CIRCUMFERENCE}
              strokeDashoffset={arcOffset}
              style={{ transition: 'stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1)' }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-2xl font-bold leading-none ${isHigh ? 'text-green-600' : 'text-amber-600'}`}>
              {pct}%
            </span>
            <span className="text-[10px] text-gray-400 mt-0.5 font-medium tracking-wide">confidence</span>
          </div>
        </div>
      </div>

      <p className="text-sm text-gray-500 mb-5">
        {valid_frames} of {total_frames} frames had detectable pose landmarks
      </p>

      {/* Vote breakdown */}
      <div className="space-y-2.5">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Frame vote breakdown
        </p>
        {sortedVotes.map(([label, count]) => (
          <div key={label} className="flex items-center gap-3">
            <span className="w-36 text-sm text-gray-700 capitalize truncate">{label}</span>
            <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
              <div
                className={`h-2 rounded-full ${label === exercise ? 'bg-green-500' : 'bg-gray-300'}`}
                style={{
                  width: drawn ? `${(count / maxVotes) * 100}%` : '0%',
                  transition: 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
              />
            </div>
            <span className="w-6 text-right text-xs text-gray-500 tabular-nums">{count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
