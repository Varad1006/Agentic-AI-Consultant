import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'

export default function App() {
  // --- 1. CORE STATE ---
  const [inputText, setInputText] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileObject, setFileObject] = useState(null) // NEW: Holds the file until button is clicked
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState('Idle')
  const [report, setReport] = useState('')
  
  // --- 2. CHAT STATE ---
  const [chatInput, setChatInput] = useState('')
  const [chatHistory, setChatHistory] = useState([])
  const [isChatting, setIsChatting] = useState(false)
  
  // --- 3. PDF REF ---
  const reportRef = useRef(null)

  // --- 4. POLLING EFFECT ---
  useEffect(() => {
    let interval;
    if (jobId && status === 'Processing') {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8000/api/v1/consult/${jobId}/report`);
          const data = await res.json();
          console.log(data);
          console.log(typeof data.answer);
          console.log(data.answer);
          
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

  // --- 5. HANDLERS ---
  
  // Just "attaches" the file to the UI, doesn't submit yet
  const handleFileSelection = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setFileObject(file);
    setSelectedFile(file.name);
    setInputText(''); // Clear text if they select a file
  }

  // The master button that handles BOTH files and text
  const handleGenerateReport = async () => {
    setStatus('Processing');
    setReport('');
    setChatHistory([]);
    
    // Scenario 1: User attached a file
    if (fileObject) {
        const formData = new FormData();
        formData.append('file', fileObject);
    
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
    // Scenario 2: User pasted text
    else if (inputText.trim()) {
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
  }

  const downloadPDF = async () => {
    try {
      const html2pdf = (await import('html2pdf.js')).default;
      const element = reportRef.current;
      const opt = {
        margin:       [0.5, 0.5, 0.5, 0.5],
        filename:     `Apex_Consulting_Architecture_${jobId.substring(0,6)}.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2, useCORS: true },
        jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
      };
      html2pdf().set(opt).from(element).save();
    } catch (err) {
      console.error("PDF generation failed:", err);
      alert("Could not generate PDF. Please ensure html2pdf.js is available.");
    }
  }
  
  const handleSendMessage = async () => {
    if (!chatInput.trim() || !jobId) return;
    
    const userMsg = chatInput;
    setChatInput('');
    setChatHistory(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsChatting(true);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/consult/${jobId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMsg })
      });
      
      const data = await res.json();
      setChatHistory(prev => [...prev, { role: 'assistant', content: typeof data.answer === "string" ? data.answer : JSON.stringify(data.answer, null, 2) }]);
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'assistant', content: "Connection error." }]);
    } finally {
      setIsChatting(false);
    }
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
            <label className="block text-sm font-medium text-gray-700 mb-2">Upload Document (PDF, DOCX, TXT)</label>
            <input 
              type="file" 
              accept=".pdf,.docx,.txt,.csv"
              onChange={handleFileSelection}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            {selectedFile && <p className="mt-2 text-sm text-green-600">Attached: {selectedFile}</p>}
          </div>
          
          <div className="relative flex items-center py-4">
            <div className="flex-grow border-t border-gray-300"></div>
            <span className="mx-4 text-gray-400 text-sm">OR PASTE TEXT</span>
            <div className="flex-grow border-t border-gray-300"></div>
          </div>
          
          <textarea
            className="w-full h-32 p-4 border rounded-md focus:ring-2 focus:ring-blue-500 mb-4"
            placeholder="Paste your business context or SOPs here..."
            value={inputText}
            onChange={(e) => {
                setInputText(e.target.value);
                setFileObject(null); // Clear file if they start typing
                setSelectedFile(null);
            }}
          />
          
          <button 
            onClick={handleGenerateReport}
            disabled={status === 'Processing' || (!inputText.trim() && !fileObject)}
            className="w-full bg-blue-600 text-white py-3 rounded-md font-semibold hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
          >
            {status === 'Processing' ? 'Agents are analyzing...' : 'Generate Architecture Report'}
          </button>
        </section>

        {report && (
          <div className="space-y-8">
            <div className="flex justify-end">
              <button 
                onClick={downloadPDF}
                className="bg-green-600 text-white px-6 py-2 rounded-md font-semibold hover:bg-green-700 shadow-sm flex items-center gap-2"
              >
                Download PDF Report
              </button>
            </div>

            <section ref={reportRef} className="bg-white p-10 rounded-lg shadow-sm border border-gray-200 prose prose-blue max-w-none">
              <ReactMarkdown>{report}</ReactMarkdown>
            </section>

            <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h2 className="text-xl font-bold mb-4">Chat with your Consultant</h2>
              <div className="h-64 overflow-y-auto mb-4 p-4 border rounded bg-gray-50 flex flex-col gap-3">
                {chatHistory.map((msg, idx) => (
                  <div key={idx} className={`p-3 rounded-lg max-w-[80%] ${msg.role === 'user' ? 'bg-blue-100 self-end text-blue-900' : 'bg-white border self-start text-gray-800 shadow-sm'}`}>
                    <strong>{msg.role === 'user' ? 'You' : 'Consultant'}: </strong> 
                    <ReactMarkdown className="inline prose-sm">{msg.content}</ReactMarkdown>
                  </div>
                ))}
                {isChatting && <p className="text-gray-500 italic text-sm">Consultant is typing...</p>}
              </div>
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  className="flex-grow p-3 border rounded focus:ring-2 focus:ring-blue-500"
                  placeholder="Ask a question..."
                />
                <button 
                  onClick={handleSendMessage}
                  disabled={isChatting || !chatInput.trim()}
                  className="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700 disabled:bg-blue-300"
                >
                  Send
                </button>
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  )
}