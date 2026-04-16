import React, { useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { CheckCircle, ArrowRight } from 'lucide-react';
import { useToastStore } from '../../store/toastStore';
import { useAuthStore } from '../../store/authStore';

const AuthSuccess: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { addToast } = useToastStore();
  const { setTokens } = useAuthStore();
  const hasShownToast = useRef(false);

  useEffect(() => {
    const accessToken = searchParams.get('access_token');
    const refreshToken = searchParams.get('refresh_token');
    
    if (accessToken && refreshToken) {
      // Store tokens and update auth state
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
      setTokens(accessToken, refreshToken);

      // Show toast only once and redirect immediately
      if (!hasShownToast.current) {
        hasShownToast.current = true;
        addToast("Witamy w Ofertatorze! Zostałeś pomyślnie zalogowany z konta Asystentów AI.", "success");
        
        // Redirect immediately - toast will persist
        navigate('/titles', { replace: true });
      }
    } else {
      // No tokens provided, redirect to error
      navigate('/auth/error?reason=invalid_token', { replace: true });
    }
  }, [searchParams, navigate, addToast, setTokens]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Logowanie pomyślne!
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Zostałeś pomyślnie zalogowany z Asystentów AI
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10 text-center">
          <div className="space-y-4">
            <div className="animate-pulse">
              <div className="flex items-center justify-center space-x-2">
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
            
            <p className="text-gray-600">
              Przekierowywanie do modułu Tytuły...
            </p>
            
            <div className="flex items-center justify-center text-sm text-gray-500">
              <ArrowRight className="w-4 h-4 mr-1" />
              Za chwilę będziesz mógł zarządzać tytułami ofert
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthSuccess;
