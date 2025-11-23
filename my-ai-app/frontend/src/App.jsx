import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles, Server, Cpu, Loader2, CheckCircle2, Code } from 'lucide-react'

function App() {
	const [input, setInput] = useState('')
	const [messages, setMessages] = useState([])
	const [loading, setLoading] = useState(false)
	const messagesEndRef = useRef(null)

	const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
	useEffect(scrollToBottom, [messages])

	const sendMessage = async () => {
		if (!input.trim() || loading) return

		const userMsg = { 
			role: 'user', 
			content: [{ text: input }] 
		}

		setMessages(prev => [...prev, userMsg])
		setInput('')
		setLoading(true)

		// Préparer le message assistant vide
		setMessages(prev => [...prev, { 
			role: 'model', 
			content: [{ text: '' }],
			tools: [],
			iterations: 0
		}])

		try {
			const res = await fetch('/api/chat', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ messages: [...messages, userMsg] })
			})

			const reader = res.body.getReader()
			const decoder = new TextDecoder()
			let buffer = ''

			while (true) {
				const { value, done } = await reader.read()
				if (done) break

				buffer += decoder.decode(value, { stream: true })
				const lines = buffer.split('\n')
				buffer = lines.pop() || ''

				for (const line of lines) {
					if (line.startsWith('data: ')) {
						try {
							const data = JSON.parse(line.slice(6))

							setMessages(prev => {
								const newMsgs = [...prev]
								const lastMsg = newMsgs[newMsgs.length - 1]

								if (data.type === 'iteration_start') {
									lastMsg.iterations = data.iteration
								} 
								else if (data.type === 'text_delta') {
									lastMsg.content[0].text += data.content
								} 
								else if (data.type === 'tools_start') {
									lastMsg.toolsCount = data.count
								} 
								else if (data.type === 'tool_call') {
									if (!lastMsg.tools) lastMsg.tools = []
									lastMsg.tools.push({
										name: data.name,
										args: data.args,
										status: 'running',
										preview: ''
									})
								} 
								else if (data.type === 'tool_result') {
									const tool = lastMsg.tools?.find(t => t.name === data.name && t.status === 'running')
									if (tool) {
										tool.status = 'done'
										tool.preview = data.preview
									}
								}
								else if (data.type === 'tools_end') {
									// Marqueur de fin d'exécution des outils
								}

								return newMsgs
							})
						} catch (e) {
							console.error('Parse error:', e)
						}
					}
				}
			}
		} catch (err) {
			console.error(err)
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className="flex flex-col h-screen bg-[#0f172a] text-slate-100 font-sans">
			{/* Header */}
			<header className="p-4 border-b border-slate-800 bg-slate-900/80 backdrop-blur flex justify-between items-center sticky top-0 z-10">
				<div className="flex items-center gap-3">
					<div className="w-10 h-10 bg-gradient-to-tr from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
						<Sparkles size={24} className="text-white" />
					</div>
					<div>
						<h1 className="font-bold text-lg">Gemini 2.5 + MCP</h1>
						<p className="text-xs text-slate-500">Swiss Real Estate Agent</p>
					</div>
				</div>
				<div className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full bg-green-900/30 text-green-400 border border-green-800">
					<span className="relative flex h-2 w-2">
						<span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
						<span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
					</span>
					Online
				</div>
			</header>

			{/* Messages */}
			<main className="flex-1 overflow-y-auto p-4 space-y-4">
				{messages.length === 0 && (
					<div className="h-full flex flex-col items-center justify-center text-slate-500">
						<Cpu size={64} className="mb-4 opacity-30" />
						<p className="text-sm">Analyse immobilière suisse • MCP Core</p>
					</div>
				)}

				{messages.map((msg, idx) => (
					<div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
						<div className={`max-w-[85%] space-y-2`}>
							
							{/* Iteration indicator */}
							{msg.iterations > 0 && (
								<div className="text-xs text-slate-600 flex items-center gap-1">
									<Code size={12} /> Iteration {msg.iterations}/10
								</div>
							)}

							{/* Tool execution cards */}
							{msg.tools && msg.tools.length > 0 && (
								<div className="space-y-1.5">
									{msg.tools.map((tool, tIdx) => (
										<div key={tIdx} className="text-xs bg-slate-900/60 border border-slate-800 rounded-lg p-3 font-mono">
											<div className="flex items-center gap-2 mb-1">
												{tool.status === 'running' ? (
													<Loader2 size={14} className="animate-spin text-blue-400" />
												) : (
													<CheckCircle2 size={14} className="text-green-500" />
												)}
												<span className="font-bold text-purple-400">{tool.name}</span>
											</div>
											{tool.args && Object.keys(tool.args).length > 0 && (
												<div className="text-slate-500 text-[10px] mt-1">
													Args: {JSON.stringify(tool.args)}
												</div>
											)}
											{tool.preview && tool.status === 'done' && (
												<div className="text-slate-600 text-[10px] mt-1 truncate">
													→ {tool.preview}
												</div>
											)}
										</div>
									))}
								</div>
							)}

							{/* Message text */}
							{msg.content[0].text && (
								<div className={`p-4 rounded-2xl leading-relaxed ${
									msg.role === 'user'
										? 'bg-blue-600 text-white rounded-br-sm shadow-lg'
										: 'bg-slate-800/80 border border-slate-700 text-slate-200 rounded-bl-sm shadow-xl'
								}`}>
									<p className="whitespace-pre-wrap">{msg.content[0].text}</p>
								</div>
							)}
						</div>
					</div>
				))}

				{loading && (
					<div className="flex justify-start">
						<div className="bg-slate-800 p-4 rounded-2xl rounded-bl-sm border border-slate-700">
							<Loader2 size={20} className="animate-spin text-blue-400" />
						</div>
					</div>
				)}

				<div ref={messagesEndRef} />
			</main>

			{/* Input */}
			<div className="p-4 border-t border-slate-800 bg-slate-900/90 backdrop-blur">
				<div className="flex gap-3">
					<input
						type="text"
						value={input}
						onChange={(e) => setInput(e.target.value)}
						onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
						className="flex-1 bg-slate-800/80 border border-slate-700 rounded-xl py-3 px-4 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 backdrop-blur placeholder-slate-500"
						placeholder="Ex: État locatif net hors vacances du total du parc"
						disabled={loading}
					/>
					<button
						onClick={sendMessage}
						disabled={!input.trim() || loading}
						className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed p-3 rounded-xl transition-colors flex items-center gap-2"
					>
						{loading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
					</button>
				</div>
				<p className="text-center text-[10px] text-slate-600 mt-2">
					Gemini 2.5 Flash • PostgreSQL • MCP Core
				</p>
			</div>
		</div>
	)
}

export default App
