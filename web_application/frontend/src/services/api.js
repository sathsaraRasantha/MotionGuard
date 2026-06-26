import axios from 'axios'

const BASE_URL = 'http://localhost:8000'

const client = axios.create({ baseURL: BASE_URL })

export async function uploadVideo(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await client.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    },
  })
  return res.data // { video_path, filename }
}

export async function classifyVideo(videoPath) {
  const res = await client.post('/api/classify', { video_path: videoPath })
  return res.data // { exercise, confidence, total_frames, valid_frames, votes }
}

export async function detectInjuries(videoPath, exercise) {
  const res = await client.post('/api/injury-detection', {
    video_path: videoPath,
    exercise,
  })
  return res.data // { exercise, supported, feedback[], ... }
}
