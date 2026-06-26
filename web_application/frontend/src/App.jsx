import { useEffect, useState } from 'react'
import { useAnalysisPipeline } from './hooks/useAnalysisPipeline'
import VideoUploader from './components/VideoUploader'
import PipelineStatus from './components/PipelineStatus'
import ClassificationCard from './components/ClassificationCard'
import InjuryFeedbackCard from './components/InjuryFeedbackCard'
import Footer from './components/Footer'
import ScrollToTop from './components/ScrollToTop'

const PROCESSING_STATUSES = ['uploading', 'classifying', 'detecting']

function PrintIcon() {
  return (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096a42.415 42.415 0 0110.56 0m-10.56 0L6.75 19.5m10.56-5.671c.24.03.48.062.72.096m-.72-.096L17.25 19.5M6.75 19.5h10.5M4.5 7.5h15M4.5 7.5a2.25 2.25 0 00-2.25 2.25v6a2.25 2.25 0 002.25 2.25h15a2.25 2.25 0 002.25-2.25v-6A2.25 2.25 0 0019.5 7.5M4.5 7.5V6a2.25 2.25 0 012.25-2.25h10.5A2.25 2.25 0 0119.5 6v1.5" />
    </svg>
  )
}

function ResultsSummaryBanner({ classification, injuryResult }) {
  const pct = Math.round((classification?.confidence ?? 0) * 100)
  const supported = injuryResult?.supported
  const injuryCount = injuryResult?.injury_prone_frames ?? 0
  const severity = injuryResult?.overall_severity

  let colorClass = 'bg-gray-50 border-gray-200 text-gray-700'
  if (supported && injuryCount === 0) {
    colorClass = 'bg-green-50 border-green-200 text-green-800'
  } else if (supported && severity === 'warning') {
    colorClass = 'bg-amber-50 border-amber-200 text-amber-800'
  } else if (supported && severity === 'danger') {
    colorClass = 'bg-red-50 border-red-200 text-red-800'
  }

  const riskLabel = !supported
    ? 'Not supported'
    : injuryCount === 0
    ? 'None detected ✓'
    : `${injuryCount} frame${injuryCount > 1 ? 's' : ''} flagged`

  return (
    <div className={`rounded-2xl border px-6 py-4 flex flex-wrap items-center gap-x-6 gap-y-3 fade-in ${colorClass}`}>
      <Stat label="Exercise" value={<span className="capitalize">{classification?.exercise}</span>} />
      <Divider />
      <Stat label="Confidence" value={`${pct}%`} />
      <Divider />
      <Stat label="Risk Flags" value={riskLabel} />

      <button
        onClick={() => window.print()}
        className="no-print ml-auto inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border border-current opacity-60 hover:opacity-100 transition-opacity"
      >
        <PrintIcon /> Export Report
      </button>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] font-semibold uppercase tracking-widest opacity-50">{label}</span>
      <span className="font-bold text-sm">{value}</span>
    </div>
  )
}

function Divider() {
  return <div className="w-px h-4 bg-current opacity-20 hidden sm:block" />
}

export default function App() {
  const { status, uploadProgress, classification, injuryResult, error, run, reset } =
    useAnalysisPipeline()

  const [visible, setVisible] = useState(true)

  useEffect(() => {
    setVisible(false)
    const t = setTimeout(() => setVisible(true), 60)
    return () => clearTimeout(t)
  }, [status])

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-green-50/70 via-white to-white">

      {/* ── Sticky nav ── */}
      <nav className="no-print bg-white/80 backdrop-blur-sm border-b border-gray-200 px-6 py-3.5 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-green-500 flex items-center justify-center shadow-sm">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <span className="font-bold text-gray-900 text-lg tracking-tight">MotionGuard</span>
          <span className="ml-0.5 text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-green-100 text-green-700 uppercase tracking-wide select-none">
            v1.0 · Research
          </span>
        </div>

        <div className="flex items-center gap-5">
          {status === 'idle' && (
            <a
              href="#how-it-works"
              className="hidden sm:inline text-sm text-gray-500 hover:text-gray-800 font-medium transition-colors"
            >
              How it works
            </a>
          )}
          {status !== 'idle' && (
            <button
              onClick={reset}
              className="text-sm text-gray-500 hover:text-gray-800 flex items-center gap-1.5 font-medium transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Analyse another
            </button>
          )}
        </div>
      </nav>

      {/* ── Main content ── */}
      <main
        className="flex-1 max-w-4xl w-full mx-auto px-6 py-10"
        style={{ opacity: visible ? 1 : 0, transition: 'opacity 0.25s ease' }}
      >

        {/* Idle: uploader */}
        {status === 'idle' && <VideoUploader onFile={run} />}

        {/* Processing: stepper */}
        {PROCESSING_STATUSES.includes(status) && (
          <PipelineStatus
            status={status}
            uploadProgress={uploadProgress}
            classification={classification}
            injuryResult={injuryResult}
          />
        )}

        {/* Error */}
        {status === 'error' && (
          <div className="fade-in flex flex-col items-center justify-center min-h-[50vh] text-center">
            <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h3>
            <p className="text-gray-500 max-w-md mb-6">{error}</p>
            <button
              onClick={reset}
              className="bg-green-500 hover:bg-green-600 text-white font-semibold px-6 py-2.5 rounded-xl transition-colors"
            >
              Try again
            </button>
          </div>
        )}

        {/* Done: results */}
        {status === 'done' && classification && (
          <div className="space-y-6 fade-in">

            <ResultsSummaryBanner classification={classification} injuryResult={injuryResult} />

            <div className="print-card">
              <ClassificationCard classification={classification} />
            </div>

            {injuryResult && (
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-4">Injury Risk Analysis</h2>

                {!injuryResult.supported && (
                  <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6 text-blue-700">
                    <p className="font-semibold mb-1">Injury detection not available</p>
                    <p className="text-sm">
                      Phase-aware injury analysis currently supports: pull up, squat,
                      leg extension, shoulder press, t bar row.
                    </p>
                  </div>
                )}

                {injuryResult.supported && injuryResult.injury_prone_frames === 0 && (
                  <div className="bg-green-50 border border-green-200 rounded-2xl p-8 text-center">
                    <div className="text-5xl mb-3">✅</div>
                    <p className="text-xl font-bold text-green-700 mb-1">Great form!</p>
                    <p className="text-green-600 text-sm">
                      No injury-prone phases detected across {injuryResult.steady_phase_frames} steady-phase frames.
                    </p>
                  </div>
                )}

                {injuryResult.supported && injuryResult.feedback?.length > 0 && (
                  <div className="space-y-6">
                    <div className={`rounded-xl px-5 py-3 flex items-center gap-3 ${
                      injuryResult.overall_severity === 'danger'
                        ? 'bg-red-50 border border-red-200'
                        : 'bg-amber-50 border border-amber-200'
                    }`}>
                      <span className="text-lg">
                        {injuryResult.overall_severity === 'danger' ? '🔴' : '⚠️'}
                      </span>
                      <p className="text-sm font-medium text-gray-700">
                        <span className="font-bold capitalize">{injuryResult.overall_severity}</span>
                        {' '}— {injuryResult.injury_prone_frames} injury-prone frame
                        {injuryResult.injury_prone_frames > 1 ? 's' : ''} detected across{' '}
                        {injuryResult.feedback.length} phase
                        {injuryResult.feedback.length > 1 ? 's' : ''}
                      </p>
                    </div>

                    {injuryResult.feedback.map((fb, i) => (
                      <div key={i} className="print-card">
                        <InjuryFeedbackCard feedback={fb} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>

      <Footer />
      <ScrollToTop />
    </div>
  )
}
