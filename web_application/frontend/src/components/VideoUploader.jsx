import { useRef, useState } from 'react'

const ACCEPTED = '.mp4,.mov,.avi,.mkv,.webm'

const FEATURE_PILLS = [
  { label: 'AI-Powered Pose Estimation' },
  { label: '7 Exercise Classes' },
  { label: 'Real-time Analysis' },
  { label: 'RAG Coaching Feedback' },
]

const HOW_IT_WORKS = [
  {
    step: '01',
    title: 'Upload Video',
    description:
      'Drag & drop a gym workout video in any common format. Frames are extracted and processed locally on your server.',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round"
          d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
      </svg>
    ),
  },
  {
    step: '02',
    title: 'AI Analysis',
    description:
      'MediaPipe extracts 3D pose landmarks from 50 sampled frames. XGBoost OvR classifiers vote across frames to identify the exercise.',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round"
          d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
      </svg>
    ),
  },
  {
    step: '03',
    title: 'Coaching Feedback',
    description:
      'Phase-aware biomechanical thresholds flag injury risks. Claude AI generates personalised corrective cues grounded in peer-reviewed literature via RAG.',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round"
          d="M8.625 9.75a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375m-13.5 3.01c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.184-4.183a1.14 1.14 0 01.778-.332 48.294 48.294 0 005.83-.498c1.585-.233 2.708-1.626 2.708-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
      </svg>
    ),
  },
]

/* Classification (7) + the 5 that also get full injury analysis */
const EXERCISES = [
  { name: 'Pull Up',           injury: true  },
  { name: 'Squat',             injury: true  },
  { name: 'Leg Extension',     injury: true  },
  { name: 'T Bar Row',         injury: true  },
  { name: 'Deadlift',          injury: false },
  { name: 'Chest Fly Machine', injury: false },
  { name: 'Leg Raises',        injury: false },
]

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function VideoUploader({ onFile }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [pendingFile, setPendingFile] = useState(null)

  function handlePick(file) {
    if (!file) return
    setPendingFile(file)
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    handlePick(e.dataTransfer.files?.[0])
  }

  /* ── File confirm screen ── */
  if (pendingFile) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] fade-in">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8 text-center">
            <div className="w-16 h-16 rounded-2xl bg-green-50 border border-green-100 flex items-center justify-center mx-auto mb-5">
              <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M15 10l4.553-2.069A1 1 0 0121 8.82V15.18a1 1 0 01-1.447.89L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
              </svg>
            </div>

            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">Video ready</p>
            <h2 className="text-lg font-bold text-gray-900 truncate mb-1">{pendingFile.name}</h2>
            <p className="text-sm text-gray-400 mb-8">{formatSize(pendingFile.size)}</p>

            <button
              onClick={() => onFile(pendingFile)}
              className="w-full bg-green-500 hover:bg-green-600 active:scale-[0.98] text-white font-semibold py-3 rounded-xl transition-all duration-150 mb-3"
            >
              Analyse Video
            </button>
            <button
              onClick={() => setPendingFile(null)}
              className="text-sm text-gray-400 hover:text-gray-700 transition-colors"
            >
              Choose a different file
            </button>
          </div>
        </div>
      </div>
    )
  }

  /* ── Main landing screen ── */
  return (
    <div className="flex flex-col items-center fade-in">

      {/* Hero */}
      <div className="text-center mb-10 pt-4">
        <span className="inline-block text-xs font-semibold px-3 py-1 rounded-full bg-green-100 text-green-700 uppercase tracking-widest mb-4">
          MSc Research Project
        </span>
        <h1 className="text-5xl font-extrabold text-gray-900 tracking-tight mb-3">MotionGuard</h1>
        <p className="text-gray-500 text-lg max-w-lg mx-auto leading-relaxed">
          Upload a gym workout video and get AI-powered exercise classification with personalised injury risk feedback.
        </p>
        <div className="flex flex-wrap justify-center gap-2 mt-5">
          {FEATURE_PILLS.map((p) => (
            <span
              key={p.label}
              className="text-xs font-medium px-3 py-1 rounded-full bg-white border border-gray-200 text-gray-600 shadow-sm"
            >
              {p.label}
            </span>
          ))}
        </div>
      </div>

      {/* Drop zone */}
      <div
        onClick={() => inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`
          w-full max-w-xl border-2 border-dashed rounded-2xl p-16 flex flex-col items-center
          cursor-pointer transition-all duration-200 select-none
          ${dragging
            ? 'border-green-500 bg-green-50 scale-[1.02]'
            : 'border-gray-300 bg-gray-50 hover:border-green-400 hover:bg-green-50/60'}
        `}
      >
        <svg
          className={`w-16 h-16 mb-4 transition-colors ${dragging ? 'text-green-500' : 'text-gray-400'}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.2}
        >
          <path strokeLinecap="round" strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
        </svg>
        <p className="text-gray-700 font-semibold text-lg">
          {dragging ? 'Drop to analyse' : 'Drag & drop your exercise video'}
        </p>
        <p className="mt-1 text-gray-400 text-sm">or click to browse</p>
        <p className="mt-4 text-xs text-gray-400 tracking-wide">MP4 · MOV · AVI · MKV · WebM</p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        className="hidden"
        onChange={(e) => handlePick(e.target.files?.[0])}
      />

      {/* How it works */}
      <div id="how-it-works" className="w-full mt-20">
        <p className="text-center text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">How it works</p>
        <h2 className="text-center text-2xl font-bold text-gray-900 mb-10">Three steps to smarter training</h2>

        <div className="grid sm:grid-cols-3 gap-6">
          {HOW_IT_WORKS.map((item) => (
            <div key={item.step} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="w-11 h-11 rounded-xl bg-green-50 border border-green-100 flex items-center justify-center text-green-600">
                  {item.icon}
                </div>
                <span className="text-3xl font-extrabold text-gray-100 select-none">{item.step}</span>
              </div>
              <h3 className="font-bold text-gray-900">{item.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{item.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Supported exercises */}
      <div className="w-full mt-16 mb-4">
        <p className="text-center text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">Supported exercises</p>
        <h2 className="text-center text-2xl font-bold text-gray-900 mb-2">What can MotionGuard analyse?</h2>
        <p className="text-center text-sm text-gray-400 mb-8">
          All exercises support classification.{' '}
          <span className="inline-flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
            Highlighted
          </span>{' '}
          exercises also include full phase-aware injury analysis.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {EXERCISES.map((ex) => (
            <div
              key={ex.name}
              className={`rounded-xl border px-4 py-3 flex items-center justify-between gap-2 transition-colors ${
                ex.injury
                  ? 'bg-green-50 border-green-200'
                  : 'bg-white border-gray-200'
              }`}
            >
              <span className={`text-sm font-medium ${ex.injury ? 'text-green-900' : 'text-gray-700'}`}>
                {ex.name}
              </span>
              {ex.injury && (
                <span className="flex-shrink-0 w-2 h-2 rounded-full bg-green-500" title="Injury analysis supported" />
              )}
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}
