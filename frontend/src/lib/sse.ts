import { API_BASE_URL } from './api';

type SSEPayload = Record<string, unknown>;

interface SSEStepPayload {
  node: string;
  status: string;
  label: string;
}

interface SSETokenPayload {
  text: string;
}

export interface SSECallbacks {
  onStep?: (data: SSEStepPayload) => void;
  onToken?: (data: SSETokenPayload) => void;
  onEvaluation?: (data: SSEPayload) => void;
  onComplete?: (data: SSEPayload) => void;
  onError?: (error: string) => void;
}

function isRecord(value: unknown): value is SSEPayload {
  return typeof value === 'object' && value !== null;
}

export async function streamChatQuery(
  query: string,
  conversationId: string = 'default',
  userId: string = 'default',
  callbacks: SSECallbacks,
  fileIds: string[] = [],
  imageIds: string[] = [],
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
        file_ids: fileIds,
        image_ids: imageIds,
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
          const parsed: unknown = JSON.parse(dataStr);
          if (!isRecord(parsed)) {
            continue;
          }

          if (eventType === 'step' && callbacks.onStep) {
            callbacks.onStep({
              node: typeof parsed.node === 'string' ? parsed.node : 'unknown',
              status: typeof parsed.status === 'string' ? parsed.status : 'UNKNOWN',
              label: typeof parsed.label === 'string' ? parsed.label : 'Processing...',
            });
          } else if (eventType === 'token' && callbacks.onToken) {
            callbacks.onToken({
              text: typeof parsed.text === 'string' ? parsed.text : '',
            });
          } else if (eventType === 'evaluation' && callbacks.onEvaluation) {
            callbacks.onEvaluation(parsed);
          } else if (eventType === 'complete' && callbacks.onComplete) {
            callbacks.onComplete(parsed);
          } else if (eventType === 'error' && callbacks.onError) {
            callbacks.onError(
              typeof parsed.error === 'string' ? parsed.error : 'Unknown streaming error'
            );
          }
        } catch (error) {
          console.error('Error parsing SSE data chunk:', dataStr, error);
        }
      }
    }
  } catch (error: unknown) {
    if (callbacks.onError) {
      callbacks.onError(
        error instanceof Error ? error.message : 'Stream connection failed'
      );
    }
  }
}
