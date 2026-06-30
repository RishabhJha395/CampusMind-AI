import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Send, ArrowLeft, Bot, User, Loader2, Sparkles, ExternalLink } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { apiClient } from '../api/client';

export default function ChatPage() {
  const { universityId } = useParams();
  const navigate = useNavigate();
  const [university, setUniversity] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    async function init() {
      try {
        const data = await apiClient.getUniversities();
        const unis = data.universities || [];
        const uni = unis.find(u => u.university_id === universityId);
        if (uni) {
          setUniversity(uni);
          setMessages([{
            role: 'assistant',
            content: uni.welcome_message || `Hello! I am the CampusMind AI assistant for ${uni.university_name}. How can I help you today?`
          }]);
        } else {
          navigate('/');
        }
      } catch (err) {
        console.error(err);
        navigate('/');
      }
    }
    init();
  }, [universityId, navigate]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Add empty assistant message that will be populated via stream
    setMessages(prev => [...prev, { role: 'assistant', content: '', sources: [] }]);

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage.content,
          university_id: universityId,
          stream: true
        })
      });

      if (!response.ok) throw new Error('Failed to get response');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        
        // Keep the last part in buffer as it might be incomplete
        buffer = lines.pop() || "";
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (dataStr === '[DONE]') {
               setIsLoading(false);
               continue;
            }
            try {
              const data = JSON.parse(dataStr);
              if (data.type === 'sources') {
                 setMessages(prev => {
                    const newMessages = [...prev];
                    newMessages[newMessages.length - 1].sources = data.data;
                    return newMessages;
                 });
              } else if (data.type === 'chunk') {
                 setMessages(prev => {
                    const newMessages = [...prev];
                    newMessages[newMessages.length - 1].content += data.content;
                    return newMessages;
                 });
              }
            } catch (err) {
              console.error("Parse error on chunk: ", dataStr, err);
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = { 
          role: 'assistant', 
          content: "I'm sorry, I encountered an error while trying to answer your question. Please try again.",
          isError: true
        };
        return newMessages;
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!university) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-slate-50 dark:bg-slate-900 overflow-hidden relative">
      
      {/* Dynamic Background Elements */}
      <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-b from-primary/10 to-transparent pointer-events-none" />

      {/* Header */}
      <header className="flex-none bg-white/70 dark:bg-slate-800/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-700 z-10 px-6 py-4 shadow-sm">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => navigate('/')}
              className="p-2 -ml-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-slate-500"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center space-x-3">
              {university.logo_url ? (
                <img src={university.logo_url} alt="logo" className="w-10 h-10 object-contain rounded-lg bg-white p-1 shadow-sm" />
              ) : (
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-primary" />
                </div>
              )}
              <div>
                <h2 className="font-bold text-slate-900 dark:text-white text-lg tracking-tight leading-none mb-1">
                  {university.university_name} AI
                </h2>
                <div className="flex items-center space-x-2">
                  <span className="flex w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                  <p className="text-xs text-slate-500 font-medium">Online</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto px-4 py-8 custom-scrollbar">
        <div className="max-w-4xl mx-auto space-y-8">
          {messages.map((msg, idx) => (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              key={idx}
              className={`flex items-end space-x-3 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm ${
                msg.role === 'user' 
                  ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white' 
                  : 'bg-white border border-slate-200 dark:bg-slate-800 dark:border-slate-700 text-primary'
              }`}>
                {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>
              
              <div className="flex flex-col max-w-[85%] sm:max-w-[75%] space-y-2">
                <div className={`px-5 py-4 rounded-2xl shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-primary text-white rounded-br-sm'
                    : msg.isError 
                      ? 'bg-red-50 text-red-700 rounded-bl-sm border border-red-100' 
                      : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-bl-sm border border-slate-100 dark:border-slate-700'
                }`}>
                  <div className={`prose prose-sm max-w-none ${msg.role === 'user' ? 'text-white prose-invert' : 'dark:prose-invert'}`}>
                    {msg.role === 'user' ? (
                      <p className="whitespace-pre-wrap m-0 leading-relaxed">{msg.content}</p>
                    ) : (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    )}
                  </div>
                </div>

                {/* Sources Pill */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {msg.sources.map((source, sIdx) => (
                      <a 
                        key={sIdx}
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center space-x-1 px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-full text-xs text-slate-500 hover:text-primary hover:border-primary/50 transition-colors shadow-sm cursor-pointer"
                        title={source.title}
                      >
                        <ExternalLink className="w-3 h-3" />
                        <span className="max-w-[150px] truncate font-medium">
                          {source.title || 'Source'}
                        </span>
                      </a>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}

          {isLoading && !messages[messages.length-1]?.content && !messages[messages.length-1]?.sources?.length && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-end space-x-3"
            >
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-white border border-slate-200 dark:bg-slate-800 dark:border-slate-700 flex items-center justify-center shadow-sm">
                <Bot className="w-4 h-4 text-primary" />
              </div>
              <div className="bg-white dark:bg-slate-800 px-5 py-4 rounded-2xl rounded-bl-sm border border-slate-100 dark:border-slate-700 shadow-sm flex space-x-2">
                <div className="w-2 h-2 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 rounded-full bg-primary/80 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <footer className="flex-none bg-white/70 dark:bg-slate-800/80 backdrop-blur-md border-t border-slate-200 dark:border-slate-700 p-4">
        <div className="max-w-4xl mx-auto">
          <form 
            onSubmit={handleSubmit}
            className="relative flex items-center bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary transition-all duration-300"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Ask about ${university.university_name}...`}
              disabled={isLoading}
              className="w-full bg-transparent px-6 py-4 outline-none text-slate-800 dark:text-white placeholder-slate-400"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 p-2.5 rounded-xl bg-primary text-white hover:bg-primary/90 disabled:bg-slate-100 disabled:text-slate-400 dark:disabled:bg-slate-800 transition-colors shadow-sm"
            >
              {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
          </form>
          <div className="text-center mt-3">
            <p className="text-[11px] text-slate-400 font-medium">
              CampusMind AI can make mistakes. Consider verifying important information from official sources.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
