import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadResume = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/upload_resume', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const uploadJobDescription = async (fileOrText) => {
  if (typeof fileOrText === 'string') {
    const formData = new FormData();
    formData.append('text', fileOrText);
    const { data } = await api.post('/upload_job_description', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  }
  const formData = new FormData();
  formData.append('file', fileOrText);
  const { data } = await api.post('/upload_job_description', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const analyze = async (resumeFile, jdFile, jdText) => {
  const formData = new FormData();
  formData.append('resume_file', resumeFile);
  if (jdFile) {
    formData.append('jd_file', jdFile);
  }
  if (jdText) {
    formData.append('jd_text', jdText);
  }
  // Use axios directly (no Content-Type) so FormData gets correct multipart boundary
  const { data } = await axios.post(`${API_BASE}/analyze`, formData, {
    timeout: 300000,
  });
  return data;
};

export const downloadReport = (analysisId) => {
  return `${API_BASE}/download_report/${analysisId}`;
};

export const getHistory = async () => {
  const { data } = await api.get('/history');
  return data;
};
