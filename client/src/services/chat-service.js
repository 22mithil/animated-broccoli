const API_BASE_URL = 'http://localhost:8001';

export class ChatService {
  static async getHistory() {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch chat history');
      }

      const history = await response.json();
      return history.map((session) => ({
        id: session._id,
        title:
          session.title ||
          `Chat ${new Date(session.created_at).toLocaleDateString()}`,
        timestamp: session.created_at,
        messages: session.messages || [],
      }));
    } catch (error) {
      console.error('Error fetching chat history:', error);
      throw error;
    }
  }
  static async createSession() {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to create chat session');
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating chat session:', error);
      throw error;
    }
  }

  static async getSession(sessionId) {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/session/${sessionId}`);

      if (!response.ok) {
        throw new Error('Failed to get chat session');
      }

      const session = await response.json();

      // Format messages for frontend use
      const formattedMessages =
        session.messages?.map((message) => ({
          id: message._id || `${Date.now()}-${message.role}`,
          role: message.role,
          content: message.content,
          timestamp: message.timestamp,
          query_metadata: message.query_metadata,
        })) || [];

      return {
        ...session,
        messages: formattedMessages,
      };
    } catch (error) {
      console.error('Error getting chat session:', error);
      throw error;
    }
  }

  static async sendMessage(query, sessionId = null) {
    try {
      // If no sessionId is provided, create a new session first
      if (!sessionId) {
        const session = await this.createSession();
        sessionId = session._id;
      }

      const response = await fetch(
        `${API_BASE_URL}/query?session_id=${sessionId}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const result = await response.json();

      // Format messages based on the query and response
      const messages = [
        {
          id: Date.now() + '-user',
          role: 'user',
          content: query,
          timestamp: new Date().toISOString(),
        },
        {
          id: Date.now() + '-assistant',
          role: 'assistant',
          content: result.response,
          timestamp: new Date().toISOString(),
          query_metadata: {
            original_query: result.original_query,
            enhanced_query: result.enhanced_query,
            detected_label: result.detected_label,
            results: result.results,
          },
        },
      ];

      return {
        ...result,
        sessionId,
        messages,
      };
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }
}
