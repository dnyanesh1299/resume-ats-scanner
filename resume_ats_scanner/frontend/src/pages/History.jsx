import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHistory, downloadReport } from '../api/client';

export default function History() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHistory()
      .then((data) => setHistory(data.history || []))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

  const handleView = (item) => {
    navigate('/results', { state: { analysis: item } });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Analysis History</h1>
      
      {history.length === 0 ? (
        <div className="bg-white rounded-xl shadow-md p-12 text-center border border-slate-200">
          <p className="text-slate-600">No analysis history yet.</p>
          <p className="text-slate-500 mt-2">Run an analysis from the Home page to see results here.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {history.map((item, i) => (
            <div
              key={item.analysis_id || i}
              className="bg-white rounded-xl shadow-md p-6 border border-slate-200 hover:border-primary-300 transition"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-slate-800">
                    {item.resume_data?.name || 'Unknown'} - {item.jd_data?.job_title || 'Job'}
                  </h3>
                  <p className="text-slate-500 text-sm mt-1">
                    ATS Score: {item.total_ats_score}% • {item.created_at?.slice(0, 10) || 'N/A'}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleView(item)}
                    className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-medium"
                  >
                    View
                  </button>
                  {item.analysis_id && (
                    <a
                      href={downloadReport(item.analysis_id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium"
                    >
                      PDF
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
