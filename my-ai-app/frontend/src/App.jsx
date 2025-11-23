import { useState } from 'react'
import { Send, Bot, User, Loader2 } from 'lucide-react'

function App() {
	const [input, setInput] = useState('')
	const [messages, setMessages] = useState([])
	const [loading, setLoading] = useState(false)

	const sendMessage = async () => {
		if (!input.trim() || loading) return

		const userMsg = { 
			role: 'user', 
			content: [{ text: input }] 
		}

		setMessages(prev => [...prev, userMsg])
		setInput('')
		setLoading(true)

		try {
			const res = await fetch('/api/chat_stream', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ messages: [...messages, userMsg] })
			})
			const data = await res.json()
			
			setMessages(prev => [...prev, { 
				role: 'model', 
				content: [{ text: data.response }] 
			}])
		} catch (err) {
			console.error(err)
			setMessages(prev => [...prev, { 
				role: 'model', 
				content: [{ text: `Erreur: ${err.message}` }] 
			}])
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className="flex flex-col h-screen bg-slate-900 text-slate-100">
			{/* Header */}
			<header className="p-6 border-b border-slate-800 bg-slate-900/80 backdrop-blur flex items-center gap-3">
				<div className="w-10 h-10 bg-gradient-to-tr from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
					<Bot size={24} className="text-white" />
				</div>
				<div>
					<h1 className="font-bold text-xl">Gemini 2.0 Agent</h1>
					<p className="text-xs text-slate-500">Connected to MCP Core</p>
				</div>
			</header>

			{/* Messages */}
			<main className="flex-1 overflow-y-auto p-6 space-y-4">
				{messages.map((msg, idx) => (
					<div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
						{msg.role === 'model' && (
							<div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center shrink-0">
								<Bot size={16} />
							</div>
						)}
						
						<div className={`max-w-[75%] p-4 rounded-2xl ${
							msg.role === 'user'
								? 'bg-blue-600 text-white rounded-br-none'
								: 'bg-slate-800 border border-slate-700 rounded-bl-none'
						}`}>
							<p className="whitespace-pre-wrap leading-relaxed">{msg.content[0].text}</p>
						</div>

						{msg.role === 'user' && (
							<div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
								<User size={16} />
							</div>
						)}
					</div>
				))}

				{loading && (
					<div className="flex items-center gap-3">
						<div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center">
							<Bot size={16} />
						</div>
						<div className="bg-slate-800 p-4 rounded-2xl rounded-bl-none">
							<Loader2 size={16} className="animate-spin text-blue-400" />
						</div>
					</div>
				)}
			</main>

			{/* Input */}
			<div className="p-6 border-t border-slate-800 bg-slate-900/80 backdrop-blur">
				<div className="flex gap-3 items-end">
					<input
						type="text"
						value={input}
						onChange={(e) => setInput(e.target.value)}
						onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
						className="flex-1 bg-slate-800 border border-slate-700 rounded-xl py-3 px-4 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-500"
						placeholder="Posez une question..."
					/>
					<button
						onClick={sendMessage}
						disabled={!input.trim() || loading}
						className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed p-3 rounded-xl transition-colors"
					>
						<Send size={20} />
					</button>
				</div>
				<p className="text-center text-xs text-slate-600 mt-3">
					Powered by Gemini 2.0 • Render • MCP
				</p>
			</div>
		</div>
	)
}

export default App
