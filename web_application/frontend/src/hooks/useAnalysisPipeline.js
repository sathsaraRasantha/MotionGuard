import { useState, useCallback } from 'react'
import { uploadVideo, classifyVideo, detectInjuries } from '../services/api'

/**
 * Orchestrates the three-step pipeline:
 *   idle → uploading → classifying → detecting → done  (or error)
 *
 * Exposes:
 *   status           — current pipeline stage
 *   uploadProgress   — 0-100 while uploading
 *   classification   — result from /api/classify
 *   injuryResult     — result from /api/injury-detection
 *   error            — error message string if any step fails
 *   run(file)        — starts the pipeline with the given File object
 *   reset()          — returns to idle
 */
export function useAnalysisPipeline() {
  const [status, setStatus] = useState('idle')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [classification, setClassification] = useState(null)
  const [injuryResult, setInjuryResult] = useState(null)
  const [error, setError] = useState(null)

  const reset = useCallback(() => {
    setStatus('idle')
    setUploadProgress(0)
    setClassification(null)
    setInjuryResult(null)
    setError(null)
  }, [])

  const run = useCallback(async (file) => {
    reset()

    try {
      // Step 1 — upload
      setStatus('uploading')
      setUploadProgress(0)
      const { video_path } = await uploadVideo(file, setUploadProgress)
      setUploadProgress(100)

      // Step 2 — classify
      setStatus('classifying')
      const classData = await classifyVideo(video_path)
      setClassification(classData)

      // Step 3 — detect injuries using classified exercise
      setStatus('detecting')
      const injuryData = await detectInjuries(video_path, classData.exercise)
      setInjuryResult(injuryData)

      setStatus('done')
    } catch (err) {
      const message =
        err?.response?.data?.detail || err?.message || 'An unexpected error occurred.'
      setError(message)
      setStatus('error')
    }
  }, [reset])

  return { status, uploadProgress, classification, injuryResult, error, run, reset }
}
