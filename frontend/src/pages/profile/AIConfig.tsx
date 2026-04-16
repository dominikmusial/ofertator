import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input, Label } from '@/components/ui/input';
import { SimpleSelect } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { 
  Loader2, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Info,
  Eye,
  EyeOff,
  Trash2
} from 'lucide-react';
import toast from 'react-hot-toast';
import { 
  useAIProviders, 
  useAIConfigStatus, 
  useAIConfig, 
  useTestAPIKey, 
  useCreateAIConfig, 
  useUpdateAIConfig, 
  useDeleteAIConfig 
} from '../../hooks/shared/ai';

interface AIProvider {
  id: string;
  name: string;
}

interface AIProviderInfo {
  providers: Record<string, AIProvider[]>;
  default_provider: string;
  default_model: string;
}

interface AIConfigStatus {
  has_config: boolean;
  is_active: boolean;
  provider?: string;
  model?: string;
  last_validated?: string;
  can_use_default: boolean;
  default_provider?: string;
  default_model?: string;
}

interface AIConfigResponse {
  id: number;
  ai_provider: string;
  model_name: string;
  is_active: boolean;
  last_validated_at?: string;
  created_at: string;
  updated_at?: string;
}

const AIConfig: React.FC = () => {
  // Use React Query hooks
  const { data: providers, isLoading: providersLoading } = useAIProviders();
  const { data: status, isLoading: statusLoading } = useAIConfigStatus();
  const { data: config, isLoading: configLoading } = useAIConfig();
  
  // Mutations
  const testKeyMutation = useTestAPIKey();
  const createConfigMutation = useCreateAIConfig();
  const updateConfigMutation = useUpdateAIConfig();
  const deleteConfigMutation = useDeleteAIConfig();
  
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [apiKey, setApiKey] = useState<string>('');
  const [showApiKey, setShowApiKey] = useState<boolean>(false);
  
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message?: string;
  } | null>(null);

  // Set initial values when data loads
  useEffect(() => {
    if (providers && status) {
      if (config) {
        setSelectedProvider(config.ai_provider);
        setSelectedModel(config.model_name);
      } else {
        setSelectedProvider(providers.default_provider);
        setSelectedModel(providers.default_model);
      }
    }
  }, [providers, status, config]);

  // Update selected model when provider changes
  useEffect(() => {
    if (providers && selectedProvider) {
      const availableModels = providers.providers[selectedProvider] || [];
      if (availableModels.length > 0 && !availableModels.find(m => m.id === selectedModel)) {
        // If current model is not available for selected provider, choose first available
        setSelectedModel(availableModels[0].id);
      }
    }
  }, [selectedProvider, providers, selectedModel]);

  // Loading state
  const loading = providersLoading || statusLoading || configLoading;

  const testApiKey = async () => {
    if (!selectedProvider || !selectedModel || !apiKey.trim()) {
      toast.error('Wprowadź wszystkie wymagane dane');
      return;
    }

    setTestResult(null);

    testKeyMutation.mutate({
      provider: selectedProvider,
      model_name: selectedModel,
      api_key: apiKey,
    }, {
      onSuccess: (result) => {
        setTestResult({
          success: result.is_valid,
          message: result.error_message
        });
        
        if (result.is_valid) {
          toast.success('Klucz API jest prawidłowy!');
        } else {
          toast.error(`Błąd: ${result.error_message}`);
        }
      },
      onError: (error) => {
        console.error('Error testing API key:', error);
        toast.error('Błąd podczas testowania klucza API');
        setTestResult({
          success: false,
          message: 'Błąd połączenia z serwerem'
        });
      }
    });
  };

  const saveConfig = async () => {
    const isUpdate = status?.has_config && config;
    
    // Check if provider changed (requires new API key)
    const providerChanged = isUpdate && config && config.ai_provider !== selectedProvider;
    
    // API key is required if:
    // 1. Creating new config, OR
    // 2. Provider changed (old key won't work for new provider)
    const apiKeyRequired = !isUpdate || providerChanged;
    
    if (!selectedProvider || !selectedModel || (apiKeyRequired && !apiKey.trim())) {
      if (apiKeyRequired && !apiKey.trim()) {
        toast.error('Klucz API jest wymagany dla wybranego providera');
      } else {
        toast.error('Wprowadź wszystkie wymagane dane');
      }
      return;
    }

    let configData;
    
    if (isUpdate) {
      // Update: optional fields, set is_active to true to activate the config
      configData = {
        ai_provider: selectedProvider,
        model_name: selectedModel,
        is_active: true,
        ...(apiKey.trim() && { api_key: apiKey }) // Only include if provided
      };
    } else {
      // Create: all fields required (is_active set automatically by backend)
      configData = {
        ai_provider: selectedProvider,
        model_name: selectedModel,
        api_key: apiKey
      };
    }

    // Use status.has_config to determine create vs update
    const mutation = isUpdate ? updateConfigMutation : createConfigMutation;
    
    mutation.mutate(configData, {
      onSuccess: () => {
        setApiKey(''); // Clear for security
        toast.success('Konfiguracja AI została zapisana i aktywowana!');
        setTestResult(null); // Clear test result
      },
      onError: (error) => {
        console.error('Error saving config:', error);
        toast.error('Błąd podczas zapisywania konfiguracji');
      }
    });
  };

  const deleteConfig = async () => {
    if (!config) return;

    deleteConfigMutation.mutate(undefined, {
      onSuccess: () => {
        setApiKey('');
        setTestResult(null);
        toast.success('Konfiguracja AI została usunięta');
      },
      onError: (error) => {
        console.error('Error deleting config:', error);
        toast.error('Błąd podczas usuwania konfiguracji');
      }
    });
  };

  const getAvailableModels = () => {
    if (!providers || !selectedProvider) return [];
    return providers.providers[selectedProvider] || [];
  };

  const getModelDisplayName = (modelId: string) => {
    const models = getAvailableModels();
    const model = models.find(m => m.id === modelId);
    return model?.name || modelId;
  };

  const getProviderDisplayName = (providerId: string) => {
    const providerNames: Record<string, string> = {
      anthropic: 'Anthropic Claude',
      google: 'Google Gemini'
    };
    return providerNames[providerId] || providerId;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Ładowanie konfiguracji AI...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Konfiguracja AI</h1>
        <p className="text-gray-600 mt-2">
          Zarządzaj ustawieniami AI dla automatycznego generowania treści ofert
        </p>
      </div>

      {/* Current Active Configuration */}
      {status && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span>Aktywna Konfiguracja AI</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Currently using info */}
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <Info className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="font-medium text-green-900">
                      {status.has_config && status.is_active 
                        ? '✓ Używasz własnego klucza API' 
                        : '✓ Używasz klucza vAutomate (firma)'}
                    </p>
                    <div className="mt-2 text-sm text-green-800 space-y-1">
                      <div>
                        <strong>Provider:</strong>{' '}
                        {status.has_config && status.is_active 
                          ? getProviderDisplayName(status.provider || '') 
                          : (status.default_provider === 'google' ? 'Google Gemini' : 'Anthropic Claude')}
                      </div>
                      <div>
                        <strong>Model:</strong>{' '}
                        {status.has_config && status.is_active 
                          ? getModelDisplayName(status.model || '') 
                          : status.default_model}
                      </div>
                      {status.has_config && status.is_active && status.last_validated && (
                        <div>
                          <strong>Ostatnia walidacja:</strong>{' '}
                          {new Date(status.last_validated).toLocaleString('pl-PL')}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Toggle switch - always visible if user has config and can use default */}
              {status.has_config && status.can_use_default && (
                <div className="p-4 border-2 border-gray-200 rounded-lg bg-white">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <label htmlFor="toggle-source" className="text-base font-semibold text-gray-900 cursor-pointer">
                        Przełącz źródło klucza API
                      </label>
                      <p className="text-sm text-gray-600 mt-1">
                        {status.is_active 
                          ? 'Wyłącz aby użyć darmowego klucza vAutomate'
                          : 'Włącz aby użyć swojego zapisanego klucza API'
                        }
                      </p>
                    </div>
                    <Switch
                      id="toggle-source"
                      checked={status.is_active}
                      disabled={updateConfigMutation.isPending}
                      onCheckedChange={async (checked) => {
                        if (!config) return;
                        try {
                          await updateConfigMutation.mutateAsync({
                            ai_provider: config.ai_provider,
                            model_name: config.model_name,
                            is_active: checked
                          });
                          toast.success(checked ? 'Przełączono na własny klucz' : 'Przełączono na klucz vAutomate');
                        } catch (error) {
                          console.error('Toggle error:', error);
                          toast.error('Błąd podczas przełączania');
                        }
                      }}
                    />
                  </div>
                </div>
              )}

              {/* No access warning */}
              {!status.has_config && !status.can_use_default && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Nie masz dostępu do AI. Dodaj własny klucz API poniżej, aby korzystać z funkcji AI.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Saved Configuration Display */}
      {config && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Twoja Zapisana Konfiguracja</span>
              {!status?.is_active && (
                <Badge variant="secondary">Nieaktywna</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="grid md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                <div>
                  <span className="text-sm text-gray-600">Provider:</span>
                  <p className="font-medium">{getProviderDisplayName(config.ai_provider)}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Model:</span>
                  <p className="font-medium">{getModelDisplayName(config.model_name)}</p>
                </div>
                {config.last_validated_at && (
                  <div className="md:col-span-2">
                    <span className="text-sm text-gray-600">Ostatnia walidacja:</span>
                    <p className="font-medium">{new Date(config.last_validated_at).toLocaleString('pl-PL')}</p>
                  </div>
                )}
              </div>
              
              <div className="flex gap-2">
                <Button
                  onClick={deleteConfig}
                  disabled={deleteConfigMutation.isPending}
                  variant="destructive"
                  size="sm"
                >
                  {deleteConfigMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Usuwanie...
                    </>
                  ) : (
                    <>
                      <Trash2 className="mr-2 h-4 w-4" />
                      Usuń Konfigurację
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configuration Form */}
      <Card>
        <CardHeader>
          <CardTitle>
            {(status?.has_config && config) ? 'Zaktualizuj Swoją Konfigurację' : 'Dodaj Własny Klucz API'}
          </CardTitle>
          <p className="text-sm text-gray-600 mt-2">
            {(status?.has_config && config)
              ? 'Możesz zmienić providera, model lub zaktualizować swój klucz API'
              : 'Skonfiguruj własny klucz API, aby mieć pełną kontrolę nad użyciem AI'}
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Provider Selection */}
          <div className="space-y-2">
            <Label htmlFor="provider">Provider AI</Label>
            <SimpleSelect 
              value={selectedProvider} 
              onValueChange={setSelectedProvider}
              placeholder="Wybierz providera AI"
            >
              {providers && Object.keys(providers.providers).map((providerId) => (
                <option key={providerId} value={providerId}>
                  {getProviderDisplayName(providerId)}
                </option>
              ))}
            </SimpleSelect>
          </div>

          {/* Model Selection */}
          <div className="space-y-2">
            <Label htmlFor="model">Model AI</Label>
            <SimpleSelect 
              value={selectedModel} 
              onValueChange={setSelectedModel}
              disabled={!selectedProvider}
              placeholder="Wybierz model AI"
            >
              {getAvailableModels().map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </SimpleSelect>
            {selectedProvider && providers && selectedModel === providers.default_model && (
              <p className="text-sm text-blue-600">⭐ Model domyślny</p>
            )}
          </div>

          {/* API Key */}
          <div className="space-y-2">
            <Label htmlFor="apiKey">
              Klucz API
              {/* Show optional only if updating AND provider didn't change */}
              {config && config.ai_provider === selectedProvider && (
                <span className="text-gray-500 font-normal ml-2">(opcjonalnie - pozostaw puste aby zachować obecny)</span>
              )}
              {/* Show required asterisk if creating new config OR provider changed */}
              {(!config || config.ai_provider !== selectedProvider) && (
                <span className="text-red-500 ml-1">*</span>
              )}
            </Label>
            
            {/* Warning when provider changed */}
            {config && config.ai_provider !== selectedProvider && (
              <Alert className="border-amber-200 bg-amber-50">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-amber-800 text-sm">
                  Zmieniłeś providera AI. Musisz wprowadzić nowy klucz API dla <strong>{getProviderDisplayName(selectedProvider)}</strong>.
                </AlertDescription>
              </Alert>
            )}
            
            <div className="relative">
              <Input
                id="apiKey"
                type={showApiKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={
                  config && config.ai_provider === selectedProvider
                    ? "Pozostaw puste aby zachować obecny klucz"
                    : "Wprowadź klucz API dla wybranego providera"
                }
                className="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3"
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
            <p className="text-sm text-gray-600">
              {selectedProvider === 'anthropic' && (
                <>Uzyskaj klucz API w <a href="https://console.anthropic.com/" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Anthropic Console</a></>
              )}
              {selectedProvider === 'google' && (
                <>Uzyskaj klucz API w <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Google AI Studio</a></>
              )}
            </p>
          </div>

          {/* Test Result */}
          {testResult && (
            <Alert className={testResult.success ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}>
              {testResult.success ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <XCircle className="h-4 w-4 text-red-600" />
              )}
              <AlertDescription className={testResult.success ? "text-green-800" : "text-red-800"}>
                {testResult.success ? (
                  "Klucz API jest prawidłowy!"
                ) : (
                  `Błąd: ${testResult.message}`
                )}
              </AlertDescription>
            </Alert>
          )}

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={testApiKey}
              disabled={
                testKeyMutation.isPending || 
                !selectedProvider || 
                !selectedModel || 
                !apiKey.trim()
              }
              variant="outline"
            >
              {testKeyMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Testowanie...
                </>
              ) : (
                'Testuj Klucz API'
              )}
            </Button>

            <Button
              onClick={saveConfig}
              disabled={
                createConfigMutation.isPending || 
                updateConfigMutation.isPending || 
                !selectedProvider || 
                !selectedModel || 
                // API key required if: creating new OR provider changed
                ((!config || config.ai_provider !== selectedProvider) && !apiKey.trim())
              }
            >
              {createConfigMutation.isPending || updateConfigMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Zapisywanie...
                </>
              ) : (
                (status?.has_config && config) ? 'Aktualizuj Konfigurację' : 'Zapisz Konfigurację'
              )}
            </Button>
          </div>
          
          {/* Additional Info */}
          <Alert className="border-blue-200 bg-blue-50">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription>
              <div className="space-y-2 text-sm text-blue-900">
                <p><strong>Bezpieczeństwo:</strong></p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li>Klucze API są szyfrowane i bezpiecznie przechowywane</li>
                  <li>Możesz w każdej chwili zaktualizować lub usunąć swoją konfigurację</li>
                </ul>
                {status?.can_use_default && (
                  <>
                    <p className="mt-3"><strong>Przełączanie między kluczami:</strong></p>
                    <ul className="list-disc list-inside space-y-1 ml-2">
                      <li>Po zapisaniu możesz przełączać się między swoim kluczem a kluczem vAutomate</li>
                      <li>Użyj przełącznika na górze strony aby zmienić źródło klucza</li>
                      <li>Twoja konfiguracja zostanie zachowana nawet gdy nie jest aktywna</li>
                    </ul>
                  </>
                )}
              </div>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  );
};

export default AIConfig; 