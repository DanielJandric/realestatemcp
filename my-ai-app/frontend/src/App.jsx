import { useState } from 'react'
import { Send, Sparkles, Server, Cpu } from 'lucide-react'

function App() {
	const [input, setInput] = useState('')
	const [messages, setMessages] = useState([])
	const [loading, setLoading] = useState(false)

	const sendMessage = async () => {
		if (!input.trim()) return
		const newMsgs = [...messages, { role: 'user', content: input }]
		setMessages(newMsgs)
		setInput('')
		setLoading(true)
		try {
			const res = await fetch('/api/chat', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ message: input, history: messages })
			})
			const data = await res.json()
			setMessages([...newMsgs, { role: 'assistant', content: data.response, tool: data.tool_used }])
		} catch (err) {
			console.error(err)
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col items-center font-sans">
			<header className="w-full p-6 border-b border-slate-800 bg-slate-900/50 backdrop-blur flex justify-between items-center sticky top-0 z-10">
				<div className="flex items-center gap-2">
					<Sparkles className="text-blue-400" />
					<h1 className="font-bold text-xl tracking-tight">
						Gemini 3.0 <span className="text-slate-500 font-normal">+ MCP Core</span>
					</h1>
				</div>
				<div className="text-xs px-3 py-1 rounded-full bg-green-900/30 text-green-400 border border-green-800 flex items-center gap-2">
					<span className="relative flex h-2 w-2">
						<span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
						<span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
					</span>
					System Online
				</div>
			</header>

			<main className="flex-1 w-full max-w-3xl p-4 flex flex-col gap-6 overflow-y-auto pb-32">
				{messages.length === 0 && (
					<div className="flex flex-col items-center justify-center h-full text-slate-500 mt-20">
						<Cpu size={48} className="mb-4 opacity-50" />
						<p>Connecté au serveur MCP. Posez une question.</p>
					</div>
				)}

				{messages.map((m, i) => (
					<div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
						<div className={`max-w-[80%] rounded-2xl p-4 ${
							m.role === 'user'
								? 'bg-blue-600 text-white rounded-br-sm'
								: 'bg-slate-800 border border-slate-700 rounded-bl-sm shadow-xl'
						}`}>
							{m.tool && (
								<div className="text-xs mb-2 flex items-center gap-1 text-purple-400 uppercase font-bold tracking-wider">
									<Server size={10} /> Utilisation de {m.tool}
								</div>
							)}
							<p className="leading-relaxed whitespace-pre-wrap">{m.content}</p>
						</div>
					</div>
				))}

				{loading && (
					<div className="flex justify-start animate-pulse">
						<div className="bg-slate-800 h-10 w-24 rounded-full"></div>
					</div>
				)}
			</main>

			<div className="fixed bottom-0 w-full bg-gradient-to-t from-slate-900 to-transparent p-6 flex justify-center">
				<div className="w-full max-w-3xl relative">
					<input
						type="text"
						value={input}
						onChange={(e) => setInput(e.target.value)}
						onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
						className="w-full bg-slate-800/80 border border-slate-700 rounded-full py-4 pl-6 pr-14 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 backdrop-blur shadow-2xl transition-all"
						placeholder="Interroger le système..."
					/>
					<button
						onClick={sendMessage}
						className="absolute right-2 top-2 bg-blue-600 hover:bg-blue-500 p-2 rounded-full transition-colors"
					>
						<Send size={20} />
					</button>
				</div>
			</div>
		</div>
	)
}

export default App


