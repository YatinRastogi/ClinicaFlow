import React, { useState, useEffect } from 'react';
import { Calendar, Users, LayoutDashboard, Settings, LogOut, ChevronRight, Activity } from 'lucide-react';
import { DoctorDashboard } from './DoctorDashboard';

export const DoctorPortal = ({ onLogout, doctorProfile }: { onLogout: () => void, doctorProfile: any }) => {
  const [schedule, setSchedule] = useState<any[]>([]);
  const [selectedAppointment, setSelectedAppointment] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeMenu, setActiveMenu] = useState<'dashboard' | 'patients'>('dashboard');

  useEffect(() => {
    fetchSchedule();
  }, [doctorProfile.id]);

  const fetchSchedule = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/doctors/${doctorProfile.id}/schedule`);
      if (res.ok) {
        const data = await res.json();
        setSchedule(data.schedule || []);
      }
    } catch (e) {
      console.error('Error fetching schedule', e);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans">
      
      {/* Sidebar Navigation */}
      <div className={`w-72 bg-indigo-900 text-white flex flex-col transition-all duration-300 ${selectedAppointment ? 'hidden md:flex' : 'flex'}`}>
        <div className="p-6">
          <div className="flex items-center gap-3 font-bold text-2xl mb-8 tracking-tight">
            <Activity className="text-indigo-400" size={28} />
            ClinicaFlow
          </div>
          
          <nav className="space-y-2">
            <button onClick={() => setActiveMenu('dashboard')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors ${activeMenu === 'dashboard' ? 'bg-indigo-800 text-indigo-100' : 'text-indigo-200 hover:bg-indigo-800 hover:text-white'}`}>
              <LayoutDashboard size={20} /> Dashboard
            </button>
            <button onClick={() => setActiveMenu('patients')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors ${activeMenu === 'patients' ? 'bg-indigo-800 text-indigo-100' : 'text-indigo-200 hover:bg-indigo-800 hover:text-white'}`}>
              <Users size={20} /> My Patients
            </button>
          </nav>
        </div>

        <div className="mt-auto p-6">
          <button 
            onClick={onLogout}
            className="flex items-center gap-3 w-full px-4 py-3 rounded-lg text-indigo-200 hover:bg-red-500 hover:text-white transition-colors"
          >
            <LogOut size={20} /> Logout
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {selectedAppointment ? (
        <DoctorDashboard 
          appointment={selectedAppointment} 
          onBack={() => setSelectedAppointment(null)} 
        />
      ) : (
        <div className="flex-1 flex flex-col overflow-y-auto">
          <header className="bg-white border-b px-8 py-6">
            <h1 className="text-2xl font-bold text-gray-800">Welcome, {doctorProfile.name}</h1>
            <p className="text-gray-500 mt-1">Here is your {activeMenu === 'dashboard' ? 'schedule for today' : 'patient list'}.</p>
          </header>

          <div className="p-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
                <h2 className="font-semibold text-gray-700 flex items-center gap-2">
                  {activeMenu === 'dashboard' ? (
                    <><Calendar size={18} className="text-indigo-500" /> Today's Appointments</>
                  ) : (
                    <><Users size={18} className="text-indigo-500" /> All Patients</>
                  )}
                </h2>
              </div>
              
              {isLoading ? (
                <div className="p-12 text-center text-gray-500">Loading...</div>
              ) : schedule.length === 0 ? (
                <div className="p-12 text-center text-gray-500">
                  <p>No data available.</p>
                </div>
              ) : activeMenu === 'dashboard' ? (
                <div className="divide-y divide-gray-100">
                  {schedule.map((appt, index) => (
                    <div 
                      key={index} 
                      onClick={() => setSelectedAppointment(appt)}
                      className="p-6 flex items-center justify-between hover:bg-indigo-50 cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center font-bold text-lg">
                          {appt.patient?.name?.charAt(0) || '?'}
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">{appt.patient?.name || 'Unknown'}</h3>
                          <div className="text-sm text-gray-500 flex gap-3 mt-1">
                            <span>Age: {appt.patient?.age}</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-gray-800 text-lg">
                          {new Date(appt.time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${appt.status === 'Scheduled' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                          {appt.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="divide-y divide-gray-100">
                  {/* Derive unique patients from schedule */}
                  {Array.from(new Map(schedule.map(appt => [appt.patient.id, appt.patient])).values()).map((patient: any, index) => (
                    <div key={index} className="p-6 flex items-center justify-between hover:bg-indigo-50 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center font-bold text-lg">
                          {patient?.name?.charAt(0) || '?'}
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900 text-lg">{patient?.name}</h3>
                          <p className="text-sm text-gray-500">Age: {patient?.age} • Blood Group: {patient?.blood_group}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
