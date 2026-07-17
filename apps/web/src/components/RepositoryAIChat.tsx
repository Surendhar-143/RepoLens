import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Send, 
  Trash2, 
  Sparkles, 
  Plus, 
  ArrowRight,
  ShieldCheck
} from 'lucide-react';
import { api } from '../services/api.ts';
import { Button } from './ui/Button.tsx';
import { Card, CardFooter } from './ui/Card.tsx';

interface RepositoryAIChatProps {
  repositoryId: string;
  onSelectFile: (fileId: string) => void;
}

export const RepositoryAIChat: React.FC<RepositoryAIChatProps> = ({
  repositoryId,
  onSelectFile
}) => {
  const queryClient = useQueryClient();
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [inputMessage, setInputMessage] = useState('');
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  // Suggested prompts widgets
  const suggestedQuestions = [
    "Explain project architecture.",
    "Where is authentication implemented?",
    "List all database models and schemas.",
    "Describe the request lifecycle flows."
  ];

  // Load Conversations History
  const { data: conversations = [], refetch: refetchConversations } = useQuery({
    queryKey: ['ai-conversations', repositoryId],
    queryFn: async () => {
      const response = await api.get(`/ai/conversations?repository_id=${repositoryId}`);
      return response.data;
    }
  });

  // Load Active Conversation Messages
  const { data: messages = [], refetch: refetchMessages } = useQuery({
    queryKey: ['ai-messages', activeConvId],
    queryFn: async () => {
      if (!activeConvId) return [];
      const response = await api.get(`/ai/conversations/${activeConvId}`);
      return response.data;
    },
    enabled: !!activeConvId
  });

  // Delete Conversation session
  const deleteConv = useMutation({
    mutationFn: async (convId: string) => {
      await api.delete(`/ai/conversations/${convId}`);
    },
    onSuccess: () => {
      if (activeConvId) setActiveConvId(null);
      refetchConversations();
    }
  });

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isGenerating) return;
    
    setInputMessage('');
    setStreamingMessage('');
    setIsGenerating(true);

    // Temp message array update
    const userMsg = { role: 'user', content: text, citations: [] };
    queryClient.setQueryData(['ai-messages', activeConvId], (old: any) => [...(old || []), userMsg]);

    try {
      const token = localStorage.getItem('repolens_access_token');
      const response = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          repository_id: repositoryId,
          conversation_id: activeConvId,
          message: text
        })
      });

      if (!response.body) throw new Error("Null completion body stream.");
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      let accumulatedResponse = '';
      let finalConvId = activeConvId;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const rawText = decoder.decode(value);
        const lines = rawText.split('\n');

        for (const line of lines) {
          const cleanLine = line.trim();
          if (!cleanLine || !cleanLine.startsWith('data: ')) continue;
          if (cleanLine === 'data: [DONE]') break;

          try {
            const payload = JSON.parse(cleanLine.substring(6));
            if (payload.token) {
              accumulatedResponse += payload.token;
              setStreamingMessage(accumulatedResponse);
            }

            if (payload.conversation_id) {
              finalConvId = payload.conversation_id;
            }
          } catch (err) {
            continue;
          }
        }
      }

      // Sync active conversation
      if (!activeConvId && finalConvId) {
        setActiveConvId(finalConvId);
        refetchConversations();
      } else {
        refetchMessages();
      }

    } catch (e: any) {
      console.error(e);
    } finally {
      setIsGenerating(false);
      setStreamingMessage('');
    }
  };

  const startNewConversation = () => {
    setActiveConvId(null);
    setStreamingMessage('');
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[550px] items-stretch">
      
      {/* Sidebar Conversation list */}
      <Card className="lg:col-span-1 bg-card/15 p-4 flex flex-col justify-between overflow-y-auto border-border/40 select-none">
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Conversations</h3>
            <Button variant="outline" size="icon" className="w-7 h-7" onClick={startNewConversation}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-1.5 text-xs">
            {conversations.map((c: any) => (
              <div 
                key={c.id} 
                className={`group flex items-center justify-between p-2.5 rounded-lg cursor-pointer transition-all ${
                  activeConvId === c.id ? 'bg-[#a21caf]/15 text-[#f5d0fe]' : 'text-zinc-300 hover:bg-secondary/40'
                }`}
                onClick={() => setActiveConvId(c.id)}
              >
                <span className="truncate max-w-[80%] font-semibold">{c.title}</span>
                <button 
                  onClick={(e) => { e.stopPropagation(); deleteConv.mutate(c.id); }}
                  className="opacity-0 group-hover:opacity-100 hover:text-rose-400 p-0.5"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Main chat interface viewport */}
      <Card className="lg:col-span-3 flex flex-col justify-between overflow-hidden bg-card/25 border-border/40 relative">
        
        {/* Messages list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 select-text">
          {activeConvId || messages.length > 0 ? (
            <div className="space-y-4 text-xs">
              {messages.map((m: any, idx: number) => (
                <div key={idx} className={`flex flex-col space-y-2 p-3.5 rounded-xl border ${
                  m.role === 'user' 
                    ? 'bg-secondary/25 border-border/20 self-end ml-12 text-zinc-100' 
                    : 'bg-card/45 border-violet-500/10 self-start mr-12 text-zinc-300'
                }`}>
                  <div className="flex items-center gap-1.5 mb-1 select-none">
                    <span className={`text-[10px] font-bold uppercase tracking-wider ${
                      m.role === 'user' ? 'text-zinc-400' : 'text-[#f5d0fe]'
                    }`}>{m.role === 'user' ? 'Developer' : 'Assistant'}</span>
                  </div>
                  
                  <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>

                  {/* Navigable Citations grid list */}
                  {m.citations && m.citations.length > 0 && (
                    <div className="pt-3 border-t border-border/20 mt-2 select-none flex flex-wrap gap-2">
                      {m.citations.map((cit: any, cidx: number) => (
                        <button
                          key={cidx}
                          onClick={() => onSelectFile(cit.file_id)}
                          className="flex items-center gap-1.5 px-2 py-1 bg-[#0b081a] border border-border/60 hover:border-[#a21caf] hover:text-[#f5d0fe] rounded text-[10px] cursor-pointer font-mono"
                        >
                          <ShieldCheck className="h-3 w-3 text-emerald-500" />
                          <span>{cit.title}</span>
                          <ArrowRight className="h-2.5 w-2.5" />
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {/* Streaming tokens indicator */}
              {streamingMessage && (
                <div className="p-3.5 bg-card/45 border border-violet-500/10 rounded-xl mr-12 text-zinc-300">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#f5d0fe] block mb-2 select-none">Assistant</span>
                  <p className="whitespace-pre-wrap leading-relaxed">{streamingMessage}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center p-6 select-none">
              <Sparkles className="h-10 w-10 text-[#a21caf] animate-pulse mb-2" />
              <h4 className="font-semibold text-sm text-white">AI Repository Assistant</h4>
              <p className="text-xs text-muted-foreground max-w-xs mt-1 mb-6">
                Ask questions regarding project architectures or request flows grounded in this repository.
              </p>

              {/* Suggestions */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-md text-left">
                {suggestedQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(q)}
                    className="p-3 bg-secondary/15 border border-border/40 hover:border-border/80 rounded-lg text-[11px] font-semibold text-zinc-300 transition-all text-left flex justify-between items-center cursor-pointer"
                  >
                    <span>{q}</span>
                    <ArrowRight className="h-3.5 w-3.5 text-zinc-500 shrink-0 ml-2" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Input box */}
        <CardFooter className="border-t border-border/40 p-3 flex gap-2">
          <input
            type="text"
            placeholder="Ask AI about codebase... (e.g. explain authentication middleware)"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage(inputMessage)}
            disabled={isGenerating}
            className="flex-1 h-10 px-3 bg-secondary/50 text-foreground text-xs border border-border rounded-lg focus:outline-hidden"
          />
          <Button 
            onClick={() => handleSendMessage(inputMessage)}
            loading={isGenerating}
            disabled={!inputMessage.trim()}
            variant="primary"
          >
            <Send className="h-4 w-4" />
          </Button>
        </CardFooter>

      </Card>

    </div>
  );
};
