import { useState, useEffect } from 'react';
import { api } from '../../../../lib/api';

interface TaskStatus {
  task_id: string;
  account_id: number;
  status: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  result?: {
    status: string;
    account_name?: string;
    account_id?: number;
    error?: string;
    is_reauth?: boolean;
  };
}

export const useReAuthStatus = (accountId: number | null, taskId: string | null) => {
  const [status, setStatus] = useState<TaskStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    if (!accountId || !taskId) {
      setStatus(null);
      setIsPolling(false);
      return;
    }

    setIsPolling(true);
    let pollInterval: NodeJS.Timeout;

    const pollStatus = async () => {
      try {
        const response = await api.get<TaskStatus>(
          `/allegro/accounts/${accountId}/re-authenticate/status/${taskId}`
        );
        
        setStatus(response.data);

        // Debug logging
        console.log('Re-auth status poll:', {
          celeryStatus: response.data.status,
          resultStatus: response.data.result?.status,
          result: response.data.result
        });

        // Stop polling only when we have a final result
        // Check both Celery task status AND our custom result.status
        const celeryComplete = response.data.status === 'SUCCESS' || response.data.status === 'FAILURE';
        const hasTerminalResult = response.data.result && 
                                  (response.data.result.status === 'SUCCESS' || 
                                   response.data.result.status === 'FAILURE');
        
        // Stop only when Celery task is done AND we have a terminal result
        if (celeryComplete && hasTerminalResult) {
          console.log('Stopping poll - task complete with result:', response.data.result);
          setIsPolling(false);
          if (pollInterval) {
            clearInterval(pollInterval);
          }
        }
      } catch (error) {
        console.error('Error polling re-auth status:', error);
        setIsPolling(false);
        if (pollInterval) {
          clearInterval(pollInterval);
        }
      }
    };

    // Poll immediately, then every 2 seconds
    pollStatus();
    pollInterval = setInterval(pollStatus, 2000);

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [accountId, taskId]);

  return {
    status,
    isPolling,
  };
};


