import React from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { AlertTriangle, RefreshCw, ArrowLeft, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

const AuthError: React.FC = () => {
  const [searchParams] = useSearchParams();
  const reason = searchParams.get('reason');

  const errorMessages: Record<string, {
    title: string;
    message: string;
    action?: string;
    actionLink?: string;
    showRetry?: boolean;
  }> = {
    'token_expired': {
      title: 'Link wygasł',
      message: 'Link z Asystentów AI wygasł (ważny przez 5 minut). Spróbuj ponownie z aplikacji Asystentów AI.',
      action: 'Przejdź do Asystentów AI',
      actionLink: 'https://vsprint.pl/modelegpt/asystenciai/login.php',
      showRetry: true
    },
    'email_exists': {
      title: 'Konto już istnieje',
      message: 'Konto z tym adresem email już istnieje w Ofertatorze. Zaloguj się normalnie lub użyj funkcji resetowania hasła.',
      action: 'Przejdź do logowania',
      actionLink: '/login'
    },
    'invalid_token': {
      title: 'Nieprawidłowy link',
      message: 'Link transferu jest nieprawidłowy lub został uszkodzony. Upewnij się, że skopiowałeś cały link z Asystentów AI.',
      action: 'Spróbuj ponownie',
      actionLink: 'https://vsprint.pl/modelegpt/asystenciai/login.php',
      showRetry: true
    },
    'invalid_user_data': {
      title: 'Nieprawidłowe dane użytkownika',
      message: 'Twoje konto w Asystentach AI nie spełnia wymagań do transferu. Upewnij się, że email jest zweryfikowany i regulamin zaakceptowany.',
      action: 'Sprawdź ustawienia konta',
      actionLink: 'https://vsprint.pl/modelegpt/asystenciai/login.php'
    },
    'server_error': {
      title: 'Błąd serwera',
      message: 'Wystąpił nieoczekiwany błąd serwera. Spróbuj ponownie za chwilę lub skontaktuj się z pomocą techniczną.',
      showRetry: true
    },
    'setup_incomplete': {
      title: 'Konfiguracja nie została dokończona',
      message: 'Proces konfiguracji konta został przerwany. Spróbuj ponownie z aplikacji Asystentów AI.',
      action: 'Spróbuj ponownie',
      actionLink: 'https://vsprint.pl/modelegpt/asystenciai/login.php'
    }
  };

  const errorInfo = errorMessages[reason || 'unknown'] || {
    title: 'Nieoczekiwany błąd',
    message: 'Wystąpił nieoczekiwany błąd podczas transferu konta. Spróbuj ponownie lub skontaktuj się z pomocą techniczną.',
    showRetry: true
  };

  const handleRetry = () => {
    // Go back to asystenciai
    window.location.href = 'https://vsprint.pl/modelegpt/asystenciai/login.php';
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <AlertTriangle className="mx-auto h-12 w-12 text-red-500" />
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Problem z transferem konta
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Wystąpił problem podczas łączenia z Asystentami AI
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              {errorInfo.title}
            </CardTitle>
            <CardDescription>
              {errorInfo.message}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            
            {reason === 'token_expired' && (
              <Alert>
                <RefreshCw className="h-4 w-4" />
                <AlertDescription>
                  Tokeny transferu wygasają po 5 minutach ze względów bezpieczeństwa. 
                  To normalne zachowanie systemu.
                </AlertDescription>
              </Alert>
            )}

            {reason === 'email_exists' && (
              <Alert>
                <Mail className="h-4 w-4" />
                <AlertDescription>
                  Jeśli to Twoje konto, możesz zalogować się normalnie. 
                  Jeśli zapomniałeś hasła, użyj funkcji resetowania hasła.
                </AlertDescription>
              </Alert>
            )}

            <div className="flex flex-col gap-3">
              {errorInfo.actionLink && (
                <Button 
                  className="w-full"
                  variant={errorInfo.showRetry ? "default" : "default"}
                >
                  {errorInfo.actionLink.startsWith('http') ? (
                    <a href={errorInfo.actionLink} target="_blank" rel="noopener noreferrer">
                      {errorInfo.action}
                    </a>
                  ) : (
                    <Link to={errorInfo.actionLink}>
                      {errorInfo.action}
                    </Link>
                  )}
                </Button>
              )}

              {errorInfo.showRetry && !errorInfo.actionLink && (
                <Button onClick={handleRetry} className="w-full">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Spróbuj ponownie
                </Button>
              )}

              <Button variant="outline" className="w-full">
                <Link to="/login" className="flex items-center justify-center gap-2">
                  <ArrowLeft className="w-4 h-4" />
                  Przejdź do logowania
                </Link>
              </Button>
            </div>

            <div className="pt-4 border-t text-center">
              <p className="text-xs text-gray-500">
                Problemy z integracją? Skontaktuj się z pomocą techniczną
              </p>
              <Button variant="outline" size="sm" className="text-xs">
                <a href="mailto:igor@vautomate.pl">
                  igor@vautomate.pl
                </a>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AuthError;
