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
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800 flex flex-col items-center py-20 px-4 relative overflow-hidden">
      
      {/* Abstract Background Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-primary/20 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob"></div>
      <div className="absolute top-[20%] right-[-10%] w-96 h-96 bg-purple-300/30 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob animation-delay-2000"></div>
      <div className="absolute bottom-[-20%] left-[20%] w-96 h-96 bg-pink-300/20 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob animation-delay-4000"></div>

      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="text-center z-10 max-w-2xl mx-auto mb-16"
      >
        <div className="inline-flex items-center justify-center p-3 bg-white/50 dark:bg-white/10 rounded-2xl shadow-sm backdrop-blur-md mb-6 border border-white/20">
          <BookOpen className="w-8 h-8 text-primary" />
        </div>
        <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white mb-6">
          Welcome to <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-purple-600">CampusMind AI</span>
        </h1>
        <p className="text-lg md:text-xl text-slate-600 dark:text-slate-300 leading-relaxed">
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
                transition={{ duration: 0.5, delay: index * 0.1 }}
                whileHover={{ y: -8, scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => navigate(`/chat/${uni.university_id}`)}
                className="group relative cursor-pointer"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-purple-600/5 rounded-3xl transform transition-transform duration-300 group-hover:scale-105" />
                
                <div className="relative h-full bg-white/70 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200/50 dark:border-slate-700/50 p-8 rounded-3xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden">
                  
                  {/* Decorative corner accent using university primary color */}
                  <div 
                    className="absolute -top-12 -right-12 w-24 h-24 rounded-full opacity-20 blur-xl transition-all duration-500 group-hover:scale-150 group-hover:opacity-40"
                    style={{ backgroundColor: uni.primary_color || '#3b82f6' }}
                  />

                  <div className="flex items-start justify-between mb-8">
                    <div 
                      className="w-16 h-16 rounded-2xl flex items-center justify-center shadow-sm border border-slate-100 dark:border-slate-700 bg-white dark:bg-slate-900 overflow-hidden"
                    >
                      {uni.logo_url ? (
                        <img src={uni.logo_url} alt={uni.university_name} className="w-10 h-10 object-contain" />
                      ) : (
                        <GraduationCap className="w-8 h-8 text-slate-400" />
                      )}
                    </div>
                    <div className="w-10 h-10 rounded-full bg-slate-50 dark:bg-slate-800 flex items-center justify-center group-hover:bg-primary group-hover:text-white transition-colors duration-300 shadow-sm border border-slate-100 dark:border-slate-700">
                      <ArrowRight className="w-5 h-5 text-slate-400 group-hover:text-white transition-colors" />
                    </div>
                  </div>

                  <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-3 tracking-tight">
                    {uni.university_name}
                  </h3>
                  
                  {uni.welcome_message && (
                    <p className="text-slate-500 dark:text-slate-400 text-sm line-clamp-3 leading-relaxed">
                      {uni.welcome_message}
                    </p>
                  )}
                  
                  <div className="mt-8 flex items-center space-x-2">
                    <span 
                      className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold"
                      style={{ 
                        backgroundColor: `${uni.primary_color || '#3b82f6'}15`,
                        color: uni.primary_color || '#3b82f6'
                      }}
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
