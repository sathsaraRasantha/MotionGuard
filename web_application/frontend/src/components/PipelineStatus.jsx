const STEPS = [
  {
    key: 'uploading',
    label: 'Upload Video',
    activeLabel: 'Uploading video…',
    hint: 'Sending your file to the analysis server',
  },
  {
    key: 'classifying',
    label: 'Classify Exercise',
    activeLabel: 'Analysing movement…',
    hint: 'Extracting pose landmarks across 50 frames — usually 10–20 s',
  },
  {
    key: 'detecting',
    label: 'Detect Injury Risk',
    activeLabel: 'Checking key phases…',
    hint: 'Running phase-aware biomechanical checks + RAG feedback — may take 30–60 s',
  },
]

const ORDER = ['uploading', 'classifying', 'detecting', 'done']

function stepState(stepKey, currentStatus) {
  const stepIdx    = ORDER.indexOf(stepKey)
  const currentIdx = ORDER.indexOf(currentStatus === 'done' ? 'done' : currentStatus)
  if (currentIdx > stepIdx)  return 'done'
  if (currentIdx === stepIdx) return 'active'
  return 'pending'
}

function Spinner() {
  return (
    <svg className="animate-spin h-5 w-5 text-green-600" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg className="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd"
        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
        clipRule="evenodd" />
    </svg>
  )
}

function StepIcon({ state }) {
  if (state === 'done') {
    return (
      <div className="w-9 h-9 rounded-full bg-green-500 flex items-center justify-center">
        <CheckIcon />
      </div>
    )
  }
  if (state === 'active') {
    return (
      <div className="w-9 h-9 rounded-full bg-white border-2 border-green-500 flex items-center justify-center pulse-ring">
        <Spinner />
      </div>
    )
  }
  return (
    <div className="w-9 h-9 rounded-full bg-gray-100 border-2 border-gray-200 flex items-center justify-center">
      <div className="w-3 h-3 rounded-full bg-gray-300" />
    </div>
  )
}

function doneLabel(stepKey, classification, injuryResult) {
  if (stepKey === 'uploading')   return 'Video uploaded successfully'
  if (stepKey === 'classifying') return classification
    ? `Detected: ${classification.exercise} (${Math.round(classification.confidence * 100)}% confidence)`
    : 'Classified'
  if (stepKey === 'detecting') {
    if (!injuryResult) return 'Analysis complete'
    if (!injuryResult.supported) return 'Injury detection not supported for this exercise'
    const n = injuryResult.injury_prone_frames
    return n === 0 ? 'No injury-prone phases detected ✓' : `Found ${n} injury-prone frame${n > 1 ? 's' : ''}`
  }
  return ''
}

export default function PipelineStatus({ status, uploadProgress, classification, injuryResult }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] fade-in">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Analysing your video…</h2>
      <p className="text-sm text-gray-400 mb-10">Please keep this tab open while processing completes</p>

      <div className="w-full max-w-md space-y-0">
        {STEPS.map((step, idx) => {
          const state  = stepState(step.key, status)
          const isLast = idx === STEPS.length - 1

          return (
            <div key={step.key} className="flex items-start gap-4">
              {/* Icon + connector */}
              <div className="flex flex-col items-center">
                <StepIcon state={state} />
                {!isLast && (
                  <div className={`w-0.5 h-10 mt-1 transition-colors duration-500 ${state === 'done' ? 'bg-green-400' : 'bg-gray-200'}`} />
                )}
              </div>

              {/* Text */}
              <div className="pt-1.5 pb-8">
                <p className={`font-semibold text-sm ${state === 'pending' ? 'text-gray-400' : 'text-gray-800'}`}>
                  {state === 'active' ? step.activeLabel : step.label}
                </p>

                {/* Upload progress bar */}
                {state === 'active' && step.key === 'uploading' && uploadProgress < 100 && (
                  <div className="mt-2 w-48 bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-green-500 h-1.5 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                )}

                {/* Time hint for non-upload active steps */}
                {state === 'active' && step.key !== 'uploading' && (
                  <p className="text-xs text-gray-400 italic mt-1">{step.hint}</p>
                )}

                {/* Done label */}
                {state === 'done' && (
                  <p className="text-xs text-green-600 mt-0.5 font-medium">
                    {doneLabel(step.key, classification, injuryResult)}
                  </p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
