import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import html2pdf from 'html2pdf.js'

export default function App() {
  const [inputText, setInputText] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState('Idle')
  const [report, setReport] = useState('')
  
  // NEW: Reference to the report container for PDF generation
  const reportRef = useRef(null)

  // Poll the backend every 3 seconds while processing
  useEffect(() => {
    let interval;
    if (jobId && status === 'Processing') {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8000/api/v1/consult/${jobId}/report`);
          const data = await res.json();
          
          if (res.status === 200 && data.content) {
            setReport(data.content);
            setStatus('Completed');
            clearInterval(interval);
          }
        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [jobId, status]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setSelectedFile(file.name);
    setStatus('Processing');
    setReport('');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:8000/api/v1/upload', {
        method: 'POST',
        body: formData
      });
      
      if (!res.ok) throw new Error(`API Error: ${res.status}`);
      const data = await res.json();
      setJobId(data.job_id);
    } catch (err) {
      setStatus('Failed to upload document');
    }
  }

  const handleSubmitText = async () => {
    setStatus('Processing');
    setReport('');
    try {
      const res = await fetch('http://localhost:8000/api/v1/consult', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_text: inputText })
      });
      if (!res.ok) throw new Error(`API Error: ${res.status}`);
      const data = await res.json();
      setJobId(data.job_id);
    } catch (err) {
      setStatus('Failed to connect to API');
    }
  }

  // NEW: Function to trigger the PDF download
  const downloadPDF = () => {
    const element = reportRef.current;
    const opt = {
      margin:       [0.5, 0.5, 0.5, 0.5],
      filename:     `Apex_Consulting_Architecture_${jobId.substring(0,6)}.pdf`,
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { scale: 2, useCORS: true },
      jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(element).save();
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-8">
        
        <header className="text-center">
          <h1 className="text-4xl font-bold text-gray-900">Autonomous AI Consultant</h1>
          <p className="text-gray-500 mt-2">Upload your business processes for instant architectural analysis and ROI.</p>
        </header>

        <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload a Business Process Document (PDF, DOCX, TXT)
            </label>
            <input 
              type="file" 
              accept=".pdf,.docx,.txt,.csv"
              onChange={handleFileUpload}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            {selectedFile && <p className="mt-2 text-sm text-green-600">Attached: {selectedFile}</p>}
          </div>

          <div className="relative flex items-center py-4">
            <div className="flex-grow border-t border-gray-300"></div>
            <span className="flex-shrink-0 mx-4 text-gray-400 text-sm font-medium">OR PASTE TEXT</span>
            <div className="flex-grow border-t border-gray-300"></div>
          </div>

          <textarea
            className="w-full h-32 p-4 border rounded-md focus:ring-2 focus:ring-blue-500 mb-4"
            placeholder="Paste your business context or SOPs here..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
          />
          <button 
            onClick={handleSubmitText}
            disabled={status === 'Processing' || (!inputText && !selectedFile)}
            className="w-full bg-blue-600 text-white py-3 rounded-md font-semibold hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
          >
            {status === 'Processing' ? 'Agents are analyzing...' : 'Generate Architecture Report'}
          </button>
        </section>

        {report && (
          <div className="space-y-4">
            {/* NEW: PDF Download Action Bar */}
            <div className="flex justify-end">
              <button 
                onClick={downloadPDF}
                className="bg-green-600 text-white px-6 py-2 rounded-md font-semibold hover:bg-green-700 shadow-sm flex items-center gap-2 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download PDF Report
              </button>
            </div>

            {/* The report wrapper ref for the PDF generator */}
            <section ref={reportRef} className="bg-white p-10 rounded-lg shadow-sm border border-gray-200 prose prose-blue max-w-none">
              <ReactMarkdown>{report}</ReactMarkdown>
            </section>
          </div>
        )}
        
      </div>
    </div>
  )
}