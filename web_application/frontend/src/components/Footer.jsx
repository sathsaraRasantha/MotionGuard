export default function Footer() {
  return (
    <footer className="no-print mt-auto border-t border-gray-200 bg-white py-8 px-6">
      <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-md bg-green-500 flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <span className="font-semibold text-gray-700 text-sm">MotionGuard</span>
          <span className="text-gray-400 text-xs">· v1.0 Research Prototype</span>
        </div>

        <p className="text-xs text-gray-400 text-center max-w-sm leading-relaxed">
          MotionGuard is an MSc research prototype. Feedback is for educational purposes only and is{' '}
          <strong className="text-gray-500 font-semibold">not a substitute for professional medical or physiotherapy advice</strong>.
        </p>

        <p className="text-xs text-gray-400 whitespace-nowrap">© {new Date().getFullYear()} MotionGuard</p>
      </div>
    </footer>
  )
}
