import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { GraduationCap, ArrowRight, BookOpen, Loader2 } from 'lucide-react';
import { apiClient } from '../api/client';

export default function UniversitySelectionPage() {
  const [universities, setUniversities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    async function fetchUniversities() {
      try {
        const data = await apiClient.getUniversities();
        setUniversities(data.universities || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchUniversities();
  }, []);

  return (
    <div className="min-h-screen bg-[linear-gradient(135deg,#F8FBFF_0%,#EEF5FF_50%,#F7FAFF_100%)] flex flex-col items-center py-20 px-4 relative overflow-hidden font-['Inter']">
      
      {/* Abstract Background Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] bg-[#EAF2FF] rounded-full mix-blend-multiply filter blur-[120px] opacity-40 animate-blob"></div>
      <div className="absolute top-[20%] right-[-10%] w-[500px] h-[500px] bg-[#EAF2FF] rounded-full mix-blend-multiply filter blur-[100px] opacity-30 animate-blob animation-delay-2000"></div>
      <div className="absolute bottom-[-20%] left-[20%] w-[700px] h-[700px] bg-[#EAF2FF] rounded-full mix-blend-multiply filter blur-[150px] opacity-40 animate-blob animation-delay-4000"></div>

      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="text-center z-10 max-w-2xl mx-auto mb-16"
      >
        <div className="inline-flex items-center justify-center p-3 bg-[rgba(255,255,255,0.75)] rounded-2xl shadow-[0_5px_15px_rgba(0,0,0,0.04)] backdrop-blur-[20px] mb-6 border border-[rgba(70,120,255,0.08)]">
          <BookOpen className="w-8 h-8 text-[#3B82F6]" />
        </div>
        <h1 className="text-5xl md:text-6xl font-[700] tracking-tight text-[#0F172A] mb-6">
          Welcome to <br className="hidden md:block" />
          <span className="text-transparent bg-clip-text bg-[linear-gradient(135deg,#3B82F6,#06B6D4)]">CampusMind AI</span>
        </h1>
        <p className="text-lg md:text-xl text-[#475569] leading-relaxed">
          Your intelligent campus assistant. Select your university below to access instantly searchable, verified institutional knowledge.
        </p>
      </motion.div>

      <div className="w-full max-w-6xl z-10">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
            <p className="text-slate-500 font-medium">Loading universities...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-6 rounded-2xl border border-red-100 dark:border-red-800 text-center max-w-lg mx-auto shadow-sm">
            <p className="font-semibold text-lg mb-2">Connection Error</p>
            <p>{error}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {universities.map((uni, index) => (
              <motion.div
                key={uni.university_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, ease: "easeOut", delay: index * 0.1 }}
                whileHover={{ y: -4 }}
                onClick={() => navigate(`/chat/${uni.university_id}`)}
                className="group relative cursor-pointer"
              >
                <div className="relative h-full bg-[rgba(255,255,255,0.75)] backdrop-blur-[20px] border border-[rgba(70,120,255,0.08)] p-8 rounded-[24px] shadow-[0_15px_40px_rgba(30,80,180,0.08)] transition-all duration-250 ease-out overflow-hidden">
                  
                  {/* Decorative corner accent using university primary color */}
                  <div 
                    className="absolute -top-12 -right-12 w-24 h-24 rounded-full opacity-10 blur-xl transition-all duration-500 group-hover:scale-150 group-hover:opacity-20"
                    style={{ backgroundColor: uni.primary_color || '#3B82F6' }}
                  />

                  <div className="flex items-start justify-between mb-8">
                    <div 
                      className="w-16 h-16 rounded-2xl flex items-center justify-center border border-[rgba(70,120,255,0.08)] bg-white overflow-hidden shadow-[0_4px_15px_rgba(15,23,42,0.05)]"
                    >
                      {uni.logo_url ? (
                        <img src={uni.logo_url} alt={uni.university_name} className="w-10 h-10 object-contain" />
                      ) : (
                        <GraduationCap className="w-8 h-8 text-[#94A3B8]" />
                      )}
                    </div>
                    <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center transition-all duration-250 ease-out shadow-[0_4px_15px_rgba(15,23,42,0.05)] border border-[#E5EDF9] group-hover:border-[#3B82F6]">
                      <ArrowRight className="w-5 h-5 text-[#94A3B8] group-hover:text-[#3B82F6] transition-all duration-250 ease-out group-hover:translate-x-1" />
                    </div>
                  </div>

                  <h3 className="text-2xl font-[600] text-[#0F172A] mb-3 tracking-tight">
                    {uni.university_name}
                  </h3>
                  
                  {uni.welcome_message && (
                    <p className="text-[#64748B] text-sm line-clamp-3 leading-relaxed font-[400]">
                      {uni.welcome_message}
                    </p>
                  )}
                  
                  <div className="mt-8 flex items-center space-x-2">
                    <span 
                      className="inline-flex items-center px-4 py-2 rounded-full text-sm font-[500] bg-[#3B82F6] text-white transition-all duration-250 ease-out group-hover:bg-[#2563EB] shadow-[0_8px_20px_rgba(59,130,246,0.25)] group-hover:scale-[1.02]"
                    >
                      Enter Campus
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
