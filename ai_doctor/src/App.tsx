import React, { useState, useRef } from 'react';
import {
  Heart, Thermometer, Activity, Upload, FileText, User, Stethoscope, TrendingUp,
  AlertTriangle, Shield, Plus, X, Loader2, CheckCircle, Calendar
} from 'lucide-react';
import { ChatPanel } from './ChatPanel';
import { Auth } from './Auth';
import { DoctorPortal } from './DoctorPortal';

// --- CHILD COMPONENTS ---

const PatientInputForm = ({
  patientData, setPatientData,
  symptoms, setSymptoms,
  vitals, setVitals,
  labReport, setLabReport,
  healthRecord, setHealthRecord,
  onGenerateReport,
  isLoading,
}) => {
  const [newSymptom, setNewSymptom] = useState('');
  const [formError, setFormError] = useState('');
  const labReportRef = useRef<HTMLInputElement>(null);
  const healthRecordRef = useRef<HTMLInputElement>(null);

  const addSymptom = () => {
    if (newSymptom.trim()) {
      setSymptoms([...symptoms, { name: newSymptom.trim(), duration: '', severity: 'mild' }]);
      setNewSymptom('');
    }
  };

  const removeSymptom = (index: number) => {
    setSymptoms(symptoms.filter((_, i) => i !== index));
  };

  const updateSymptom = (index: number, field: string, value: string) => {
    const updated = symptoms.map((symptom, i) =>
      i === index ? { ...symptom, [field]: value } : symptom
    );
    setSymptoms(updated);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>, setFile: (f: File | null) => void) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0]);
    }
  };

  const handleSubmit = () => {
    // Basic validation
    if (symptoms.length === 0) {
      setFormError('Please add at least one symptom.');
      return;
    }
    setFormError('');
    onGenerateReport();
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-6 rounded-lg mb-8">
        <h1 className="text-3xl font-bold mb-2">ClinicaFlow</h1>
        <p className="text-blue-100">Please provide your health information for AI-powered diagnostic analysis</p>
      </div>

      {/* Patient Information */}
      <div className="bg-gray-50 p-6 rounded-lg mb-6">
        <div className="flex items-center mb-4">
          <User className="text-indigo-600 mr-3" size={24} />
          <h2 className="text-xl font-semibold text-gray-800">Patient Information</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Weight (kg)</label>
            <input
              type="number"
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              placeholder="kg"
              value={patientData.weight}
              onChange={(e) => setPatientData({ ...patientData, weight: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Height (cm)</label>
            <input
              type="number"
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              placeholder="cm"
              value={patientData.height}
              onChange={(e) => setPatientData({ ...patientData, height: e.target.value })}
            />
          </div>
        </div>
      </div>

      {/* Symptoms Section */}
      <div className="bg-gray-50 p-6 rounded-lg mb-6">
        <div className="flex items-center mb-4">
          <Stethoscope className="text-red-500 mr-3" size={24} />
          <h2 className="text-xl font-semibold text-gray-800">Current Symptoms <span className="text-red-500">*</span></h2>
        </div>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            placeholder="Enter a symptom (e.g., headache, fever)"
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            value={newSymptom}
            onChange={(e) => setNewSymptom(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addSymptom()}
          />
          <button
            onClick={addSymptom}
            className="px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center transition-colors"
          >
            <Plus size={20} />
          </button>
        </div>
        <div className="space-y-4">
          {symptoms.map((symptom, index) => (
            <div key={index} className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium text-gray-800">{symptom.name}</h3>
                <button onClick={() => removeSymptom(index)} className="text-red-500 hover:text-red-700 transition-colors">
                  <X size={20} />
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Duration</label>
                  <select
                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    value={symptom.duration}
                    onChange={(e) => updateSymptom(index, 'duration', e.target.value)}
                  >
                    <option value="">Select duration</option>
                    <option value="less_than_1_hour">Less than 1 hour</option>
                    <option value="1_24_hours">1–24 hours</option>
                    <option value="1_7_days">1–7 days</option>
                    <option value="1_4_weeks">1–4 weeks</option>
                    <option value="more_than_1_month">More than 1 month</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Severity</label>
                  <select
                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    value={symptom.severity}
                    onChange={(e) => updateSymptom(index, 'severity', e.target.value)}
                  >
                    <option value="mild">Mild</option>
                    <option value="moderate">Moderate</option>
                    <option value="severe">Severe</option>
                  </select>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Vitals Section */}
      <div className="bg-gray-50 p-6 rounded-lg mb-6">
        <div className="flex items-center mb-4">
          <Activity className="text-green-500 mr-3" size={24} />
          <h2 className="text-xl font-semibold text-gray-800">Vital Signs</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Thermometer className="inline mr-2" size={16} />Temperature (°F)
            </label>
            <input type="number" step="0.1" className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none" placeholder="98.6" value={vitals.temperature} onChange={(e) => setVitals(prev => ({ ...prev, temperature: e.target.value }))} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Heart className="inline mr-2" size={16} />Blood Pressure
            </label>
            <div className="flex gap-2">
              <input type="number" className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none" placeholder="120" value={vitals.bp_systolic} onChange={(e) => setVitals(prev => ({ ...prev, bp_systolic: e.target.value }))} />
              <span className="self-center text-gray-500 font-medium">/</span>
              <input type="number" className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none" placeholder="80" value={vitals.bp_diastolic} onChange={(e) => setVitals(prev => ({ ...prev, bp_diastolic: e.target.value }))} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">SpO2 (%)</label>
            <input type="number" className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none" placeholder="98" value={vitals.spo2} onChange={(e) => setVitals(prev => ({ ...prev, spo2: e.target.value }))} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Heart Rate (bpm)</label>
            <input type="number" className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none" placeholder="72" value={vitals.pulse} onChange={(e) => setVitals(prev => ({ ...prev, pulse: e.target.value }))} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Respiratory Rate</label>
            <input type="number" className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none" placeholder="16" value={vitals.respiratory_rate} onChange={(e) => setVitals(prev => ({ ...prev, respiratory_rate: e.target.value }))} />
          </div>
        </div>
      </div>

      {/* File Uploads */}
      <div className="bg-gray-50 p-6 rounded-lg mb-6">
        <div className="flex items-center mb-4">
          <Upload className="text-purple-500 mr-3" size={24} />
          <h2 className="text-xl font-semibold text-gray-800">Medical Records</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Lab Reports</label>
            <input type="file" ref={labReportRef} onChange={(e) => handleFileChange(e, setLabReport)} className="hidden" accept=".pdf,.jpg,.png" />
            <div
              onClick={() => labReportRef.current?.click()}
              className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-indigo-400 transition-colors cursor-pointer"
            >
              <Upload className="mx-auto mb-2 text-gray-400" size={32} />
              {labReport
                ? <p className="text-sm text-green-600 font-medium">{labReport.name}</p>
                : <p className="text-gray-600">Click to upload</p>
              }
              <p className="text-xs text-gray-500 mt-1">PDF, JPG, PNG up to 10MB</p>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Previous Health Records</label>
            <input type="file" ref={healthRecordRef} onChange={(e) => handleFileChange(e, setHealthRecord)} className="hidden" accept=".pdf,.doc,.docx" />
            <div
              onClick={() => healthRecordRef.current?.click()}
              className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-indigo-400 transition-colors cursor-pointer"
            >
              <FileText className="mx-auto mb-2 text-gray-400" size={32} />
              {healthRecord
                ? <p className="text-sm text-green-600 font-medium">{healthRecord.name}</p>
                : <p className="text-gray-600">Click to upload</p>
              }
              <p className="text-xs text-gray-500 mt-1">PDF, DOC, DOCX up to 10MB</p>
            </div>
          </div>
        </div>
      </div>

      {/* Validation error */}
      {formError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
          <AlertTriangle size={16} />
          {formError}
        </div>
      )}

      {/* Submit Button */}
      <div className="text-center">
        <button
          onClick={handleSubmit}
          disabled={isLoading}
          className={`inline-flex items-center gap-3 px-8 py-4 rounded-lg text-lg font-semibold shadow-lg transition-all duration-200
            ${isLoading
              ? 'bg-indigo-400 cursor-not-allowed opacity-80 scale-100'
              : 'bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 transform hover:scale-105 cursor-pointer text-white'
            } text-white`}
        >
          {isLoading ? (
            <>
              <Loader2 size={20} className="animate-spin" />
              Analysing patient data…
            </>
          ) : (
            'Generate ClinicaFlow Report'
          )}
        </button>
        <p className="text-sm text-gray-500 mt-2">
          {isLoading ? 'This may take a moment. Please wait.' : 'Fill in your details above, then click to begin.'}
        </p>
      </div>
    </div>
  );
};

const BookAppointment = ({ patientId }: { patientId: number }) => {
  const [doctors, setDoctors] = useState<any[]>([]);
  const [selectedDoctor, setSelectedDoctor] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [status, setStatus] = useState<{type: 'idle' | 'loading' | 'success' | 'error', msg: string}>({type: 'idle', msg: ''});

  React.useEffect(() => {
    fetch('http://127.0.0.1:8000/api/doctors')
      .then(res => res.json())
      .then(data => setDoctors(data.doctors || []))
      .catch(() => setStatus({type: 'error', msg: 'Failed to load doctors'}));
  }, []);

  const handleBook = async () => {
    if (!selectedDoctor || !selectedTime) return;
    setStatus({type: 'loading', msg: ''});
    try {
      // Create a date object for today at the selected time (e.g. "14:00")
      const today = new Date();
      const [hours, minutes] = selectedTime.split(':');
      today.setHours(parseInt(hours), parseInt(minutes), 0, 0);
      const isoString = today.toISOString();

      const res = await fetch('http://127.0.0.1:8000/api/appointments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doctor_id: parseInt(selectedDoctor), patient_id: patientId, appointment_time: isoString })
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Booking failed');
      
      setStatus({type: 'success', msg: 'Appointment booked successfully!'});
    } catch (e: any) {
      setStatus({type: 'error', msg: e.message});
    }
  };

  const availableSlots = ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"];

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-indigo-100">
      <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2"><Calendar className="text-indigo-500" size={20} /> Book Appointment</h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm text-gray-600 mb-1">Select Specialist</label>
          <select className="w-full p-2 border rounded focus:ring-2 focus:ring-indigo-500" value={selectedDoctor} onChange={e => setSelectedDoctor(e.target.value)}>
            <option value="">-- Choose Doctor --</option>
            {doctors.map(d => <option key={d.id} value={d.id}>{d.name} ({d.specialty})</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm text-gray-600 mb-1">Select Time (Today)</label>
          <select className="w-full p-2 border rounded focus:ring-2 focus:ring-indigo-500" value={selectedTime} onChange={e => setSelectedTime(e.target.value)}>
            <option value="">-- Choose Time --</option>
            {availableSlots.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <button 
          onClick={handleBook}
          disabled={!selectedDoctor || !selectedTime || status.type === 'loading'}
          className="w-full py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {status.type === 'loading' ? 'Booking...' : 'Confirm Appointment'}
        </button>
        {status.msg && (
          <div className={`text-sm p-2 rounded ${status.type === 'error' ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}`}>
            {status.msg}
          </div>
        )}
      </div>
    </div>
  );
};

// --- CLINICIAN DASHBOARD ---

const ClinicianDashboard = ({ patientProfile, patientData, vitals, symptoms, finalReportData, finalReportUrl }: any) => {
  const calculateBMI = () => {
    if (patientData.weight && patientData.height) {
      const heightInMeters = patientData.height / 100;
      return (patientData.weight / (heightInMeters * heightInMeters)).toFixed(1);
    }
    return 'N/A';
  };

  const rawInput = finalReportData?.raw_input?.patient_data;
  const primarySymptoms = (rawInput?.symptoms && rawInput.symptoms !== 'No symptoms reported')
    ? rawInput.symptoms
    : (symptoms.length > 0 ? symptoms.map((s: any) => s.name).join(', ') : 'N/A');
  const longestDuration = (rawInput?.duration && rawInput.duration !== 'N/A')
    ? rawInput.duration
    : (symptoms.length > 0 ? symptoms[0]?.duration.replace(/_/g, ' ') : 'N/A');

  const analysisData = finalReportData?.final_analysis?.analysis;
  let diagnoses: any[] = [];

  if (analysisData) {
    if (analysisData.probable_diagnosis) {
      diagnoses.push({
        condition: analysisData.probable_diagnosis.condition || 'Unknown',
        confidence: analysisData.probable_diagnosis.confidence || 0,
        evidence: analysisData.probable_diagnosis.evidence || [],
        urgency: (analysisData.probable_diagnosis.urgency || 'low').toLowerCase()
      });
    }
    if (analysisData.differential_diagnosis) {
      let baseConfidence = Math.max(10, (analysisData.probable_diagnosis?.confidence || 80) - 15);
      analysisData.differential_diagnosis.forEach((d: any, i: number) => {
        diagnoses.push({
          condition: d.condition,
          confidence: Math.max(5, baseConfidence - (i * 15)),
          evidence: [d.reasoning],
          urgency: 'low'
        });
      });
    }
  }

  if (diagnoses.length === 0) {
    diagnoses = [{ condition: 'Waiting for AI Analysis…', confidence: 0, evidence: [], urgency: 'low' }];
  }

  const criticalAlert = analysisData?.probable_diagnosis?.urgency?.toLowerCase() === 'high'
    ? `Urgency: High — ${analysisData.probable_diagnosis.condition}`
    : null;

  return (
    <div className="max-w-7xl mx-auto p-6 bg-gray-100 min-h-screen">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Diagnostic Results</h2>
        <p className="text-gray-500 text-sm mt-1">AI-generated preliminary analysis — always confirm with a qualified clinician.</p>
      </div>

      {criticalAlert && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded-lg">
          <div className="flex items-center">
            <AlertTriangle className="text-red-500 mr-3 flex-shrink-0" size={24} />
            <div>
              <h3 className="text-lg font-semibold text-red-800">Critical Alert: Immediate Attention Required</h3>
              <p className="text-red-700">{criticalAlert}</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Diagnostic Results */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center mb-4">
              <TrendingUp className="text-blue-500 mr-3" size={24} />
              <h2 className="text-xl font-semibold text-gray-800">Differential Diagnoses</h2>
            </div>
            <div className="space-y-4">
              {diagnoses.map((diagnosis, index) => (
                <div key={index} className={`border rounded-lg p-4 ${
                  diagnosis.urgency === 'high' ? 'border-red-300 bg-red-50' :
                  diagnosis.urgency === 'medium' ? 'border-yellow-300 bg-yellow-50' :
                  'border-gray-200 bg-white'
                }`}>
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="font-semibold text-gray-800">{index + 1}. {diagnosis.condition}</h3>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-600">{diagnosis.confidence}% confidence</span>
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${diagnosis.confidence > 80 ? 'bg-red-500' : diagnosis.confidence > 60 ? 'bg-yellow-500' : 'bg-green-500'}`}
                          style={{ width: `${diagnosis.confidence}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  <div className="text-sm text-gray-600">
                    <strong>Supporting Evidence:</strong>
                    <ul className="ml-4 mt-1">
                      {diagnosis.evidence.map((item: string, i: number) => <li key={i}>• {item}</li>)}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {finalReportUrl && (
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center mb-4">
                <FileText className="text-purple-500 mr-3" size={24} />
                <h2 className="text-xl font-semibold text-gray-800">Final Clinical Report</h2>
              </div>
              <iframe src={finalReportUrl} className="w-full h-96 border rounded-lg" title="Generated Report" />
              <div className="mt-4 text-center">
                <a
                  href={finalReportUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 inline-block transition-colors"
                >
                  Open PDF in New Tab
                </a>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="font-semibold text-gray-800 mb-4">Patient Summary</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-gray-600">Name:</span><span className="font-medium">{patientProfile.name || 'N/A'}</span></div>
              <div className="flex justify-between"><span className="text-gray-600">Age:</span><span>{patientProfile.age || 'N/A'} years</span></div>
              <div className="flex justify-between"><span className="text-gray-600">Gender:</span><span className="capitalize">{patientProfile.gender || 'N/A'}</span></div>
              <div className="flex justify-between"><span className="text-gray-600">BMI:</span><span>{calculateBMI()}</span></div>
              <div className="flex justify-between"><span className="text-gray-600">Symptoms:</span><span className="text-right max-w-[60%]">{primarySymptoms}</span></div>
              <div className="flex justify-between"><span className="text-gray-600">Duration:</span><span className="capitalize">{longestDuration}</span></div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="font-semibold text-gray-800 mb-4">Current Vitals</h3>
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1 text-gray-600"><Thermometer size={14} className="text-red-500" />Temperature</span>
                <span className="font-medium">{vitals.temperature || 'N/A'} °F</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1 text-gray-600"><Heart size={14} className="text-red-500" />Blood Pressure</span>
                <span className="font-medium">{vitals.bp_systolic || 'N/A'}/{vitals.bp_diastolic || 'N/A'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1 text-gray-600"><Activity size={14} className="text-red-500" />Heart Rate</span>
                <span className="font-medium">{vitals.pulse || 'N/A'} bpm</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1 text-gray-600"><Activity size={14} className="text-green-500" />SpO2</span>
                <span className="font-medium">{vitals.spo2 || 'N/A'}%</span>
              </div>
            </div>
          </div>

          {/* Interview summary if available */}
          {finalReportData?.interview_summary && (
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-4">Interview Summary</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Turns completed:</span>
                  <span className="font-medium">{finalReportData.interview_summary.total_turns}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Confidence:</span>
                  <span className="font-medium">{Math.round((finalReportData.interview_summary.final_confidence || 0) * 100)}%</span>
                </div>
                {finalReportData.interview_summary.unavailable_information?.length > 0 && (
                  <div>
                    <span className="text-gray-600 block mb-1">Patient could not provide:</span>
                    <ul className="ml-2 text-gray-500">
                      {finalReportData.interview_summary.unavailable_information.map((item: string, i: number) => (
                        <li key={i}>• {item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
          
          <BookAppointment patientId={patientProfile.id} />
        </div>
      </div>
    </div>
  );
};

// --- MAIN PARENT COMPONENT ---

const DiagnosticSystem = ({ patientProfile, onLogout }: { patientProfile: any, onLogout: () => void }) => {
  const [activeTab, setActiveTab] = useState('patient');
  const [symptoms, setSymptoms] = useState<{ name: string; duration: string; severity: string }[]>([]);
  const [vitals, setVitals] = useState({ temperature: '', bp_systolic: '', bp_diastolic: '', spo2: '', pulse: '', respiratory_rate: '' });
  const [patientData, setPatientData] = useState({ weight: '', height: '' });
  const [labReport, setLabReport] = useState<File | null>(null);
  const [healthRecord, setHealthRecord] = useState<File | null>(null);

  // Conversation state
  const [messages, setMessages] = useState<{ sender: 'ai' | 'user'; text: string }[]>([]);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false); // FIX: was incorrectly initialised to true
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [finalReport, setFinalReport] = useState<any | null>(null);
  const [finalReportUrl, setFinalReportUrl] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const handleStartConversation = async () => {
    if (isLoading) return; // Prevent double-submit
    setIsLoading(true);
    setApiError(null);

    const jsonData = {
      patient_profile: patientProfile,
      patient_data: {
        weight: parseInt(patientData.weight) || 0,
        symptoms: symptoms.map(s => s.name).join(', ') || 'No symptoms reported',
        duration: symptoms.length > 0 ? symptoms[0].duration.replace(/_/g, ' ') : 'N/A',
        vitals: {
          temperature: vitals.temperature,
          bp: `${vitals.bp_systolic}/${vitals.bp_diastolic}`,
          pulse: vitals.pulse,
          spo2: vitals.spo2,
        },
      },
    };

    try {
      const formData = new FormData();
      formData.append('user_input_json', JSON.stringify(jsonData));
      if (labReport) formData.append('lab_report', labReport);
      if (healthRecord) formData.append('health_record', healthRecord);

      const response = await fetch('http://127.0.0.1:8000/diagnose/chat', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error: ${response.status}`);
      }

      const result = await response.json();
      setConversationId(result.conversation_id);

      if (result.ai_message) {
        setMessages([{ sender: 'ai', text: result.ai_message }]);
        setIsChatOpen(true);
      } else if (result.is_complete) {
        setFinalReport(result.final_report_data);
        setFinalReportUrl(result.final_report_url);
        setIsChatOpen(false);
        setActiveTab('results');
      }
    } catch (err: any) {
      console.error('Start error:', err);
      setApiError(err.message || 'Failed to connect to the server. Make sure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleContinueConversation = async (answer: string) => {
    if (!conversationId || isLoading) return;
    setMessages(prev => [...prev, { sender: 'user', text: answer }]);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('conversation_id', conversationId);
      formData.append('user_input_json', JSON.stringify({ answer, patient_profile: patientProfile }));

      const response = await fetch('http://127.0.0.1:8000/diagnose/chat', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error: ${response.status}`);
      }

      const result = await response.json();

      if (result.ai_message) {
        setMessages(prev => [...prev, { sender: 'ai', text: result.ai_message }]);
      } else if (result.is_complete) {
        // Agent has finished — close chat, show results
        setMessages(prev => [...prev, { sender: 'ai', text: '✅ Thank you! Your diagnostic report is ready.' }]);
        setFinalReport(result.final_report_data);
        setFinalReportUrl(result.final_report_url);
        // Small delay so user sees the final message before the panel closes
        setTimeout(() => {
          setIsChatOpen(false);
          setActiveTab('results');
        }, 1500);
      }
    } catch (err: any) {
      console.error('Continue error:', err);
      setMessages(prev => [...prev, { sender: 'ai', text: '⚠️ Something went wrong. Please try again.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Tabs */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between">
            <nav className="flex space-x-8" aria-label="Tabs">
              <button
                onClick={() => setActiveTab('patient')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'patient'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Patient Input
              </button>
              <button
                onClick={() => setActiveTab('results')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'results'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Diagnostic Results
                {finalReport && <span className="ml-2 bg-green-500 text-white text-xs rounded-full px-2 py-0.5">Ready</span>}
              </button>
            </nav>
            <div className="flex items-center gap-4">
              {isLoading && (
                <div className="flex items-center gap-2 text-indigo-600 text-sm font-medium">
                  <Loader2 size={16} className="animate-spin" />
                  Processing…
                </div>
              )}
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <User size={16} />
                <span>{patientProfile.name}</span>
                <button onClick={onLogout} className="ml-2 text-red-500 hover:text-red-700 font-medium">Logout</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* API Error Banner */}
      {apiError && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-3 flex items-center gap-3 text-red-700 text-sm">
          <AlertTriangle size={16} className="flex-shrink-0" />
          <span>{apiError}</span>
          <button onClick={() => setApiError(null)} className="ml-auto text-red-500 hover:text-red-700">
            <X size={16} />
          </button>
        </div>
      )}

      {/* Content Area */}
      {activeTab === 'patient' ? (
        <PatientInputForm
          patientData={patientData}
          setPatientData={setPatientData}
          symptoms={symptoms}
          setSymptoms={setSymptoms}
          vitals={vitals}
          setVitals={setVitals}
          labReport={labReport}
          setLabReport={setLabReport}
          healthRecord={healthRecord}
          setHealthRecord={setHealthRecord}
          onGenerateReport={handleStartConversation}
          isLoading={isLoading}
        />
      ) : (
        <ClinicianDashboard
          patientProfile={patientProfile}
          patientData={patientData}
          vitals={vitals}
          symptoms={symptoms}
          finalReportData={finalReport}
          finalReportUrl={finalReportUrl}
        />
      )}

      {/* Chat Panel — only shown while agent is asking questions */}
      {isChatOpen && (
        <ChatPanel
          messages={messages}
          onSendMessage={handleContinueConversation}
          isLoading={isLoading}
        />
      )}
    </div>
  );
};

export default function App() {
  const [userProfile, setUserProfile] = useState<any>(null);

  if (!userProfile) {
    return <Auth onLogin={setUserProfile} />;
  }

  if (userProfile.role === 'doctor') {
    return <DoctorPortal onLogout={() => setUserProfile(null)} doctorProfile={userProfile} />;}

  return <DiagnosticSystem patientProfile={userProfile} onLogout={() => setUserProfile(null)} />;
}