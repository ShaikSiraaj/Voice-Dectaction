import React, { useState, useEffect } from 'react';
import { UserCheck, UserPlus, Fingerprint, ShieldCheck } from 'lucide-react';

export function SpeakerManager() {
  const [speakers, setSpeakers] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [formData, setFormData] = useState({ id: '', name: '', role: '', department: '' });

  const fetchSpeakers = async () => {
    try {
      const res = await fetch('/api/speakers');
      const data = await res.json();
      setSpeakers(data);
    } catch (err) {
      console.error('Failed to fetch speakers:', err);
    }
  };

  useEffect(() => {
    fetchSpeakers();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/speakers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        setShowAddModal(false);
        setFormData({ id: '', name: '', role: '', department: '' });
        fetchSpeakers();
      }
    } catch (err) {
      console.error('Failed to enroll speaker:', err);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <Fingerprint className="h-5 w-5 text-sky-600" />
          <h2 className="text-base font-bold text-slate-900">
            Enrolled Voice Biometric Profiles (SASV Database)
          </h2>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-1"
        >
          <UserPlus className="h-3.5 w-3.5" /> Enroll Voice Profile
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {speakers.map((s) => (
          <div key={s.id} className="p-4 border border-slate-200 rounded-xl bg-slate-50 space-y-2">
            <div className="flex justify-between items-start">
              <div>
                <div className="font-bold text-xs text-slate-900">{s.name}</div>
                <div className="text-[11px] font-medium text-slate-500">{s.role} • {s.department}</div>
              </div>
              <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                <ShieldCheck className="h-3 w-3" /> Enrolled
              </span>
            </div>
            <div className="text-[10px] text-slate-400 font-mono">
              ID: {s.id} • Acoustic Profile: 16-Dim Centroid
            </div>
          </div>
        ))}
      </div>

      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full border border-slate-200 shadow-xl space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Enroll New Executive Voice Signature</h3>
            <form onSubmit={handleCreate} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Speaker ID</label>
                <input
                  type="text"
                  required
                  value={formData.id}
                  onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                  placeholder="spk_exec_02"
                  className="w-full border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Anita Desai"
                  className="w-full border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Role / Designation</label>
                <input
                  type="text"
                  required
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  placeholder="Chief Financial Officer"
                  className="w-full border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Department</label>
                <input
                  type="text"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  placeholder="Finance & Treasury"
                  className="w-full border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg font-bold"
                >
                  Save Profile
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
