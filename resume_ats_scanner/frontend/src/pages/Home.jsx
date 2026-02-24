import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyze } from '../api/client';

export default function Home() {
  const navigate = useNavigate();
  const [resumeFile, setResumeFile] = useState(null);
  const [jdFile, setJdFile] = useState(null);
  const [jdText, setJdText] = useState('');
  const [jdInputMode, setJdInputMode] = useState('text'); // 'text' or 'file'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!resumeFile) {
      setError('Please upload your resume PDF');
      return;
    }
    if (jdInputMode === 'text' && !jdText.trim()) {
      setError('Please paste job description or upload JD PDF');
      return;
    }
    if (jdInputMode === 'file' && !jdFile) {
      setError('Please upload job description PDF');
      return;
    }

    setLoading(true);
    try {
      const result = await analyze(
        resumeFile,
        jdInputMode === 'file' ? jdFile : null,
        jdInputMode === 'text' ? jdText : null
      );
      navigate('/results', { state: { analysis: result } });
    } catch (err) {
      let errMsg = 'Analysis failed';
      if (err.code === 'ECONNABORTED') errMsg = 'Request timed out. Analysis takes 1-3 min on first run (model loading). Try again.';
      else if (err.code === 'ERR_NETWORK') errMsg = 'Cannot connect to backend. Is it running on http://localhost:8000?';
      else if (err.response?.data?.detail) errMsg = Array.isArray(err.response.data.detail) ? err.response.data.detail.map(e => e.msg).join('; ') : err.response.data.detail;
      else if (err.message) errMsg = err.message;
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-slate-800 mb-2">
          AI Resume ATS Scanner
        </h1>
        <p className="text-slate-600">
          Upload your resume and job description to get ATS compatibility score and improvement suggestions
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Resume Upload */}
        <div className="bg-white rounded-xl shadow-md p-6 border border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">1. Upload Resume (PDF)</h2>
          <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:border-primary-400 transition">
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setResumeFile(e.target.files[0])}
              className="hidden"
              id="resume-upload"
            />
            <label htmlFor="resume-upload" className="cursor-pointer block">
              <svg className="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="mt-2 text-slate-600">
                {resumeFile ? resumeFile.name : 'Click to upload resume PDF'}
              </p>
            </label>
          </div>
        </div>

        {/* Job Description */}
        <div className="bg-white rounded-xl shadow-md p-6 border border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">2. Job Description</h2>
          
          <div className="flex gap-4 mb-4">
            <button
              type="button"
              onClick={() => setJdInputMode('text')}
              className={`px-4 py-2 rounded-lg font-medium ${
                jdInputMode === 'text' ? 'bg-primary-600 text-white' : 'bg-slate-100 text-slate-600'
              }`}
            >
              Paste Text
            </button>
            <button
              type="button"
              onClick={() => setJdInputMode('file')}
              className={`px-4 py-2 rounded-lg font-medium ${
                jdInputMode === 'file' ? 'bg-primary-600 text-white' : 'bg-slate-100 text-slate-600'
              }`}
            >
              Upload PDF
            </button>
          </div>

          {jdInputMode === 'text' ? (
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste job description here..."
              rows={10}
              className="w-full border border-slate-300 rounded-lg p-4 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          ) : (
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center">
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setJdFile(e.target.files[0])}
                className="hidden"
                id="jd-upload"
              />
              <label htmlFor="jd-upload" className="cursor-pointer block">
                <p className="text-slate-600">
                  {jdFile ? jdFile.name : 'Click to upload job description PDF'}
                </p>
              </label>
            </div>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-4 bg-primary-600 hover:bg-primary-700 disabled:bg-slate-400 text-white font-semibold rounded-xl transition uppercase tracking-wide"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Analyzing (1–3 min on first run)...
            </span>
          ) : 'Analyze Resume'}
        </button>
      </form>
    </div>
  );
}
