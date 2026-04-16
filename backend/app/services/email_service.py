import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from typing import Optional, Dict

from app.core.config import settings

class EmailService:
    def __init__(self):
        self.smtp_server = settings.MAIL_SERVER
        self.smtp_port = settings.MAIL_PORT
        self.username = settings.MAIL_USERNAME
        self.password = settings.MAIL_PASSWORD
        self.from_email = settings.MAIL_FROM

    async def send_verification_email(self, to_email: str, token: str, first_name: str = ""):
        verification_url = f"{settings.FRONTEND_URL}/auth/verify/{token}"
        
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Weryfikacja konta Ofertator</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Witaj{% if first_name %} {{ first_name }}{% endif %} w Ofertatorze!</h2>
                <p>Dziękujemy za rejestrację w aplikacji Ofertator. Aby aktywować swoje konto, kliknij przycisk poniżej:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ verification_url }}" 
                       style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Zweryfikuj konto
                    </a>
                </div>
                
                <p>Lub skopiuj i wklej ten link w przeglądarce:</p>
                <p style="background-color: #f3f4f6; padding: 10px; border-radius: 4px; word-break: break-all;">
                    {{ verification_url }}
                </p>
                
                <p><strong>Uwaga:</strong> Link wygasa za 24 godziny.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 14px; color: #6b7280;">
                    Jeśli nie zakładałeś konta w Ofertatorze, zignoruj tę wiadomość.
                </p>
            </div>
        </body>
        </html>
        """)
        
        html_content = template.render(verification_url=verification_url, first_name=first_name)
        await self._send_email(to_email, "Weryfikacja konta Ofertator", html_content)

    async def send_password_reset_email(self, to_email: str, token: str, first_name: str = ""):
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password/{token}"
        
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Reset hasła Ofertator</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #dc2626;">Reset hasła Ofertator</h2>
                <p>Witaj{% if first_name %} {{ first_name }}{% endif %},</p>
                <p>Otrzymaliśmy prośbę o reset hasła do Twojego konta. Kliknij przycisk poniżej, aby ustawić nowe hasło:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ reset_url }}" 
                       style="background-color: #dc2626; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Resetuj hasło
                    </a>
                </div>
                
                <p>Lub skopiuj i wklej ten link w przeglądarce:</p>
                <p style="background-color: #f3f4f6; padding: 10px; border-radius: 4px; word-break: break-all;">
                    {{ reset_url }}
                </p>
                
                <p><strong>Uwaga:</strong> Link wygasa za 1 godzinę.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 14px; color: #6b7280;">
                    Jeśli nie prosiłeś o reset hasła, zignoruj tę wiadomość. Twoje hasło pozostanie bez zmian.
                </p>
            </div>
        </body>
        </html>
        """)
        
        html_content = template.render(reset_url=reset_url, first_name=first_name)
        await self._send_email(to_email, "Reset hasła Ofertator", html_content)

    async def send_admin_new_registration_email(self, admin_email: str, user_first_name: str, user_last_name: str, user_email: str, registration_date: str):
        """Send notification to admin about new user registration"""
        
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Nowa rejestracja - Ofertator</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #f59e0b;">🔔 Nowa rejestracja w Ofertator</h2>
                <p>Witaj Administrator,</p>
                <p>Nowy użytkownik zarejestrował się w systemie Ofertator i oczekuje na zatwierdzenie konta.</p>
                
                <div style="background-color: #fef3c7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #92400e; margin-top: 0;">Dane użytkownika:</h3>
                    <p><strong>Imię i nazwisko:</strong> {{ user_first_name }} {{ user_last_name }}</p>
                    <p><strong>Adres email:</strong> {{ user_email }}</p>
                    <p><strong>Data rejestracji:</strong> {{ registration_date }}</p>
                </div>
                
                <p>Aby zatwierdzić lub odrzucić rejestrację, zaloguj się do panelu administratora Ofertatora.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ admin_panel_url }}" 
                       style="background-color: #f59e0b; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Przejdź do panelu administratora
                    </a>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 14px; color: #6b7280;">
                    Ten email został wysłany automatycznie z systemu Ofertator.<br>
                    Jeśli nie jesteś administratorem, skontaktuj się z zespołem wsparcia.
                </p>
            </div>
        </body>
        </html>
        """)
        
        admin_panel_url = f"{settings.FRONTEND_URL}/admin/users"
        html_content = template.render(
            user_first_name=user_first_name,
            user_last_name=user_last_name,
            user_email=user_email,
            registration_date=registration_date,
            admin_panel_url=admin_panel_url
        )
        await self._send_email(admin_email, "Nowa rejestracja - Ofertator", html_content)

    async def send_user_approval_email(self, to_email: str, first_name: str = ""):
        """Send approval confirmation to user"""
        
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Konto zatwierdzone - Ofertator</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #10b981;">✅ Konto zatwierdzone!</h2>
                <p>Witaj{% if first_name %} {{ first_name }}{% endif %},</p>
                <p>Miamy przyjemność poinformować Cię, że Twoje konto w systemie Ofertator zostało zatwierdzone przez administratora.</p>
                
                <div style="background-color: #d1fae5; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #10b981;">
                    <p style="margin: 0;"><strong>🎉 Gratulacje! Możesz teraz korzystać z Ofertatora.</strong></p>
                </div>
                
                <p>Teraz możesz:</p>
                <ul>
                    <li>Zalogować się do systemu</li>
                    <li>Dodać swoje konta</li>
                    <li>Korzystać z wszystkich narzędzi do zarządzania ofertami</li>
                    <li>Tworzyć i używać szablonów</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ login_url }}" 
                       style="background-color: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Zaloguj się do Ofertatora
                    </a>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 14px; color: #6b7280;">
                    Jeśli masz jakiekolwiek pytania, skontaktuj się z naszym zespołem wsparcia.
                </p>
            </div>
        </body>
        </html>
        """)
        
        login_url = f"{settings.FRONTEND_URL}/auth/login"
        html_content = template.render(
            first_name=first_name,
            login_url=login_url
        )
        await self._send_email(to_email, "Konto zatwierdzone - Ofertator", html_content)

    async def send_user_rejection_email(self, to_email: str, first_name: str = "", rejection_reason: str = ""):
        """Send rejection notification to user"""
        
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Rejestracja odrzucona - Ofertator</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #dc2626;">❌ Rejestracja odrzucona</h2>
                <p>Witaj{% if first_name %} {{ first_name }}{% endif %},</p>
                <p>Niestety, Twoja rejestracja w systemie Ofertator została odrzucona przez administratora.</p>
                
                {% if rejection_reason %}
                <div style="background-color: #fee2e2; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc2626;">
                    <p style="margin: 0;"><strong>Powód odrzucenia:</strong></p>
                    <p style="margin: 5px 0 0 0;">{{ rejection_reason }}</p>
                </div>
                {% endif %}
                
                <p>Twoje dane zostały usunięte z naszego systemu. Jeśli uważasz, że jest to pomyłka, możesz:</p>
                <ul>
                    <li>Skontaktować się z zespołem wsparcia</li>
                    <li>Spróbować zarejestrować się ponownie z poprawnymi danymi</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ support_url }}" 
                       style="background-color: #6b7280; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Kontakt z wsparciem
                    </a>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 14px; color: #6b7280;">
                    Dziękujemy za zrozumienie.<br>
                    Zespół Ofertator
                </p>
            </div>
        </body>
        </html>
        """)
        
        support_url = f"{settings.FRONTEND_URL}/contact"  # Assuming there's a contact page
        html_content = template.render(
            first_name=first_name,
            rejection_reason=rejection_reason,
            support_url=support_url
        )
        await self._send_email(to_email, "Rejestracja odrzucona - Ofertator", html_content)

    async def send_user_deactivation_email(self, to_email: str, first_name: str = "", reason: str = "", admin_email: str = ""):
        """Send deactivation notification email to user"""
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Konto zostało dezaktywowane - Ofertator</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #f59e0b;">⚠️ Konto zostało dezaktywowane</h2>
                <p>Witaj{% if first_name %} {{ first_name }}{% endif %},</p>
                <p>Informujemy, że Twoje konto w systemie Ofertator zostało <strong>tymczasowo dezaktywowane</strong> przez administratora.</p>
                
                {% if reason %}
                <div style="background-color: #fef3c7; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                    <p style="margin: 0;"><strong>Powód dezaktywacji:</strong></p>
                    <p style="margin: 5px 0 0 0;">{{ reason }}</p>
                </div>
                {% endif %}
                
                <p><strong>Co to oznacza?</strong></p>
                <ul>
                    <li>Nie możesz się zalogować do systemu</li>
                    <li>Twoje dane pozostają nienaruszone</li>
                    <li>Dezaktywacja może zostać cofnięta przez administratora</li>
                </ul>
                
                <p><strong>Co dalej?</strong></p>
                <p>Jeśli uważasz, że dezaktywacja nastąpiła przez pomyłkę lub masz pytania, skontaktuj się z administratorem:</p>
                
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Kontakt z administratorem:</strong></p>
                    <p style="margin: 5px 0 0 0;">{{ admin_email }}</p>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 14px; color: #6b7280;">
                    Dziękujemy za zrozumienie.<br>
                    Zespół Ofertator
                </p>
            </div>
        </body>
        </html>
        """)
        
        html_content = template.render(
            first_name=first_name,
            reason=reason,
            admin_email=admin_email
        )
        await self._send_email(to_email, "Konto zostało dezaktywowane - Ofertator", html_content)

    async def send_user_reactivation_email(self, to_email: str, first_name: str = "", admin_email: str = ""):
        """Send reactivation notification email to user"""
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Konto zostało przywrócone - Ofertator</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #10b981;">✅ Konto zostało przywrócone</h2>
                <p>Witaj{% if first_name %} {{ first_name }}{% endif %},</p>
                <p><strong>Dobra wiadomość!</strong> Twoje konto w systemie Ofertator zostało przywrócone przez administratora.</p>
                
                <div style="background-color: #d1fae5; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #10b981;">
                    <p style="margin: 0;"><strong>Status konta:</strong> Aktywne</p>
                    <p style="margin: 5px 0 0 0;">Możesz się ponownie zalogować do systemu</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ login_url }}" 
                       style="background-color: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Zaloguj się do systemu
                    </a>
                </div>
                
                <p>Jeśli masz pytania, skontaktuj się z administratorem:</p>
                <p style="background-color: #f3f4f6; padding: 10px; border-radius: 4px;">
                    <strong>Kontakt:</strong> {{ admin_email }}
                </p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 14px; color: #6b7280;">
                    Miło Cię z powrotem widzieć!<br>
                    Zespół Ofertator
                </p>
            </div>
        </body>
        </html>
        """)
        
        login_url = f"{settings.FRONTEND_URL}/auth/login"
        html_content = template.render(
            first_name=first_name,
            admin_email=admin_email,
            login_url=login_url
        )
        await self._send_email(to_email, "Konto zostało przywrócone - Ofertator", html_content)

    async def send_user_deletion_email(self, to_email: str, first_name: str = "", reason: str = "", admin_email: str = ""):
        """Send deletion notification email to user"""
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Konto zostało usunięte - Ofertator</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-line: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #dc2626;">🔒 Konto zostało usunięte</h2>
                <p>Witaj{% if first_name %} {{ first_name }}{% endif %},</p>
                <p>Informujemy, że Twoje konto w systemie Ofertator zostało <strong>trwale usunięte</strong> przez administratora.</p>
                
                {% if reason %}
                <div style="background-color: #fee2e2; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc2626;">
                    <p style="margin: 0;"><strong>Powód usunięcia:</strong></p>
                    <p style="margin: 5px 0 0 0;">{{ reason }}</p>
                </div>
                {% endif %}
                
                <p><strong>Co to oznacza?</strong></p>
                <ul>
                    <li>Twoje konto zostało trwale usunięte</li>
                    <li>Nie możesz się już zalogować do systemu</li>
                    <li>Twoje dane zostały usunięte zgodnie z polityką prywatności</li>
                    <li>Operacja jest nieodwracalna</li>
                </ul>
                
                <div style="background-color: #f9fafb; padding: 15px; border-radius: 5px; margin: 20px 0; border: 1px solid #e5e7eb;">
                    <p style="margin: 0;"><strong>Dane analityczne:</strong></p>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">Twoje dane analityczne (statystyki użycia AI) zostały zarchiwizowane w celach sprawozdawczych, ale nie zawierają informacji osobowych.</p>
                </div>
                
                <p>Jeśli uważasz, że usunięcie nastąpiło przez pomyłkę lub masz pytania, możesz skontaktować się z administratorem:</p>
                
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Kontakt z administratorem:</strong></p>
                    <p style="margin: 5px 0 0 0;">{{ admin_email }}</p>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 14px; color: #6b7280;">
                    Dziękujemy za korzystanie z naszego systemu.<br>
                    Zespół Ofertator
                </p>
            </div>
        </body>
        </html>
        """)
        
        html_content = template.render(
            first_name=first_name,
            reason=reason,
            admin_email=admin_email
        )
        await self._send_email(to_email, "Konto zostało usunięte - Ofertator", html_content)

    # Admin notification emails for user management actions
    async def send_admin_user_deactivated_email(self, to_email: str, user_first_name: str, user_last_name: str, 
                                               user_email: str, reason: str, admin_email: str):
        """Send notification to admin about user deactivation"""
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Użytkownik został dezaktywowany - Ofertator</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #f59e0b;">⚠️ Użytkownik został dezaktywowany</h2>
                
                <div style="background-color: #fef3c7; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                    <p style="margin: 0;"><strong>Akcja:</strong> Dezaktywacja użytkownika</p>
                    <p style="margin: 5px 0 0 0;"><strong>Status:</strong> Wykonana pomyślnie</p>
                </div>
                
                <h3>Szczegóły użytkownika:</h3>
                <ul>
                    <li><strong>Imię i nazwisko:</strong> {{ user_first_name }} {{ user_last_name }}</li>
                    <li><strong>Email:</strong> {{ user_email }}</li>
                    <li><strong>Powód dezaktywacji:</strong> {{ reason }}</li>
                    <li><strong>Administrator wykonujący:</strong> {{ admin_email }}</li>
                    <li><strong>Data dezaktywacji:</strong> {{ current_time }}</li>
                </ul>
                
                <p><strong>Konsekwencje dezaktywacji:</strong></p>
                <ul>
                    <li>Użytkownik nie może się zalogować do systemu</li>
                    <li>Wszystkie dane użytkownika pozostają nienaruszone</li>
                    <li>Operacja jest odwracalna przez administratora</li>
                    <li>Użytkownik otrzymał powiadomienie email</li>
                </ul>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 14px; color: #6b7280;">
                    To jest automatyczne powiadomienie z systemu Ofertator.
                </p>
            </div>
        </body>
        </html>
        """)
        
        from datetime import datetime
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        html_content = template.render(
            user_first_name=user_first_name,
            user_last_name=user_last_name,
            user_email=user_email,
            reason=reason,
            admin_email=admin_email,
            current_time=current_time
        )
        await self._send_email(to_email, "Użytkownik został dezaktywowany - Ofertator", html_content)

    async def send_admin_user_reactivated_email(self, to_email: str, user_first_name: str, user_last_name: str,
                                              user_email: str, admin_email: str):
        """Send notification to admin about user reactivation"""
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Użytkownik został przywrócony - Ofertator</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #10b981;">✅ Użytkownik został przywrócony</h2>
                
                <div style="background-color: #d1fae5; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #10b981;">
                    <p style="margin: 0;"><strong>Akcja:</strong> Przywrócenie użytkownika</p>
                    <p style="margin: 5px 0 0 0;"><strong>Status:</strong> Wykonana pomyślnie</p>
                </div>
                
                <h3>Szczegóły użytkownika:</h3>
                <ul>
                    <li><strong>Imię i nazwisko:</strong> {{ user_first_name }} {{ user_last_name }}</li>
                    <li><strong>Email:</strong> {{ user_email }}</li>
                    <li><strong>Administrator wykonujący:</strong> {{ admin_email }}</li>
                    <li><strong>Data przywrócenia:</strong> {{ current_time }}</li>
                </ul>
                
                <p><strong>Konsekwencje przywrócenia:</strong></p>
                <ul>
                    <li>Użytkownik może się ponownie zalogować do systemu</li>
                    <li>Wszystkie dane użytkownika pozostały nienaruszone</li>
                    <li>Przywrócone zostały wszystkie uprawnienia</li>
                    <li>Użytkownik otrzymał powiadomienie email</li>
                </ul>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 14px; color: #6b7280;">
                    To jest automatyczne powiadomienie z systemu Ofertator.
                </p>
            </div>
        </body>
        </html>
        """)
        
        from datetime import datetime
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        html_content = template.render(
            user_first_name=user_first_name,
            user_last_name=user_last_name,
            user_email=user_email,
            admin_email=admin_email,
            current_time=current_time
        )
        await self._send_email(to_email, "Użytkownik został przywrócony - Ofertator", html_content)

    async def send_admin_user_deleted_email(self, to_email: str, user_first_name: str, user_last_name: str,
                                           user_email: str, user_type: str, reason: str, admin_email: str,
                                           transferred_data: Optional[Dict] = None):
        """Send notification to admin about user deletion"""
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Użytkownik został usunięty - Ofertator</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #dc2626;">🗑️ Użytkownik został usunięty</h2>
                
                <div style="background-color: #fee2e2; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc2626;">
                    <p style="margin: 0;"><strong>Akcja:</strong> Trwałe usunięcie użytkownika</p>
                    <p style="margin: 5px 0 0 0;"><strong>Status:</strong> Wykonana pomyślnie</p>
                </div>
                
                <h3>Szczegóły użytkownika:</h3>
                <ul>
                    <li><strong>Imię i nazwisko:</strong> {{ user_first_name }} {{ user_last_name }}</li>
                    <li><strong>Email:</strong> {{ user_email }}</li>
                    <li><strong>Typ użytkownika:</strong> {{ user_type }}</li>
                    <li><strong>Powód usunięcia:</strong> {{ reason }}</li>
                    <li><strong>Administrator wykonujący:</strong> {{ admin_email }}</li>
                    <li><strong>Data usunięcia:</strong> {{ current_time }}</li>
                </ul>
                
                {% if transferred_data %}
                <h3>Przeniesione dane:</h3>
                <div style="background-color: #f0f9ff; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #0284c7;">
                    <p style="margin: 0;"><strong>Następujące dane zostały przeniesione do administratora:</strong></p>
                    <ul style="margin: 10px 0 0 0;">
                        <li>Konta: {{ transferred_data.accounts or 0 }}</li>
                        <li>Szablony: {{ transferred_data.templates or 0 }}</li>
                        <li>Zdjęcia: {{ transferred_data.images or 0 }}</li>
                    </ul>
                </div>
                {% endif %}
                
                <p><strong>Konsekwencje usunięcia:</strong></p>
                <ul>
                    <li>Konto użytkownika zostało trwale usunięte</li>
                    <li>Dane analityczne zostały zarchiwizowane</li>
                    {% if transferred_data %}
                    <li>Wybrane dane zostały przeniesione do administratora</li>
                    {% else %}
                    <li>Wszystkie dane użytkownika zostały usunięte</li>
                    {% endif %}
                    <li>Operacja jest nieodwracalna</li>
                    <li>Użytkownik otrzymał powiadomienie email</li>
                </ul>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 14px; color: #6b7280;">
                    To jest automatyczne powiadomienie z systemu Ofertator.
                </p>
            </div>
        </body>
        </html>
        """)
        
        from datetime import datetime
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        html_content = template.render(
            user_first_name=user_first_name,
            user_last_name=user_last_name,
            user_email=user_email,
            user_type=user_type,
            reason=reason,
            admin_email=admin_email,
            current_time=current_time,
            transferred_data=transferred_data
        )
        await self._send_email(to_email, "Użytkownik został usunięty - Ofertator", html_content)

    async def send_admin_created_user_email(self, to_email: str, user_name: str, email: str, password: str):
        """
        Send welcome email with credentials to admin-created user.
        """
        login_url = f"{settings.FRONTEND_URL}/auth/login"
        
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Witaj w Ofertatorze</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Witaj {{ user_name }} w Ofertatorze!</h2>
                <p>Twoje konto zostało utworzone przez administratora.</p>
                
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #1f2937;">Dane logowania:</h3>
                    <p style="margin: 10px 0;">
                        <strong>Email:</strong> {{ email }}
                    </p>
                    <p style="margin: 10px 0;">
                        <strong>Hasło:</strong> <code style="background-color: #e5e7eb; padding: 4px 8px; border-radius: 4px;">{{ password }}</code>
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ login_url }}" 
                       style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Zaloguj się
                    </a>
                </div>
                
                <p><strong>Zalecenia bezpieczeństwa:</strong></p>
                <ul>
                    <li>Zapisz te dane w bezpiecznym miejscu</li>
                    <li>Nie udostępniaj hasła nikomu</li>
                    <li>Możesz zmienić hasło po zalogowaniu w ustawieniach profilu</li>
                </ul>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 14px; color: #6b7280;">
                    Jeśli masz pytania, skontaktuj się z administratorem.
                </p>
            </div>
        </body>
        </html>
        """)
        
        html_content = template.render(
            user_name=user_name,
            email=email,
            password=password,
            login_url=login_url
        )
        await self._send_email(to_email, "Witaj w Ofertatorze - Dane logowania", html_content)

    async def _send_email(self, to_email: str, subject: str, html_content: str):
        """Send email using SMTP in async manner"""
        def send_sync():
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            try:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    if settings.MAIL_USE_TLS:
                        server.starttls()
                    if self.username and self.password:
                        server.login(self.username, self.password)
                    server.send_message(msg)
                return True
            except Exception as e:
                print(f"Failed to send email to {to_email}: {str(e)}")
                return False
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, send_sync)

# Singleton instance
email_service = EmailService() 