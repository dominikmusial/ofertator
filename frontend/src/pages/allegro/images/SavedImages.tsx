import React, { useState } from 'react';
import { useSharedAccounts } from '../../../hooks/marketplaces/allegro/accounts';
import { useBulkDownloadImages } from '../../../hooks/shared/images/bulk';
import { useBulkDeleteImages } from '../../../hooks/shared/images/bulk';
import AccountSelectorWithProps from '../../../components/ui/AccountSelectorWithProps';
import { AuthenticatedImage } from '../../../components/ui/AuthenticatedImage';
import toast from 'react-hot-toast';
import api from '../../../lib/api';

interface SavedImage {
  filename: string;
  url: string;
  size: number;
}

interface SavedImagesData {
  account_name: string;
  saved_images: {
    original: Record<string, SavedImage[]>;
    processed: Record<string, SavedImage[]>;
  };
}

export default function SavedImages() {
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [savedImagesData, setSavedImagesData] = useState<SavedImagesData | null>(null);
  const [loading, setLoading] = useState(false);

  const [previewImage, setPreviewImage] = useState<{url: string, filename: string} | null>(null);
  const [deletingImage, setDeletingImage] = useState<string | null>(null);
  const [selectedOriginalOffers, setSelectedOriginalOffers] = useState<Set<string>>(new Set());
  const [selectedProcessedOffers, setSelectedProcessedOffers] = useState<Set<string>>(new Set());

  const { accounts, isLoading: accountsLoading } = useSharedAccounts();
  const { 
    isDownloading: isBulkDownloading, 
    downloadProgress, 
    downloadStatus, 
    startBulkDownload, 
    cancelBulkDownload 
  } = useBulkDownloadImages();
  const { 
    isDeleting: isBulkDeleting, 
    deleteProgress, 
    deleteStatus, 
    startBulkDelete, 
    cancelBulkDelete 
  } = useBulkDeleteImages();

  const loadSavedImages = async (accountId: number) => {
    setLoading(true);
    try {
      const response = await api.get(`/allegro/offers/saved-images/${accountId}`);
      setSavedImagesData(response.data);
    } catch (error: any) {
      toast.error(`Failed to load saved images: ${error.response?.data?.detail || error.message}`);
      setSavedImagesData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleAccountChange = (accountId: number | null) => {
    setSelectedAccountId(accountId);
    setSavedImagesData(null);
    setSelectedOriginalOffers(new Set());
    setSelectedProcessedOffers(new Set());
    if (accountId) {
      loadSavedImages(accountId);
    }
  };

  const handleOfferSelection = (offerId: string, checked: boolean, imageType: 'original' | 'processed') => {
    if (imageType === 'original') {
      const newSelectedOffers = new Set(selectedOriginalOffers);
      if (checked) {
        newSelectedOffers.add(offerId);
      } else {
        newSelectedOffers.delete(offerId);
      }
      setSelectedOriginalOffers(newSelectedOffers);
    } else {
      const newSelectedOffers = new Set(selectedProcessedOffers);
      if (checked) {
        newSelectedOffers.add(offerId);
      } else {
        newSelectedOffers.delete(offerId);
      }
      setSelectedProcessedOffers(newSelectedOffers);
    }
  };

  const handleSelectAllOffers = (imageType: 'original' | 'processed', checked: boolean) => {
    if (savedImagesData) {
      const offers = Object.keys(savedImagesData.saved_images[imageType]);
      if (imageType === 'original') {
        const newSelectedOffers = new Set(selectedOriginalOffers);
        if (checked) {
          offers.forEach(offerId => newSelectedOffers.add(offerId));
        } else {
          offers.forEach(offerId => newSelectedOffers.delete(offerId));
        }
        setSelectedOriginalOffers(newSelectedOffers);
      } else {
        const newSelectedOffers = new Set(selectedProcessedOffers);
        if (checked) {
          offers.forEach(offerId => newSelectedOffers.add(offerId));
        } else {
          offers.forEach(offerId => newSelectedOffers.delete(offerId));
        }
        setSelectedProcessedOffers(newSelectedOffers);
      }
    }
  };

  const handleBulkDownload = async (imageType: 'original' | 'processed') => {
    if (!selectedAccountId) return;

    try {
      const selectedOffers = imageType === 'original' ? selectedOriginalOffers : selectedProcessedOffers;
      const offerIds = Array.from(selectedOffers);
      
      if (offerIds.length === 0) {
        toast.error('Please select at least one offer to download');
        return;
      }

      await startBulkDownload(selectedAccountId, imageType, offerIds);
    } catch (error) {
      // Error handling is done in the hook
    }
  };

  const handleBulkDelete = async (imageType: 'original' | 'processed') => {
    if (!selectedAccountId) return;

    try {
      const selectedOffers = imageType === 'original' ? selectedOriginalOffers : selectedProcessedOffers;
      const offerIds = Array.from(selectedOffers);
      
      if (offerIds.length === 0) {
        toast.error('Please select at least one offer to delete');
        return;
      }

      // Show confirmation dialog
      const confirmed = window.confirm(
        `Are you sure you want to delete all ${imageType} images from ${offerIds.length} selected offers? This action cannot be undone.`
      );
      
      if (!confirmed) return;

      await startBulkDelete(selectedAccountId, imageType, offerIds);
      
      // Refresh the saved images data after successful deletion
      setTimeout(() => {
        loadSavedImages(selectedAccountId);
      }, 2000);
    } catch (error) {
      // Error handling is done in the hook
    }
  };

  const downloadSingleImage = async (imageUrl: string, filename: string) => {
    try {
      const response = await api.get(imageUrl, { responseType: 'blob' });
      const blob = new Blob([response.data]);
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success(`Downloaded ${filename}`);
    } catch (error: any) {
      toast.error(`Failed to download image: ${error.response?.data?.detail || error.message}`);
    }
  };

  const deleteImage = async (accountId: number, imageType: 'original' | 'processed', offerId: string, filename: string) => {
    const deleteKey = `${imageType}-${offerId}-${filename}`;
    setDeletingImage(deleteKey);
    
    try {
      // Call API to delete the image
      await api.delete(`/allegro/offers/saved-images/${accountId}/delete/${imageType}/${offerId}/${filename}`);
      
      // Refresh the saved images data
      loadSavedImages(accountId);
      toast.success(`Deleted ${filename}`);
    } catch (error: any) {
      toast.error(`Failed to delete image: ${error.response?.data?.detail || error.message}`);
    } finally {
      setDeletingImage(null);
    }
  };

  const openPreview = (imageUrl: string, filename: string) => {
    setPreviewImage({ url: imageUrl, filename });
  };

  const closePreview = () => {
    setPreviewImage(null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Zapisane zdjęcia</h1>
        <p className="text-gray-600 mb-6">
          Przeglądaj i pobieraj zdjęcia zapisane z przetwarzania ofert. Obrazy są uporządkowane według oferty i typu (oryginalne/przetworzone).
        </p>

        <div className="mb-6">
          <AccountSelectorWithProps
            accounts={(accounts as any) || []}
            selectedAccountId={selectedAccountId}
            onAccountSelect={handleAccountChange}
            loading={accountsLoading}
          />
        </div>
      </div>

      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-2 text-gray-600">Loading saved images...</span>
        </div>
      )}

      {savedImagesData && (
        <div className="space-y-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Account: {savedImagesData.account_name}
            </h2>
            
            {/* Original Images Section */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-800 flex items-center">
                  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-md text-sm mr-2">
                    Original Images
                  </span>
                  ({Object.keys(savedImagesData.saved_images.original).length} offers)
                </h3>
                <div className="flex items-center space-x-2">
                  <label className="flex items-center text-sm text-gray-600">
                    <input
                      type="checkbox"
                      className="mr-2"
                      checked={Object.keys(savedImagesData.saved_images.original).every(offerId => selectedOriginalOffers.has(offerId))}
                      onChange={(e) => handleSelectAllOffers('original', e.target.checked)}
                    />
                    Select All
                  </label>
                  <button
                    onClick={() => handleBulkDownload('original')}
                    disabled={isBulkDownloading || isBulkDeleting || selectedOriginalOffers.size === 0}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm disabled:opacity-50"
                  >
                    Download Selected ({selectedOriginalOffers.size})
                  </button>
                  <button
                    onClick={() => handleBulkDelete('original')}
                    disabled={isBulkDownloading || isBulkDeleting || selectedOriginalOffers.size === 0}
                    className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm disabled:opacity-50"
                  >
                    Delete Selected ({selectedOriginalOffers.size})
                  </button>
                </div>
              </div>
              
              {Object.keys(savedImagesData.saved_images.original).length === 0 ? (
                <p className="text-gray-500 italic">No original images saved yet.</p>
              ) : (
                <div className="grid gap-4">
                  {Object.entries(savedImagesData.saved_images.original).map(([offerId, images]) => (
                    <div key={`original-${offerId}`} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center mb-3">
                        <input
                          type="checkbox"
                          className="mr-3"
                          checked={selectedOriginalOffers.has(offerId)}
                          onChange={(e) => handleOfferSelection(offerId, e.target.checked, 'original')}
                        />
                        <h4 className="font-medium text-gray-900">Offer ID: {offerId}</h4>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {images.map((image, idx) => (
                          <div key={idx} className="border border-gray-200 rounded-lg p-2 hover:shadow-md transition-shadow">
                            <div className="relative group">
                              <AuthenticatedImage
                                src={image.url}
                                alt={image.filename}
                                className="w-full h-20 object-cover rounded cursor-pointer"
                                onClick={() => openPreview(image.url, image.filename)}
                              />
                              {/* Image overlay controls */}
                              <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity rounded flex items-center justify-center space-x-2">
                                <button
                                  onClick={() => openPreview(image.url, image.filename)}
                                  className="p-1 bg-white rounded-full hover:bg-gray-100"
                                  title="Preview"
                                >
                                  <svg className="w-4 h-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() => downloadSingleImage(image.url, image.filename)}
                                  className="p-1 bg-white rounded-full hover:bg-gray-100"
                                  title="Download"
                                >
                                  <svg className="w-4 h-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() => deleteImage(selectedAccountId!, 'original', offerId, image.filename)}
                                  disabled={deletingImage === `original-${offerId}-${image.filename}`}
                                  className="p-1 bg-white rounded-full hover:bg-gray-100 disabled:opacity-50"
                                  title="Delete"
                                >
                                  <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                  </svg>
                                </button>
                              </div>
                            </div>
                            <p className="text-xs text-gray-600 truncate mt-1" title={image.filename}>{image.filename}</p>
                            <p className="text-xs text-gray-500">{formatFileSize(image.size)}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Processed Images Section */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-800 flex items-center">
                  <span className="bg-green-100 text-green-800 px-2 py-1 rounded-md text-sm mr-2">
                    Processed Images
                  </span>
                  ({Object.keys(savedImagesData.saved_images.processed).length} offers)
                </h3>
                <div className="flex items-center space-x-2">
                  <label className="flex items-center text-sm text-gray-600">
                    <input
                      type="checkbox"
                      className="mr-2"
                      checked={Object.keys(savedImagesData.saved_images.processed).every(offerId => selectedProcessedOffers.has(offerId))}
                      onChange={(e) => handleSelectAllOffers('processed', e.target.checked)}
                    />
                    Select All
                  </label>
                  <button
                    onClick={() => handleBulkDownload('processed')}
                    disabled={isBulkDownloading || isBulkDeleting || selectedProcessedOffers.size === 0}
                    className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm disabled:opacity-50"
                  >
                    Download Selected ({selectedProcessedOffers.size})
                  </button>
                  <button
                    onClick={() => handleBulkDelete('processed')}
                    disabled={isBulkDownloading || isBulkDeleting || selectedProcessedOffers.size === 0}
                    className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm disabled:opacity-50"
                  >
                    Delete Selected ({selectedProcessedOffers.size})
                  </button>
                </div>
              </div>
              
              {Object.keys(savedImagesData.saved_images.processed).length === 0 ? (
                <p className="text-gray-500 italic">No processed images saved yet.</p>
              ) : (
                <div className="grid gap-4">
                  {Object.entries(savedImagesData.saved_images.processed).map(([offerId, images]) => (
                    <div key={`processed-${offerId}`} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center mb-3">
                        <input
                          type="checkbox"
                          className="mr-3"
                          checked={selectedProcessedOffers.has(offerId)}
                          onChange={(e) => handleOfferSelection(offerId, e.target.checked, 'processed')}
                        />
                        <h4 className="font-medium text-gray-900">Offer ID: {offerId}</h4>
                      </div>
                                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                                 {images.map((image, idx) => (
                           <div key={idx} className="border border-gray-200 rounded-lg p-2 hover:shadow-md transition-shadow">
                             <div className="relative group">
                               <AuthenticatedImage
                                 src={image.url}
                                 alt={image.filename}
                                 className="w-full h-20 object-cover rounded cursor-pointer"
                                 onClick={() => openPreview(image.url, image.filename)}
                               />
                               {/* Image overlay controls */}
                               <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity rounded flex items-center justify-center space-x-2">
                                 <button
                                   onClick={() => openPreview(image.url, image.filename)}
                                   className="p-1 bg-white rounded-full hover:bg-gray-100"
                                   title="Preview"
                                 >
                                   <svg className="w-4 h-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                   </svg>
                                 </button>
                                 <button
                                   onClick={() => downloadSingleImage(image.url, image.filename)}
                                   className="p-1 bg-white rounded-full hover:bg-gray-100"
                                   title="Download"
                                 >
                                   <svg className="w-4 h-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                   </svg>
                                 </button>
                                 <button
                                   onClick={() => deleteImage(selectedAccountId!, 'processed', offerId, image.filename)}
                                   disabled={deletingImage === `processed-${offerId}-${image.filename}`}
                                   className="p-1 bg-white rounded-full hover:bg-gray-100 disabled:opacity-50"
                                   title="Delete"
                                 >
                                   <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                   </svg>
                                 </button>
                               </div>
                             </div>
                             <p className="text-xs text-gray-600 truncate mt-1" title={image.filename}>{image.filename}</p>
                             <p className="text-xs text-gray-500">{formatFileSize(image.size)}</p>
                           </div>
                         ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {selectedAccountId && !loading && !savedImagesData && (
        <div className="text-center py-12">
          <p className="text-gray-500">No saved images found for this account.</p>
          <p className="text-gray-400 text-sm mt-2">
            Images will appear here after you use the "Save original images" or "Save processed images" 
            options in the Offer Editor.
          </p>
        </div>
      )}

      {/* Image Preview Modal */}
      {previewImage && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" onClick={closePreview}>
          <div className="relative max-w-4xl max-h-full p-4" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={closePreview}
              className="absolute top-2 right-2 text-white hover:text-gray-300 z-10"
            >
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <AuthenticatedImage
              src={previewImage.url}
              alt={previewImage.filename}
              className="max-w-full max-h-full object-contain"
            />
            <div className="absolute bottom-4 left-4 bg-black bg-opacity-50 text-white px-3 py-2 rounded">
              {previewImage.filename}
            </div>
          </div>
        </div>
      )}

      {/* Bulk Download Progress Modal */}
      {isBulkDownloading && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Bulk Download Progress</h3>
              <button
                onClick={cancelBulkDownload}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Progress</span>
                <span>{downloadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${downloadProgress}%` }}
                ></div>
              </div>
            </div>
            
            <div className="text-sm text-gray-600 mb-4">
              {downloadStatus}
            </div>
            
            <div className="flex justify-end space-x-2">
              <button
                onClick={cancelBulkDownload}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Delete Progress Modal */}
      {isBulkDeleting && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Bulk Delete Progress</h3>
              <button
                onClick={cancelBulkDelete}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Progress</span>
                <span>{deleteProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-red-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${deleteProgress}%` }}
                ></div>
              </div>
            </div>
            
            <div className="text-sm text-gray-600 mb-4">
              {deleteStatus}
            </div>
            
            <div className="flex justify-end space-x-2">
              <button
                onClick={cancelBulkDelete}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 