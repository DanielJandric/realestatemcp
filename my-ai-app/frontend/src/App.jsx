import { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, Bot, User, Loader2, CheckCircle2, Terminal } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedImage, setSelectedImage] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  useEffect(scrollToBottom, [messages])

  // Conversion image en base64
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setSelectedImage(reader.result);
      reader.readAsDataURL(file);
    }
  }

  const sendMessage = async () => {
    if ((!input.trim() && !selectedImage) || isLoading) return;

    const userMsg = { 
      role: 'user', 
      content: [
        ...(input ? [{ text: input }] : []),
        ...(selectedImage ? [{ image_url: selectedImage }] : [])
      ] 
    };

    // On ajoute le message utilisateur
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setSelectedImage(null);
    setIsLoading(true);

    // On prépare le message assistant vide qui va se remplir
    setMessages(prev => [...prev, { role: 'model', content: [{ text: '' }], tools: [] }]);

    try {
      // On envoie tout l'historique + le nouveau message
      const historyPayload = [...messages, userMsg];
      
      const response = await fetch('/api/chat_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: historyPayload }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Garder le reste

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              setMessages(prev => {
                const newMsgs = [...prev];
                const lastMsg = newMsgs[newMsgs.length - 1];

                if (data.type === 'text_delta') {
                  // Ajout du texte fluide
                  lastMsg.content[0].text += data.content;
                } else if (data.type === 'tool_log') {
                  // Affichage outil
                  if (!lastMsg.tools) lastMsg.tools = [];
                  lastMsg.tools.push({ 
                    status: 'running', 
                    name: data.name, 
                    args: JSON.stringify(data.args) 
                  });
                } else if (data.type === 'tool_result') {
                  // Mise à jour résultat
                  const tool = lastMsg.tools.find(t => t.name === data.name && t.status === 'running');
                  if (tool) {
                    tool.status = 'done';
                    tool.result = data.result;
                  }
                }
                return newMsgs;
              });
            } catch (e) { 
              console.error("Parse error", e); 
            }
          }
        }
      }
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-screen bg-[#0f172a] text-slate-100 font-sans overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-slate-900/80 backdrop-blur border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-tr from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
            <Bot size={20} className="text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight">Gemini 2.0 Agent</h1>
            <p className="text-xs text-slate-400 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              Connected to MCP Core
            </p>
          </div>
        </div>
      </header>

      {/* Chat Container */}
      <main className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 opacity-50">
            <Terminal size={64} className="mb-4" />
            <p>Prêt à travailler.</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            
            {/* Avatar Assistant */}
            {msg.role === 'model' && (
              <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center shrink-0 border border-slate-700">
                <Bot size={16} />
              </div>
            )}

            <div className={`max-w-[85%] space-y-2`}>
              {/* Image Preview User */}
              {msg.content.find(c => c.image_url) && (
                <img 
                  src={msg.content.find(c => c.image_url).image_url} 
                  alt="Upload" 
                  className="max-h-48 rounded-lg border border-slate-700 mb-2"
                />
              )}

              {/* Tool Cards (Transparence) */}
              {msg.tools && msg.tools.length > 0 && (
                <div className="flex flex-col gap-2 mb-2">
                  {msg.tools.map((tool, tIdx) => (
                    <div key={tIdx} className="text-xs bg-slate-900/50 border border-slate-800 rounded p-2 flex items-center gap-2 font-mono text-blue-300">
                      {tool.status === 'running' ? <Loader2 size={12} className="animate-spin" /> : <CheckCircle2 size={12} className="text-green-500" />}
                      <span>Utilisation de <strong>{tool.name}</strong></span>
                    </div>
                  ))}
                </div>
              )}

              {/* Texte Message */}
              {msg.content[0].text && (
                <div className={`p-4 rounded-2xl shadow-sm leading-relaxed ${
                  msg.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-tr-sm' 
                  : 'bg-slate-800/80 border border-slate-700 text-slate-200 rounded-tl-sm'
                }`}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose prose-invert prose-sm max-w-none">
                    {msg.content[0].text}
                  </ReactMarkdown>
                </div>
              )}
            </div>

            {/* Avatar User */}
            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center shrink-0">
                <User size={16} />
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      <div className="p-4 bg-slate-900/90 backdrop-blur border-t border-slate-800">
        <div className="max-w-4xl mx-auto relative flex gap-2 items-end bg-slate-800/50 p-2 rounded-xl border border-slate-700 ring-offset-2 focus-within:ring-2 ring-blue-500/50 transition-all">
          
          {/* Image Upload Button */}
          <label className="p-3 hover:bg-slate-700 rounded-lg cursor-pointer transition-colors text-slate-400 hover:text-blue-400">
            <input type="file" accept="image/*" className="hidden" onChange={handleImageUpload} />
            <Paperclip size={20} />
          </label>

          {selectedImage && (
            <div className="relative mb-2">
              <img src={selectedImage} className="h-12 w-12 object-cover rounded border border-slate-600" />
              <button onClick={() => setSelectedImage(null)} className="absolute -top-2 -right-2 bg-red-500 rounded-full p-0.5 w-4 h-4 flex items-center justify-center text-[10px]">✕</button>
            </div>
          )}

          <textarea 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if(e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Posez une question ou uploadez une image..."
            className="w-full bg-transparent border-none focus:ring-0 resize-none max-h-32 py-3 text-slate-200 placeholder-slate-500 outline-none"
            rows="1"
          />
          
          <button 
            onClick={sendMessage}
            disabled={isLoading || (!input.trim() && !selectedImage)}
            className="p-3 bg-blue-600 hover:bg-500 disabled:opacity-50 disabled:hover:bg-blue-600 rounded-lg text-white transition-all"
          >
            {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
          </button>
        </div>

        <div className="text-center mt-2 text-[10px] text-slate-600">
          Powered by Gemini 2.0 • Render • MCP
        </div>
      </div>
    </div>
  )
}

export default App
