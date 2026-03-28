import { useState, useEffect, useRef } from 'react'
import './index.css'

function App() {
  const [gameState, setGameState] = useState(null)
  const [simulateMode, setSimulateMode] = useState(false)
  const [logs, setLogs] = useState([])
  const [error, setError] = useState(null)
  const [isAiComputing, setIsAiComputing] = useState(false)
  const logEndRef = useRef(null)

  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'

  const scrollToBottom = () => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [logs])

  const addLog = (msg) => {
    setLogs(prev => [...prev, msg])
  }

  const startGame = async () => {
    try {
      const res = await fetch(`${API_URL}/start`, { method: 'POST' })
      const data = await res.json()
      setGameState(data)
      setLogs(['Game Started!'])
      setError(null)
    } catch (e) {
      setError('Failed to connect to backend server. Ensure it is running.')
    }
  }

  const checkAiTurn = async (currentState) => {
    if (!currentState || currentState.is_terminal) return

    const turn = currentState.current_turn
    if (turn === 0 || turn === 1 || (turn === 2 && simulateMode)) {
      setIsAiComputing(true)
      
      setTimeout(async () => {
        try {
          const res = await fetch(`${API_URL}/ai_turn?simulate_mode=${simulateMode}`, { method: 'POST' })
          const data = await res.json()
          
          if (data.state) {
            setGameState(data.state)
            const pName = turn === 0 ? "Player 1 (Minimax)" : turn === 1 ? "Player 2 (Expectimax)" : "Player 3 (Simulation)"
            let moveDesc = typeof data.action_taken === 'string' ? "Drew a card" : `Played ${data.action_taken.color} ${data.action_taken.value}`
            
            addLog(`\n--- ${pName} Turn ---`)
            addLog(`Action: ${moveDesc}`)
            if(data.scores && data.scores.length > 0) {
              data.scores.forEach(s => {
                  let act = typeof s.action === 'string' ? 'Draw' : `${s.action.color} ${s.action.value}`
                  addLog(`Eval ${act}: ${s.score.toFixed(1)}`)
              })
            }
          }
        } catch (e) {
             setError('Failed AI turn. Backend might be down.')
        } finally {
             setIsAiComputing(false)
        }
      }, 1000)
    }
  }

  useEffect(() => {
    if (gameState && !gameState.is_terminal) {
        checkAiTurn(gameState)
    }
  }, [gameState?.current_turn, simulateMode])

  const playCard = async (index) => {
    if (gameState.current_turn !== 2 || simulateMode) return

    try {
      const res = await fetch(`${API_URL}/play`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_index: index })
      })
      if(!res.ok) {
          const e = await res.json()
          setError(e.detail)
          return
      }
      const data = await res.json()
      const c = gameState.player_hands[2][index]
      setGameState(data.state)
      setError(null)
      addLog(`\n--- You Played --- `)
      addLog(`Action: Played ${c.color} ${c.value}`)
    } catch (e) {
      setError('Network error')
    }
  }

  const drawCard = async () => {
    if (gameState.current_turn !== 2 || simulateMode) return

    // If there is a valid play, drawing shouldn't be allowed as per simple rules, but backend catches mostly. 
    try {
      const res = await fetch(`${API_URL}/play?draw=true`, { method: 'POST' })
      const data = await res.json()
      setGameState(data.state)
      setError(null)
      addLog(`\n--- You Played ---`)
      addLog(`Action: Drew a card`)
    } catch (e) {
       setError('Network error')
    }
  }

  if (!gameState) {
    return (
      <div className="glass-panel" style={{textAlign: 'center', marginTop: '15vh'}}>
        <h1 style={{fontSize: '3rem', marginBottom: '1rem', color: 'var(--primary)', letterSpacing: '1px'}}>UNO AI Battle</h1>
        <p style={{marginBottom: '2rem', fontSize: '1.2rem', color: 'var(--text-secondary)'}}>Watch Minimax and Expectimax AI battle it out, or join in yourself!</p>
        <button className="btn btn-primary" onClick={startGame}>Start Game Engine</button>
        {error && <p style={{color: '#ef4444', marginTop: '1rem'}}>{error}</p>}
      </div>
    )
  }

  const renderCard = (card, i, onClick, highlightValid = false, spectator = false) => {
    let isValid = true
    if (highlightValid && gameState.current_turn === 2 && !simulateMode) {
      isValid = card.color === gameState.top_card.color || card.value === gameState.top_card.value
    }

    const clickable = !spectator && onClick

    return (
      <div
        key={i}
        className={`uno-card ${card.color} ${!isValid ? 'disabled' : ''} ${spectator ? 'uno-card--spectator' : ''} animate-draw`}
        data-value={card.value}
        onClick={() => clickable && isValid && onClick(i)}
        role={clickable ? 'button' : undefined}
      >
        {card.value}
      </div>
    )
  }

  return (
    <div className={`game-board glass-panel ${simulateMode ? 'game-board--simulate' : ''}`}>
      <div className="header">
        <h2 style={{margin: '0', fontSize: '2rem', color: 'white', letterSpacing: '2px'}}>UNO ADVERSARIAL</h2>
        <div className="toggle-container">
           <button className={`btn btn-secondary ${!simulateMode ? 'active' : ''}`} onClick={() => setSimulateMode(false)}>Manual Play</button>
           <button className={`btn btn-secondary ${simulateMode ? 'active' : ''}`} onClick={() => setSimulateMode(true)}>Simulation Mode</button>
        </div>
        <button className="btn btn-secondary" style={{padding: '5px 15px', fontSize: '0.9rem'}} onClick={startGame}>Restart Game</button>
        {error && <div style={{color: '#ef4444', padding: '10px'}}>{error}</div>}
      </div>

      <div className="player-left">
         <div className={`stat-box ${gameState.current_turn === 1 ? 'active-turn' : ''}`}>
             <h3 style={{margin: '0 0 5px', color:'white'}}>P2 (Expectimax - Offensive)</h3>
             <p style={{margin: 0}}>{gameState.player_hands[1].length} cards left</p>
         </div>
         <div className={`opponent-hand ${simulateMode ? 'opponent-hand--revealed' : ''}`}>
             {simulateMode
               ? gameState.player_hands[1].map((card, i) => renderCard(card, `p2-${i}`, null, false, true))
               : gameState.player_hands[1].map((_, i) => <div key={i} className="mini-card animate-draw"></div>)}
         </div>
      </div>

      <div className="center-area">
         <div className="pile">
             <div className="deck" onClick={drawCard} title="Click to Draw">
                 UNO<br/>{gameState.deck_count}
             </div>
             {renderCard(gameState.top_card, 'top')}
         </div>
         <div className="log-container">
             {logs.map((l, i) => <div key={i} dangerouslySetInnerHTML={{__html: l.replace(/\n/g, "<br/>")}} />)}
             {isAiComputing && <div style={{color: 'var(--primary)', marginTop: '10px', fontStyle: 'italic'}}>AI is computing optimal move...</div>}
             <div ref={logEndRef} />
         </div>
      </div>

      <div className="player-right">
         <div className={`stat-box ${gameState.current_turn === 0 ? 'active-turn' : ''}`}>
             <h3 style={{margin: '0 0 5px', color:'white'}}>P1 (Minimax - Defensive)</h3>
             <p style={{margin: 0}}>{gameState.player_hands[0].length} cards left</p>
         </div>
         <div className={`opponent-hand ${simulateMode ? 'opponent-hand--revealed' : ''}`}>
             {simulateMode
               ? gameState.player_hands[0].map((card, i) => renderCard(card, `p1-${i}`, null, false, true))
               : gameState.player_hands[0].map((_, i) => <div key={i} className="mini-card animate-draw"></div>)}
         </div>
      </div>

      <div className="player-bottom">
         <div className={`stat-box ${gameState.current_turn === 2 ? 'active-turn' : ''}`} style={{maxWidth: '400px'}}>
             <h3 style={{margin: '0', color:'white'}}>P3 ({simulateMode ? "Minimax Simulated" : "You"})</h3>
             {gameState.winner !== -1 && <h2 style={{color: '#10b981', margin:'10px 0'}}>Game Over! Winner: Player {gameState.winner + 1}</h2>}
         </div>
         
         <div className="hand-container">
             {gameState.player_hands[2].map((card, i) => 
                renderCard(card, i, () => playCard(i), true)
             )}
         </div>
      </div>
    </div>
  )
}

export default App
