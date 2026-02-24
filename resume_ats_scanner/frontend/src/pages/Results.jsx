import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { downloadReport } from '../api/client';

const COLORS = ['#3b82f6', '#06b6d4', '#22c55e', '#eab308', '#ef4444'];

export default function Results() {
  const location = useLocation();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState(location.state?.analysis || null);

  useEffect(() => {
    if (!analysis) {
      navigate('/');
    }
  }, [analysis, navigate]);

  if (!analysis) return null;

  const pieData = analysis.score_breakdown?.map((b, i) => ({
    name: b.component.replace(' Score', ''),
    value: b.score,
    color: COLORS[i % COLORS.length],
  })) || [];

  const barData = analysis.score_breakdown?.map((b, i) => ({
    name: b.component.replace(' Score', '').slice(0, 15),
    score: b.score,
  })) || [];

  const reportUrl = downloadReport(analysis.analysis_id);

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-800">Analysis Results</h1>
        <a
          href={reportUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition"
        >
          Download PDF Report
        </a>
      </div>

      {/* ATS Score */}
      <div className="bg-white rounded-xl shadow-md p-8 border border-slate-200">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">ATS Compatibility Score</h2>
        <div className="flex items-center gap-8">
          <div className="flex-1">
            <div className="h-4 bg-slate-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  analysis.total_ats_score >= 70 ? 'bg-green-500' :
                  analysis.total_ats_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${Math.min(100, analysis.total_ats_score)}%` }}
              />
            </div>
            <p className="mt-2 text-3xl font-bold text-slate-800">{analysis.total_ats_score}%</p>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-md p-6 border border-slate-200">
          <h3 className="font-semibold text-slate-800 mb-4">Score Breakdown (Pie)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ name, value }) => `${name}: ${value}%`}
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6 border border-slate-200">
          <h3 className="font-semibold text-slate-800 mb-4">Score Breakdown (Bar)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} />
                <YAxis type="category" dataKey="name" width={100} />
                <Bar dataKey="score" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Matched vs Missing Skills */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-md p-6 border border-slate-200">
          <h3 className="font-semibold text-green-700 mb-4">✓ Matched Skills</h3>
          <ul className="space-y-2">
            {(analysis.skill_analysis?.matched_skills || []).map((s, i) => (
              <li key={i} className="flex justify-between items-center bg-green-50 rounded px-3 py-2">
                <span>{s.skill}</span>
                <span className="text-sm text-green-600">{Math.round(s.confidence * 100)}%</span>
              </li>
            ))}
            {(!analysis.skill_analysis?.matched_skills?.length) && (
              <li className="text-slate-500">No matched skills</li>
            )}
          </ul>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6 border border-slate-200">
          <h3 className="font-semibold text-red-700 mb-4">✗ Missing Skills</h3>
          <ul className="space-y-2">
            {(analysis.skill_analysis?.missing_skills || []).map((s, i) => (
              <li key={i} className="bg-red-50 rounded px-3 py-2">{s}</li>
            ))}
            {(!analysis.skill_analysis?.missing_skills?.length) && (
              <li className="text-green-600">All required skills present!</li>
            )}
          </ul>
        </div>
      </div>

      {/* Suggestions */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-slate-200">
        <h3 className="font-semibold text-slate-800 mb-4">Improvement Suggestions</h3>
        <ul className="space-y-2">
          {(analysis.improvement_recommendations || []).map((s, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-primary-500">•</span>
              <span>{s}</span>
            </li>
          ))}
          {(analysis.formatting_suggestions || []).map((s, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-primary-500">•</span>
              <span>{s}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* AI Enhancement */}
      {analysis.ai_enhancement && (
        <div className="bg-white rounded-xl shadow-md p-6 border border-slate-200">
          <h3 className="font-semibold text-slate-800 mb-4">⭐ AI Resume Enhancement</h3>
          <div className="space-y-4">
            {analysis.ai_enhancement.enhanced_bullets?.length > 0 && (
              <div>
                <h4 className="font-medium text-slate-700 mb-2">Bullet Point Suggestions</h4>
                <ul className="space-y-2">
                  {analysis.ai_enhancement.enhanced_bullets.map((b, i) => (
                    <li key={i} className="bg-slate-50 rounded p-3">
                      <p className="text-sm text-slate-500">Original: {b.original}</p>
                      <p className="text-slate-800 mt-1">Suggested: {b.suggested}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {analysis.ai_enhancement.action_verbs?.length > 0 && (
              <div>
                <h4 className="font-medium text-slate-700 mb-2">Strong Action Verbs</h4>
                <p className="text-slate-600">
                  {analysis.ai_enhancement.action_verbs.join(', ')}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
