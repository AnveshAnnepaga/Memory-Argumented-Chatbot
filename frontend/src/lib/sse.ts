import { API_BASE_URL } from './api';

export interface SSECallbacks {
  onStep?: (data: { node: string; status: string; label: string }) => void;
  onToken?: (data: { text: string }) => void;
  onEvaluation?: (data: any) => void;
  onComplete?: (data: any) => void;
  onError?: (error: string) => void;
}

export async function streamChatQuery(
  query: string,
  conversationId: string = 'default',
  userId: string = 'default',
  callbacks: SSECallbacks
): Promise<void> {
  const url = `${API_BASE_URL}/chat/stream`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        conversation_id: conversationId,
        user_id: userId,
      }),
    });

    if (!response.ok || !response.body) {
      throw new Error(`SSE request failed with status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split('\n\n');
      buffer = blocks.pop() || '';

      for (const block of blocks) {
        const lines = block.split('\n');
        let eventType = 'message';
        let dataStr = '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.substring(7).trim();
          } else if (line.startsWith('data: ')) {
            dataStr = line.substring(6).trim();
          }
        }

        if (!dataStr) continue;

        try {
          const parsed = JSON.parse(dataStr);
          if (eventType === 'step' && callbacks.onStep) {
            callbacks.onStep(parsed);
          } else if (eventType === 'token' && callbacks.onToken) {
            callbacks.onToken(parsed);
          } else if (eventType === 'evaluation' && callbacks.onEvaluation) {
            callbacks.onEvaluation(parsed);
          } else if (eventType === 'complete' && callbacks.onComplete) {
            callbacks.onComplete(parsed);
          } else if (eventType === 'error' && callbacks.onError) {
            callbacks.onError(parsed.error || 'Unknown streaming error');
          }
        } catch (e) {
          console.error('Error parsing SSE data chunk:', dataStr, e);
        }
      }
    }
  } catch (error: any) {
    if (callbacks.onError) {
      callbacks.onError(error.message || 'Stream connection failed');
    }
  }
}
