import React, { useState, useRef, useCallback } from 'react';
import { useSharedAccounts } from '../../../hooks/marketplaces/allegro/accounts';
import { 
  useAccountImages, 
  useUploadAccountImages, 
  useSetAccountLogo, 
  useSetAccountFillers,
  useDeleteAccountImages,
  useUnsetAccountLogo,
  useUnsetAccountFillers,
  AccountImage 
} from '../../../hooks/shared/accounts';
import AccountSelectorWithProps from '../../../components/ui/AccountSelectorWithProps';
import { AuthenticatedImage } from '../../../components/ui/AuthenticatedImage';
import { toast } from 'react-hot-toast';
import api from '../../../lib/api';

interface DuplicateInfo {
  original_filename: string;
  is_duplicate: boolean;
  suggested_filename: string;
}

interface DuplicateModalData {
  files: File[];
  duplicates: DuplicateInfo[];
  filenameOverrides: { [key: string]: string };
}

const Images: React.FC = () => {
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [selectedImages, setSelectedImages] = useState<number[]>([]);
  const [previewImage, setPreviewImage] = useState<AccountImage | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [duplicateModal, setDuplicateModal] = useState<DuplicateModalData | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Hooks
  const { accounts, isLoading: accountsLoading } = useSharedAccounts();
  const { data: images, isLoading: imagesLoading, refetch: refetchImages } = useAccountImages(selectedAccountId || 0);
  const uploadMutation = useUploadAccountImages();
  const setLogoMutation = useSetAccountLogo();
  const setFillersMutation = useSetAccountFillers();
  const deleteMutation = useDeleteAccountImages();
  const unsetLogoMutation = useUnsetAccountLogo();
  const unsetFillersMutation = useUnsetAccountFillers();

  // Get logo and filler images
  const logoImage = images?.find(img => img.is_logo);
  const fillerImages = images?.filter(img => img.is_filler).sort((a, b) => (a.filler_position || 0) - (b.filler_position || 0));
  const regularImages = images?.filter(img => !img.is_logo && !img.is_filler) || [];

  // File upload handlers
  const proceedWithUpload = useCallback((files: File[], filenameOverrides: { [key: string]: string }) => {
    if (!selectedAccountId) return;

    uploadMutation.mutate(
      { accountId: selectedAccountId, files, filenameOverrides },
      {
        onSuccess: (data) => {
          const { uploaded_images, count, skipped_files } = data;
          
          if (count > 0) {
            toast.success(`Successfully uploaded ${count} images`);
          }
          
          if (skipped_files && skipped_files.length > 0) {
            skipped_files.forEach((skipped: any) => {
              toast.error(`Skipped ${skipped.filename}: ${skipped.reason}`);
            });
          }
          
          setSelectedImages([]);
          setDuplicateModal(null);
          
          // Reset file input
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
        },
        onError: (error) => {
          toast.error(`Upload failed: ${error.message}`);
          setDuplicateModal(null);
          
          // Reset file input
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
        },
      }
    );
  }, [selectedAccountId, uploadMutation]);

  const handleFileSelect = useCallback(async (files: FileList) => {
    if (!selectedAccountId) {
      toast.error('Please select an account first');
      return;
    }

    const fileArray = Array.from(files);
    const filenames = fileArray.map(file => file.name);

    try {
      // Check for duplicates
      const response = await api.post(`/allegro/images/account/${selectedAccountId}/check-duplicates`, filenames);
      const duplicates = response.data.duplicates;
      
      const hasDuplicates = duplicates.some((d: DuplicateInfo) => d.is_duplicate);
      
      if (hasDuplicates) {
        // Show duplicate resolution modal
        setDuplicateModal({
          files: fileArray,
          duplicates,
          filenameOverrides: {}
        });
      } else {
        // No duplicates, proceed with upload
        proceedWithUpload(fileArray, {});
      }
    } catch (error: any) {
      toast.error(`Failed to check duplicates: ${error.message}`);
      // Reset file input on error
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [selectedAccountId, proceedWithUpload]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  // Image selection handlers
  const toggleImageSelection = (imageId: number) => {
    setSelectedImages(prev => 
      prev.includes(imageId) 
        ? prev.filter(id => id !== imageId)
        : [...prev, imageId]
    );
  };

  const selectAllImages = () => {
    setSelectedImages(regularImages.map(img => img.id));
  };

  const clearSelection = () => {
    setSelectedImages([]);
  };

  // Action handlers
  const handleSetLogo = () => {
    if (selectedImages.length !== 1) {
      toast.error('Please select exactly one image to set as logo');
      return;
    }

    if (!selectedAccountId) return;

    setLogoMutation.mutate(
      { accountId: selectedAccountId, imageId: selectedImages[0] },
      {
        onSuccess: () => {
          toast.success('Logo set successfully');
          clearSelection();
        },
        onError: (error) => {
          toast.error(`Failed to set logo: ${error.message}`);
        },
      }
    );
  };

  const handleSetFillers = () => {
    if (selectedImages.length === 0) {
      toast.error('Please select images to set as fillers');
      return;
    }

    if (!selectedAccountId) return;

    setFillersMutation.mutate(
      { accountId: selectedAccountId, imageIds: selectedImages },
      {
        onSuccess: () => {
          toast.success(`Set ${selectedImages.length} filler images successfully`);
          clearSelection();
        },
        onError: (error) => {
          toast.error(`Failed to set fillers: ${error.message}`);
        },
      }
    );
  };

  const handleDeleteSelected = () => {
    if (selectedImages.length === 0) {
      toast.error('Please select images to delete');
      return;
    }

    if (!selectedAccountId) return;

    if (!confirm(`Are you sure you want to delete ${selectedImages.length} selected images?`)) {
      return;
    }

    deleteMutation.mutate(
      { accountId: selectedAccountId, imageIds: selectedImages },
      {
        onSuccess: () => {
          toast.success(`Deleted ${selectedImages.length} images successfully`);
          clearSelection();
        },
        onError: (error) => {
          toast.error(`Failed to delete images: ${error.message}`);
        },
      }
    );
  };

  const handleUnsetLogo = () => {
    if (!selectedAccountId) return;

    unsetLogoMutation.mutate(
      { accountId: selectedAccountId },
      {
        onSuccess: () => {
          toast.success('Logo removed successfully');
        },
        onError: (error) => {
          toast.error(`Failed to remove logo: ${error.message}`);
        },
      }
    );
  };

  const handleUnsetFillers = () => {
    if (!selectedAccountId) return;

    unsetFillersMutation.mutate(
      { accountId: selectedAccountId },
      {
        onSuccess: () => {
          toast.success('Filler images removed successfully');
        },
        onError: (error) => {
          toast.error(`Failed to remove fillers: ${error.message}`);
        },
      }
    );
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Dodawanie grafik</h1>

      {/* Account Selection */}
      <div className="mb-6">
        <AccountSelectorWithProps
          accounts={accounts || []}
          selectedAccountId={selectedAccountId}
          onAccountSelect={setSelectedAccountId}
          loading={accountsLoading}
        />
      </div>

      {selectedAccountId && (
        <>
          {/* Upload Section */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Wgraj obrazy</h2>
            
            {/* Drag and Drop Area */}
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                isDragOver 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <div className="mb-4">
                <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <p className="text-lg font-medium text-gray-900 mb-2">
                Przeciągnij i upuść obrazy tutaj
              </p>
              <p className="text-gray-500 mb-4">lub</p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium"
                disabled={uploadMutation.isPending}
              >
                {uploadMutation.isPending ? 'Wgrywanie...' : 'Wybierz pliki'}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files) {
                    handleFileSelect(e.target.files);
                  }
                }}
              />
            </div>
          </div>

          {/* Special Images Section */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Specjalne obrazy</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Logo */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">Logo:</h3>
                  {logoImage && (
                    <button
                      onClick={handleUnsetLogo}
                      className="text-red-600 hover:text-red-700 text-sm"
                      disabled={unsetLogoMutation.isPending}
                    >
                      Usuń
                    </button>
                  )}
                </div>
                {logoImage ? (
                  <div className="flex items-center space-x-3">
                    <AuthenticatedImage 
                      src={logoImage.url} 
                      alt="Logo" 
                      className="w-12 h-12 object-cover rounded cursor-pointer"
                      onClick={() => setPreviewImage(logoImage)}
                    />
                    <span className="text-sm text-gray-600">{logoImage.original_filename}</span>
                  </div>
                ) : (
                  <span className="text-gray-500">Nie znaleziono</span>
                )}
              </div>

              {/* Fillers */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">Obrazy uzupełniające:</h3>
                  {fillerImages && fillerImages.length > 0 && (
                    <button
                      onClick={handleUnsetFillers}
                      className="text-red-600 hover:text-red-700 text-sm"
                      disabled={unsetFillersMutation.isPending}
                    >
                      Usuń
                    </button>
                  )}
                </div>
                {fillerImages && fillerImages.length > 0 ? (
                  <div>
                    <span className="text-sm text-gray-600">Znaleziono ({fillerImages.length})</span>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {fillerImages.slice(0, 3).map((img) => (
                        <AuthenticatedImage
                          key={img.id}
                          src={img.url}
                          alt={`Filler ${img.filler_position}`}
                          className="w-8 h-8 object-cover rounded cursor-pointer"
                          onClick={() => setPreviewImage(img)}
                        />
                      ))}
                      {fillerImages.length > 3 && (
                        <span className="text-xs text-gray-500 self-center">+{fillerImages.length - 3} więcej</span>
                      )}
                    </div>
                  </div>
                ) : (
                  <span className="text-gray-500">Nie znaleziono</span>
                )}
              </div>
            </div>
          </div>

          {/* Images Grid */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Aktualne obrazy konta</h2>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">
                  {selectedImages.length > 0 && `${selectedImages.length} wybranych`}
                </span>
                {regularImages.length > 0 && (
                  <>
                    <button
                      onClick={selectAllImages}
                      className="text-blue-600 hover:text-blue-700 text-sm"
                    >
                      Zaznacz wszystkie
                    </button>
                    <button
                      onClick={clearSelection}
                      className="text-gray-600 hover:text-gray-700 text-sm"
                    >
                      Odznacz
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            {selectedImages.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4 p-3 bg-gray-50 rounded-lg">
                <button
                  onClick={handleSetLogo}
                  disabled={selectedImages.length !== 1 || setLogoMutation.isPending}
                  className="bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white px-3 py-1 rounded text-sm"
                >
                  Ustaw jako logo
                </button>
                <button
                  onClick={handleSetFillers}
                  disabled={setFillersMutation.isPending}
                  className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-3 py-1 rounded text-sm"
                >
                  Ustaw jako uzupełniające
                </button>
                <button
                  onClick={handleDeleteSelected}
                  disabled={deleteMutation.isPending}
                  className="bg-red-500 hover:bg-red-600 disabled:bg-gray-400 text-white px-3 py-1 rounded text-sm"
                >
                  Usuń wybrane
                </button>
              </div>
            )}

            {/* Images Grid */}
            {imagesLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                <p className="text-gray-600 mt-2">Ładowanie obrazów...</p>
              </div>
            ) : regularImages.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>Brak obrazów dla tego konta</p>
                <p className="text-sm">Wgraj obrazy używając sekcji powyżej</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {regularImages.map((image) => (
                  <div
                    key={image.id}
                    className={`relative border-2 rounded-lg overflow-hidden cursor-pointer transition-all ${
                      selectedImages.includes(image.id)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => toggleImageSelection(image.id)}
                    onDoubleClick={() => setPreviewImage(image)}
                  >
                    <AuthenticatedImage
                      src={image.url}
                      alt={image.original_filename}
                      className="w-full h-24 object-cover"
                    />
                    <div className="p-2">
                      <p className="text-xs text-gray-600 truncate" title={image.original_filename}>
                        {image.original_filename}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(image.size)}
                      </p>
                    </div>
                    {selectedImages.includes(image.id) && (
                      <div className="absolute top-1 right-1 bg-blue-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs">
                        ✓
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            <p className="text-xs text-gray-500 mt-4">
              Kliknij, aby wybrać obraz • Kliknij dwukrotnie, aby zobaczyć podgląd
            </p>
          </div>
        </>
      )}

      {/* Image Preview Modal */}
      {previewImage && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
          onClick={() => setPreviewImage(null)}
        >
          <div className="bg-white rounded-lg max-w-4xl max-h-full overflow-auto">
            <div className="p-4 border-b">
              <div className="flex items-center justify-between">
                <h3 className="font-medium">{previewImage.original_filename}</h3>
                <button
                  onClick={() => setPreviewImage(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
              <p className="text-sm text-gray-500">
                {formatFileSize(previewImage.size)} • {previewImage.content_type}
              </p>
            </div>
            <div className="p-4">
              <AuthenticatedImage
                src={previewImage.url}
                alt={previewImage.original_filename}
                className="max-w-full max-h-96 mx-auto"
              />
            </div>
          </div>
        </div>
      )}

      {/* Duplicate Resolution Modal */}
      {duplicateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-full overflow-auto">
            <div className="p-4 border-b">
              <h3 className="text-lg font-medium">Resolve Duplicate Filenames</h3>
              <p className="text-sm text-gray-500 mt-1">
                Some files have names that already exist. Please rename them or skip.
              </p>
            </div>
            <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
              {duplicateModal.duplicates.map((duplicate, index) => (
                <div key={index} className="border rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{duplicate.original_filename}</span>
                    {duplicate.is_duplicate && (
                      <span className="text-red-600 text-sm">Duplicate</span>
                    )}
                  </div>
                  
                  {duplicate.is_duplicate && (
                    <div className="space-y-2">
                      <div className="text-sm text-gray-600">
                        A file with this name already exists. Choose a new name:
                      </div>
                      <input
                        type="text"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        defaultValue={duplicate.suggested_filename}
                        onChange={(e) => {
                          setDuplicateModal(prev => {
                            if (!prev) return prev;
                            return {
                              ...prev,
                              filenameOverrides: {
                                ...prev.filenameOverrides,
                                [duplicate.original_filename]: e.target.value
                              }
                            };
                          });
                        }}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div className="p-4 border-t flex justify-end space-x-2">
              <button
                onClick={() => {
                  setDuplicateModal(null);
                  // Reset file input when cancelling
                  if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                  }
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (duplicateModal) {
                    // Set default suggested names for duplicates without custom overrides
                    const finalOverrides = { ...duplicateModal.filenameOverrides };
                    duplicateModal.duplicates.forEach(duplicate => {
                      if (duplicate.is_duplicate && !finalOverrides[duplicate.original_filename]) {
                        finalOverrides[duplicate.original_filename] = duplicate.suggested_filename;
                      }
                    });
                    
                    proceedWithUpload(duplicateModal.files, finalOverrides);
                  }
                }}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
              >
                Upload with Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Images; 