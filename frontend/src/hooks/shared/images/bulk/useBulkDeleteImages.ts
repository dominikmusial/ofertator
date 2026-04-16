import { useState } from 'react';
import api from '../../../../lib/api';
import toast from 'react-hot-toast';

interface BulkDeleteResult {
  deleted_count: number;
  failed_count: number;
  total_offers: number;
  deleted_offers: string[];
  failed_deletions: Array<{
    object_name: string;
    error: string;
  }>;
}

interface BulkDeleteStatus {
  state: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  status?: string;
  progress?: number;
  result?: BulkDeleteResult;
  error?: string;
}

export const useBulkDeleteImages = () => {
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteProgress, setDeleteProgress] = useState(0);
  const [deleteStatus, setDeleteStatus] = useState<string>('');
  const [taskId, setTaskId] = useState<string | null>(null);

  const startBulkDelete = async (
    accountId: number,
    imageType: 'original' | 'processed',
    offerIds?: string[]
  ) => {
    setIsDeleting(true);
    setDeleteProgress(0);
    setDeleteStatus('Starting bulk deletion...');
    setTaskId(null);

    try {
      // Start the bulk delete task
      const response = await api.post(
        `/allegro/offers/saved-images/${accountId}/bulk-delete/${imageType}`,
        offerIds || null
      );

      const newTaskId = response.data.task_id;
      setTaskId(newTaskId);

      // Poll for task status
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await api.get(
            `/allegro/offers/saved-images/${accountId}/bulk-delete/status/${newTaskId}`
          );
          
          const taskStatus: BulkDeleteStatus = statusResponse.data;
          
          if (taskStatus.state === 'PROGRESS') {
            setDeleteProgress(taskStatus.progress || 0);
            setDeleteStatus(taskStatus.status || 'Processing...');
          } else if (taskStatus.state === 'SUCCESS') {
            clearInterval(pollInterval);
            setDeleteProgress(100);
            setDeleteStatus('Bulk deletion completed!');
            setIsDeleting(false);
            
            const result = taskStatus.result!;
            toast.success(
              `Successfully deleted ${result.deleted_count} images from ${result.total_offers} offers!`
            );
            
            if (result.failed_count > 0) {
              toast.error(
                `Failed to delete ${result.failed_count} images. Check console for details.`
              );
              console.error('Failed deletions:', result.failed_deletions);
            }
          } else if (taskStatus.state === 'FAILURE') {
            clearInterval(pollInterval);
            setIsDeleting(false);
            toast.error(`Bulk deletion failed: ${taskStatus.error}`);
            console.error('Bulk deletion error:', taskStatus.error);
          }
        } catch (error) {
          console.error('Error polling task status:', error);
          clearInterval(pollInterval);
          setIsDeleting(false);
          toast.error('Error checking deletion status');
        }
      }, 2000);

      // Set timeout to stop polling after 10 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        if (isDeleting) {
          setIsDeleting(false);
          toast.error('Bulk deletion timed out');
        }
      }, 600000);

    } catch (error: any) {
      setIsDeleting(false);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      toast.error(`Failed to start bulk deletion: ${errorMessage}`);
      console.error('Bulk deletion error:', error);
    }
  };

  const cancelBulkDelete = () => {
    setIsDeleting(false);
    setDeleteProgress(0);
    setDeleteStatus('');
    setTaskId(null);
    toast.success('Bulk deletion cancelled');
  };

  return {
    isDeleting,
    deleteProgress,
    deleteStatus,
    startBulkDelete,
    cancelBulkDelete,
    taskId
  };
}; 