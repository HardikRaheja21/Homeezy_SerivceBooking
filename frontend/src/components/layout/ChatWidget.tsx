'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { apiClient } from '@/lib/api/client';

export function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([
    { role: 'assistant', content: 'Hi there! I am **Homeezy AI**. How can I help you with your home services today?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/ai/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${document.cookie.split('auth_token=')[1]?.split(';')[0] || ''}`
        },
        body: JSON.stringify({
          message: userMessage.content,
          history: messages.slice(1)
        })
      });

      if (!response.ok) throw new Error('Network response was not ok');
      if (!response.body) throw new Error('ReadableStream not supported');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;
            
            setMessages(prev => {
              const newMessages = [...prev];
              newMessages[newMessages.length - 1].content += data;
              return newMessages;
            });
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1].content = 'Sorry, I encountered an error connecting to the AI. Please try again.';
        return newMessages;
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <AnimatePresence>
        {!isOpen && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            className="fixed bottom-6 right-6 z-50"
          >
            <Button
              onClick={() => setIsOpen(true)}
              className="h-16 w-16 rounded-full shadow-2xl bg-slate-900 hover:bg-slate-800 p-0 border-4 border-white group transition-all duration-300 hover:shadow-[0_0_40px_-10px_rgba(15,23,42,0.5)]"
            >
              <Sparkles className="h-6 w-6 text-white group-hover:scale-110 transition-transform" />
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-6 right-6 z-50"
          >
            <Card className="w-[360px] sm:w-[400px] h-[600px] max-h-[85vh] shadow-2xl flex flex-col border-slate-200 overflow-hidden rounded-3xl">
              <CardHeader className="bg-slate-900 text-white py-4 px-6 flex flex-row justify-between items-center space-y-0">
                <div className="flex items-center gap-3">
                  <div className="bg-emerald-500/20 p-2 rounded-xl">
                    <Sparkles className="h-5 w-5 text-emerald-400" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">Homeezy AI</CardTitle>
                    <p className="text-xs text-slate-400 font-medium">Always online</p>
                  </div>
                </div>
                <Button variant="ghost" size="icon" className="text-slate-300 hover:text-white hover:bg-slate-800 rounded-full h-8 w-8" onClick={() => setIsOpen(false)}>
                  <X className="h-5 w-5" />
                </Button>
              </CardHeader>
              
              <CardContent className="flex-1 overflow-hidden p-0 bg-slate-50">
                <ScrollArea className="h-full w-full p-5" ref={scrollRef}>
                  <div className="flex flex-col space-y-6 pb-4">
                    {messages.map((msg, i) => (
                      <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        {msg.role === 'assistant' && (
                          <div className="h-8 w-8 rounded-full bg-slate-900 flex items-center justify-center mr-2 flex-shrink-0 mt-1">
                            <Sparkles className="h-4 w-4 text-emerald-400" />
                          </div>
                        )}
                        <div className={`max-w-[75%] rounded-2xl px-5 py-3 text-sm shadow-sm ${
                          msg.role === 'user' 
                            ? 'bg-emerald-600 text-white rounded-tr-sm' 
                            : 'bg-white text-slate-800 rounded-tl-sm border border-slate-100'
                        }`}>
                          {msg.role === 'assistant' ? (
                            <ReactMarkdown className="prose prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-slate-800 prose-pre:text-slate-100">
                              {msg.content}
                            </ReactMarkdown>
                          ) : (
                            msg.content
                          )}
                        </div>
                      </div>
                    ))}
                    {isLoading && messages[messages.length - 1].role === 'user' && (
                      <div className="flex justify-start items-center">
                        <div className="h-8 w-8 rounded-full bg-slate-900 flex items-center justify-center mr-2 flex-shrink-0">
                          <Sparkles className="h-4 w-4 text-emerald-400" />
                        </div>
                        <div className="bg-white rounded-2xl rounded-tl-sm px-5 py-4 border border-slate-100 shadow-sm flex gap-1">
                          <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                          <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                          <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
              
              <CardFooter className="p-4 bg-white border-t border-slate-100">
                <form 
                  className="flex w-full items-center gap-2 bg-slate-50 rounded-full pr-2 pl-4 py-2 border border-slate-200 focus-within:border-emerald-500 focus-within:ring-1 focus-within:ring-emerald-500 transition-all"
                  onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                >
                  <input
                    type="text"
                    placeholder="Ask anything..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    className="flex-1 bg-transparent border-none outline-none text-sm py-2"
                    disabled={isLoading}
                  />
                  <Button type="submit" size="icon" className="rounded-full bg-emerald-600 hover:bg-emerald-700 h-10 w-10 shrink-0 shadow-sm" disabled={isLoading || !input.trim()}>
                    <Send className="h-4 w-4 ml-0.5" />
                  </Button>
                </form>
              </CardFooter>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
