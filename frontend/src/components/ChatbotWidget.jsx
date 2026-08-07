import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Minimize2, Sparkles, Trash2 } from 'lucide-react';
import './DrMyra.css';
import { explainabilityAPI } from '../services/api-complete';

// Simple Markdown Parser for chat messages
const parseMarkdown = (text) => {
  if (!text) return '';
  
  // Split by lines to handle each line
  const lines = text.split('\n');
  let result = [];
  let inCodeBlock = false;
  let codeContent = [];
  
  lines.forEach((line, lineIndex) => {
    // Code block handling
    if (line.trim().startsWith('```')) {
      if (inCodeBlock) {
        result.push(
          <pre key={`code-${lineIndex}`} className="chat-code-block">
            <code>{codeContent.join('\n')}</code>
          </pre>
        );
        codeContent = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      return;
    }
    
    if (inCodeBlock) {
      codeContent.push(line);
      return;
    }
    
    // Process inline formatting
    let processedLine = line;
    const elements = [];
    let key = 0;
    
    // Headers
    if (line.startsWith('### ')) {
      elements.push(<h4 key={`h4-${lineIndex}`} className="chat-h4">{parseInlineMarkdown(line.slice(4))}</h4>);
    } else if (line.startsWith('## ')) {
      elements.push(<h3 key={`h3-${lineIndex}`} className="chat-h3">{parseInlineMarkdown(line.slice(3))}</h3>);
    } else if (line.startsWith('# ')) {
      elements.push(<h2 key={`h2-${lineIndex}`} className="chat-h2">{parseInlineMarkdown(line.slice(2))}</h2>);
    }
    // Bullet points
    else if (line.trim().startsWith('• ') || line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      const content = line.trim().slice(2);
      elements.push(
        <div key={`bullet-${lineIndex}`} className="chat-bullet">
          <span className="bullet-dot">•</span>
          <span>{parseInlineMarkdown(content)}</span>
        </div>
      );
    }
    // Numbered lists
    else if (/^\d+\.\s/.test(line.trim())) {
      const match = line.trim().match(/^(\d+)\.\s(.*)$/);
      if (match) {
        elements.push(
          <div key={`num-${lineIndex}`} className="chat-numbered">
            <span className="num-marker">{match[1]}.</span>
            <span>{parseInlineMarkdown(match[2])}</span>
          </div>
        );
      }
    }
    // Checkmarks
    else if (line.trim().startsWith('✅') || line.trim().startsWith('❌')) {
      elements.push(
        <div key={`check-${lineIndex}`} className="chat-check">
          {parseInlineMarkdown(line)}
        </div>
      );
    }
    // Regular paragraph
    else if (line.trim() !== '') {
      elements.push(
        <p key={`p-${lineIndex}`} className="chat-paragraph">
          {parseInlineMarkdown(line)}
        </p>
      );
    }
    // Empty line = spacing
    else {
      elements.push(<div key={`space-${lineIndex}`} className="chat-spacer" />);
    }
    
    result.push(...elements);
  });
  
  return result;
};

// Parse inline markdown (bold, italic, code, links)
const parseInlineMarkdown = (text) => {
  if (!text) return '';
  
  const parts = [];
  let remaining = text;
  let key = 0;
  
  while (remaining.length > 0) {
    // Bold: **text** or __text__
    const boldMatch = remaining.match(/^(.*?)\*\*(.+?)\*\*/);
    const boldMatch2 = remaining.match(/^(.*?)__(.+?)__/);
    
    // Inline code: `code`
    const codeMatch = remaining.match(/^(.*?)`([^`]+)`/);
    
    // Italic: *text* or _text_
    const italicMatch = remaining.match(/^(.*?)\*([^*]+)\*/);
    const italicMatch2 = remaining.match(/^(.*?)_([^_]+)_/);
    
    // Check which match comes first
    const matches = [
      { type: 'bold', match: boldMatch, length: boldMatch ? boldMatch[1].length : Infinity },
      { type: 'bold2', match: boldMatch2, length: boldMatch2 ? boldMatch2[1].length : Infinity },
      { type: 'code', match: codeMatch, length: codeMatch ? codeMatch[1].length : Infinity },
      { type: 'italic', match: italicMatch, length: italicMatch ? italicMatch[1].length : Infinity },
      { type: 'italic2', match: italicMatch2, length: italicMatch2 ? italicMatch2[1].length : Infinity },
    ].filter(m => m.match).sort((a, b) => a.length - b.length);
    
    if (matches.length > 0 && matches[0].match) {
      const first = matches[0];
      const match = first.match;
      
      // Add text before the match
      if (match[1]) {
        parts.push(<span key={key++}>{match[1]}</span>);
      }
      
      // Add the formatted text
      if (first.type === 'bold' || first.type === 'bold2') {
        parts.push(<strong key={key++} className="chat-bold">{match[2]}</strong>);
        remaining = remaining.slice(match[0].length);
      } else if (first.type === 'code') {
        parts.push(<code key={key++} className="chat-inline-code">{match[2]}</code>);
        remaining = remaining.slice(match[0].length);
      } else if (first.type === 'italic' || first.type === 'italic2') {
        parts.push(<em key={key++} className="chat-italic">{match[2]}</em>);
        remaining = remaining.slice(match[0].length);
      }
    } else {
      // No more matches, add remaining text
      parts.push(<span key={key++}>{remaining}</span>);
      break;
    }
  }
  
  return parts.length > 0 ? parts : text;
};

const SUGGESTION_CHIPS = [
  "What is SLE?",
  "How does SHAP work?",
  "Which model is best?",
  "What should I do first?",
  "Explain this platform",
];

const ChatbotWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [modelInfo, setModelInfo] = useState({ model: 'dr-myra-knowledge-base', device: 'cpu' });
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'dr-myra',
      text: "Hello. I'm Dr. Myra, your AI Clinical Assistant. How may I assist you with your autoimmune research today?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      modelInfo: null,
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [conversationHistory, setConversationHistory] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (overrideText) => {
    const userMessage = overrideText || inputValue;
    if (!userMessage.trim()) return;
    // Reset textarea height
    const textarea = document.querySelector('.chat-input');
    if (textarea) textarea.style.height = 'auto';
    const newMessage = {
      id: messages.length + 1,
      sender: 'user',
      text: userMessage,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages([...messages, newMessage]);
    setInputValue('');
    setIsTyping(true);

    // Add user message to conversation history
    const updatedHistory = [
      ...conversationHistory,
      { role: 'user', content: userMessage }
    ];

    try {
      // Call actual Dr. Myra backend API with optimized settings
      const response = await explainabilityAPI.chatWithDrMyra(
        userMessage,
        null, // context (can pass prediction/SHAP data if available)
        updatedHistory.slice(-6), // Keep last 3 exchanges for faster response
        0.3 // Lower temperature for faster, more focused responses
      );

      setIsTyping(false);
      
      const info = { model: response.model, device: response.device };
      setModelInfo(info);

      const aiResponse = {
        id: messages.length + 2,
        sender: 'dr-myra',
        text: response.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        modelInfo: info,
      };
      
      setMessages(prev => [...prev, aiResponse]);
      
      // Update conversation history
      setConversationHistory([
        ...updatedHistory,
        { role: 'assistant', content: response.response }
      ]);
    } catch (error) {
      console.error('Dr. Myra error:', error);
      setIsTyping(false);
      
      const errorMessage = {
        id: messages.length + 2,
        sender: 'dr-myra',
        text: "I apologize, but I'm having trouble connecting right now. Please try again in a moment.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        modelInfo: null,
      };
      
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    setMessages([{
      id: 1,
      sender: 'dr-myra',
      text: "Conversation cleared. How can I assist you?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      modelInfo: null,
    }]);
    setConversationHistory([]);
  };

  if (!isOpen) {
    return (
      <div className="dr-myra-dock" onClick={() => setIsOpen(true)}>
        <div className="orbital-ring"></div>
        <div className="dock-icon">
          <Sparkles className="icon-sparkle" size={24} />
        </div>
        <div className="dock-label">
          <div className="label-title">Dr. Myra</div>
          <div className="label-subtitle">AI Clinical Assistant</div>
        </div>
        <div className="status-pulse"></div>
      </div>
    );
  }

  return (
    <div className={`dr-myra-chat ${isMinimized ? 'minimized' : ''}`}>
      {/* Floating light reflection layer */}
      <div className="glass-reflection"></div>
      
      <div className="chat-header">
        <div className="header-info">
          <div className="assistant-avatar">
            <div className="avatar-glow"></div>
            <Sparkles size={18} />
          </div>
          <div className="header-text">
            <div className="assistant-name">Dr. Myra</div>
            <div className="assistant-status">
              <span className="status-indicator"></span>
              <span className="status-text">Online</span>
            </div>
          </div>
        </div>
        <div className="header-actions">
          <button
            className="header-btn"
            onClick={handleClearChat}
            title="Clear conversation"
          >
            <Trash2 size={15} />
          </button>
          <button 
            className="header-btn" 
            onClick={() => setIsMinimized(!isMinimized)}
            title={isMinimized ? "Expand" : "Minimize"}
          >
            <Minimize2 size={16} />
          </button>
          <button 
            className="header-btn" 
            onClick={() => setIsOpen(false)}
            title="Close"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          <div className="chat-body">
            {messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.sender}`}>
                {msg.sender === 'dr-myra' && (
                  <div className="message-avatar">
                    <Sparkles size={14} />
                  </div>
                )}
                <div className="message-content">
                  <div className="message-text">
                    {msg.sender === 'dr-myra' ? parseMarkdown(msg.text) : msg.text}
                  </div>
                  <div className="message-meta">
                    <span className="message-time">{msg.timestamp}</span>
                  </div>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="message dr-myra">
                <div className="message-avatar">
                  <Sparkles size={14} />
                </div>
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}

            {/* Suggestion chips — show only when conversation is fresh */}
            {messages.length <= 1 && !isTyping && (
              <div className="suggestion-chips">
                {SUGGESTION_CHIPS.map((chip) => (
                  <button
                    key={chip}
                    className="suggestion-chip"
                    onClick={() => handleSendMessage(chip)}
                  >
                    {chip}
                  </button>
                ))}
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-footer">
            <div className="input-container">
              <textarea
                className="chat-input"
                placeholder="Ask Dr. Myra about your data..."
                value={inputValue}
                onChange={(e) => {
                  setInputValue(e.target.value);
                  e.target.style.height = 'auto';
                  e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
                }}
                onKeyPress={handleKeyPress}
                rows={1}
              />
              <button
                className="send-btn"
                onClick={handleSendMessage}
                disabled={!inputValue.trim()}
              >
                <Send size={18} />
              </button>
            </div>
            <div className="chat-disclaimer">
              <p>
                Dr. Myra is an AI assistant for research purposes. Always consult qualified healthcare professionals for medical decisions.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ChatbotWidget;
