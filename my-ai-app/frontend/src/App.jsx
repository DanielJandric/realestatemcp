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
			content: input
		}

		const newMessages = [...messages, userMsg]
		setMessages(newMessages)
		setInput('')
		setLoading(true)

		try {
			const res = await fetch('/api/chat', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ message: input, history: messages })
			})
			const data = await res.json()
			
			setMessages([...newMessages, { 
				role: 'assistant', 
				content: data.response,
				tool: data.tool_used
			}])
		} catch (err) {
			console.error(err)
			setMessages([...newMessages, { 
				role: 'assistant', 
				content: `Erreur: ${err.message}`
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
				<div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
					<div className={`max-w-[80%] rounded-2xl p-4 ${
						msg.role === 'user'
							? 'bg-blue-600 text-white rounded-br-sm'
							: 'bg-slate-800 border border-slate-700 rounded-bl-sm shadow-xl'
					}`}>
						{msg.tool && (
							<div className="text-xs mb-2 flex items-center gap-1 text-purple-400 uppercase font-bold tracking-wider">
								<Server size={10} /> {msg.tool}
							</div>
						)}
						<p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
					</div>
				</div>
			))}

			{loading && (
				<div className="flex justify-start">
					<div className="bg-slate-800 p-4 rounded-2xl rounded-bl-sm animate-pulse">
						<div className="h-4 w-32 bg-slate-700 rounded"></div>
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
