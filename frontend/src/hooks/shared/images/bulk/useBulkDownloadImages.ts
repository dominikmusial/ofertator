import { useState } from 'react';
import api from '../../../../lib/api';
import toast from 'react-hot-toast';

interface BulkDownloadResult {
  download_url: string;
  filename: string;
  total_images: number;
  total_offers: number;
  processed_offers: string[];
  skipped_offers: string[];
}

interface BulkDownloadStatus {
  state: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  status?: string;
  progress?: number;
  result?: BulkDownloadResult;
  error?: string;
}

export const useBulkDownloadImages = () => {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadStatus, setDownloadStatus] = useState<string>('');
  const [taskId, setTaskId] = useState<string | null>(null);

  const startBulkDownload = async (
    accountId: number,
    imageType: 'original' | 'processed',
    offerIds?: string[]
  ) => {
    setIsDownloading(true);
    setDownloadProgress(0);
    setDownloadStatus('Starting bulk download...');
    setTaskId(null);

    try {
      // Start the bulk download task
      const response = await api.post(
        `/allegro/offers/saved-images/${accountId}/bulk-download/${imageType}`,
        offerIds || null
      );

      const newTaskId = response.data.task_id;
      setTaskId(newTaskId);

      // Poll for task status
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await api.get(
            `/allegro/offers/saved-images/${accountId}/bulk-download/status/${newTaskId}`
          );

          const status: BulkDownloadStatus = statusResponse.data;

          if (status.state === 'PROGRESS') {
            setDownloadProgress(status.progress || 0);
            setDownloadStatus(status.status || 'Processing...');
          } else if (status.state === 'SUCCESS') {
            clearInterval(pollInterval);
            setDownloadProgress(100);
            setDownloadStatus('Download ready!');

            // Download the ZIP file
            const result = status.result!;
            const downloadResponse = await api.get(
              `/allegro/offers/saved-images/${accountId}/bulk-download/download/${result.filename}`,
              { responseType: 'blob' }
            );

            // Create download link
            const blob = new Blob([downloadResponse.data], { type: 'application/zip' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = result.filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            // Show success message with summary
            toast.success(
              `Downloaded ${result.total_images} images from ${result.total_offers} offers`,
              { duration: 5000 }
            );

            setIsDownloading(false);
            setTaskId(null);

            return result;
          } else if (status.state === 'FAILURE') {
            clearInterval(pollInterval);
            setIsDownloading(false);
            setTaskId(null);
            throw new Error(status.error || 'Bulk download failed');
          }
        } catch (error) {
          clearInterval(pollInterval);
          setIsDownloading(false);
          setTaskId(null);
          throw error;
        }
      }, 2000); // Poll every 2 seconds

      // Set a timeout to prevent infinite polling
      setTimeout(() => {
        clearInterval(pollInterval);
        if (isDownloading) {
          setIsDownloading(false);
          setTaskId(null);
          toast.error('Bulk download timed out');
        }
      }, 300000); // 5 minutes timeout

    } catch (error: any) {
      setIsDownloading(false);
      setTaskId(null);
      toast.error(`Bulk download failed: ${error.response?.data?.detail || error.message}`);
      throw error;
    }
  };

  const cancelBulkDownload = () => {
    if (taskId) {
      // Note: We could implement task cancellation on the backend if needed
      setIsDownloading(false);
      setTaskId(null);
      setDownloadProgress(0);
      setDownloadStatus('');
      toast('Bulk download cancelled');
    }
  };

  return {
    isDownloading,
    downloadProgress,
    downloadStatus,
    startBulkDownload,
    cancelBulkDownload,
  };
}; 