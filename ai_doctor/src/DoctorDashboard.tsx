import React, { useState } from 'react';
import { User, Activity, FileText, MessageSquare, Zap, Loader2, Send } from 'lucide-react';

export const DoctorDashboard = ({ appointment, onBack }: { appointment: any, onBack: () => void }) => {
  const [activeTab, setActiveTab] = useState('summary');
  const [fastSummary, setFastSummary] = useState<string | null>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);
  
  // AI Assistant state
  const [chatMessages, setChatMessages] = useState<{sender: 'ai' | 'doctor', text: string}[]>([]);
  const [query, setQuery] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [pastReports, setPastReports] = useState<any[]>([]);

  React.useEffect(() => {
    fetch(`http://127.0.0.1:8000/api/patients/${appointment.patient.id}/reports`)
      .then(res => res.json())
      .then(data => setPastReports(data.reports || []))
      .catch(err => console.error("Failed to load reports", err));
  }, [appointment.patient.id]);

  const handleGenerateSummary = async () => {
    setIsLoadingSummary(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/appointments/${appointment.appointment_id}/summary`);
      const data = await res.json();
      setFastSummary(data.summary);
      setActiveTab('summary');
    } catch (e) {
      console.error(e);
      setFastSummary("Error fetching summary.");
    } finally {
      setIsLoadingSummary(false);
    }
  };

  const handleAskQuestion = async () => {
    if (!query.trim()) return;
    const currentQuery = query;
    setChatMessages(prev => [...prev, { sender: 'doctor', text: currentQuery }]);
    setQuery('');
    setIsAsking(true);
    
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/rag_qa`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: appointment.patient.id, query: currentQuery })
      });
      const data = await res.json();
      setChatMessages(prev => [...prev, { sender: 'ai', text: data.answer }]);
    } catch (e) {
      console.error(e);
      setChatMessages(prev => [...prev, { sender: 'ai', text: 'Error fetching response.' }]);
    } finally {
      setIsAsking(false);
    }
  };

  const patient = appointment.patient;

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-gray-50">
      {/* Patient Header */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between shadow-sm z-10">
        <div className="flex items-center gap-4">
          <button onClick={onBack} className="md:hidden text-indigo-600 font-medium">← Back</button>
          <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600">
            <User size={24} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">{patient?.name || 'Unknown Patient'}</h2>
            <div className="text-sm text-gray-500 flex gap-4 mt-1">
              <span>Age: {patient?.age}</span>
              <span>Blood Group: {patient?.blood_group}</span>
              <span className="text-indigo-600 font-medium">Time: {new Date(appointment.time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
            </div>
          </div>
        </div>
        <button 
          onClick={handleGenerateSummary}
          disabled={isLoadingSummary}
          className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white px-5 py-2.5 rounded-lg shadow font-medium transition-all"
        >
          {isLoadingSummary ? <Loader2 size={18} className="animate-spin" /> : <Zap size={18} />}
          Generate Fast AI Summary
        </button>
      </div>

      {/* Split View */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Pane: Medical Timeline */}
        <div className="flex-1 border-r flex flex-col bg-white overflow-hidden">
          <div className="border-b px-2 flex gap-1 bg-gray-50 pt-2">
            <button 
              onClick={() => setActiveTab('summary')}
              className={`px-4 py-2 font-medium text-sm rounded-t-lg transition-colors ${activeTab === 'summary' ? 'bg-white text-indigo-600 border-t border-x' : 'text-gray-500 hover:text-gray-700'}`}
            >
              Fast Summary
            </button>
            <button 
              onClick={() => setActiveTab('report')}
              className={`px-4 py-2 font-medium text-sm rounded-t-lg transition-colors ${activeTab === 'report' ? 'bg-white text-indigo-600 border-t border-x' : 'text-gray-500 hover:text-gray-700'}`}
            >
              Active Intake Report
            </button>
            <button 
              onClick={() => setActiveTab('past_reports')}
              className={`px-4 py-2 font-medium text-sm rounded-t-lg transition-colors ${activeTab === 'past_reports' ? 'bg-white text-indigo-600 border-t border-x' : 'text-gray-500 hover:text-gray-700'}`}
            >
              Past Reports
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-6">
            {activeTab === 'summary' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <Activity className="text-indigo-500" /> AI Clinical Brief
                </h3>
                {fastSummary ? (
                  <div className="bg-indigo-50/50 p-6 rounded-xl border border-indigo-100 prose prose-indigo">
                    <pre className="whitespace-pre-wrap font-sans text-gray-700">{fastSummary}</pre>
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-400">
                    <Zap size={48} className="mx-auto mb-3 opacity-20" />
                    <p>Click "Generate Fast AI Summary" to load</p>
                  </div>
                )}
              </div>
            )}
            {activeTab === 'report' && (
              <div className="h-full flex flex-col">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2 shrink-0">
                  <FileText className="text-indigo-500" /> Intake Report
                </h3>
                {pastReports.length > 0 && pastReports[0].url ? (
                  <iframe src={pastReports[0].url} className="w-full h-full min-h-[500px] border rounded-lg shadow-sm bg-gray-50" title="Latest Report" />
                ) : (
                  <div className="bg-gray-100 rounded-xl h-96 flex items-center justify-center text-gray-400 border-2 border-dashed border-gray-200">
                    <p>No intake report available for this patient.</p>
                  </div>
                )}
              </div>
            )}
            {activeTab === 'past_reports' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <FileText className="text-indigo-500" /> Patient History
                </h3>
                {pastReports.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No past reports found for this patient.</p>
                ) : (
                  <div className="space-y-4">
                    {pastReports.map((report, idx) => (
                      <div key={idx} className="border border-gray-200 rounded-lg p-4 bg-white shadow-sm">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="font-medium text-gray-800">Report from {new Date(report.created_at).toLocaleDateString()}</h4>
                          {report.url && (
                            <a href={report.url} target="_blank" rel="noreferrer" className="text-indigo-600 text-sm hover:underline">
                              View PDF
                            </a>
                          )}
                        </div>
                        <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                          <strong>Probable Diagnosis:</strong> {report.data?.final_analysis?.analysis?.probable_diagnosis?.condition || 'N/A'}
                          <br />
                          <strong>Confidence:</strong> {report.data?.final_analysis?.analysis?.probable_diagnosis?.confidence || 'N/A'}%
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Pane: AI Assistant Widget */}
        <div className="w-1/3 bg-gray-50 flex flex-col border-l border-gray-200">
          <div className="bg-white border-b px-4 py-3 flex items-center gap-2">
            <MessageSquare size={18} className="text-indigo-600" />
            <h3 className="font-semibold text-gray-800">AI Assistant</h3>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.length === 0 && (
              <div className="text-center text-sm text-gray-500 mt-10">
                Ask questions about the patient's history. e.g. "Has their blood pressure increased?"
              </div>
            )}
            {chatMessages.map((msg, i) => (
              <div key={i} className={`flex ${msg.sender === 'doctor' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl px-4 py-2 ${msg.sender === 'doctor' ? 'bg-indigo-600 text-white rounded-br-none' : 'bg-white border text-gray-800 rounded-bl-none shadow-sm'}`}>
                  {msg.text}
                </div>
              </div>
            ))}
            {isAsking && (
              <div className="flex justify-start">
                <div className="bg-white border text-gray-500 rounded-2xl rounded-bl-none px-4 py-2 shadow-sm flex items-center gap-2">
                  <Loader2 size={14} className="animate-spin" /> Thinking...
                </div>
              </div>
            )}
          </div>
          
          <div className="bg-white p-3 border-t">
            <div className="relative flex items-center">
              <input 
                type="text" 
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAskQuestion()}
                placeholder="Ask about patient..."
                className="w-full bg-gray-100 rounded-full py-2 pl-4 pr-10 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button 
                onClick={handleAskQuestion}
                className="absolute right-2 text-indigo-600 hover:text-indigo-800 p-1"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
