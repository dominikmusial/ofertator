import React from 'react';
import classNames from 'classnames';

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  variant?: 'default' | 'destructive' | 'warning' | 'success';
}

export const Alert: React.FC<AlertProps> = ({ 
  children, 
  className, 
  variant = 'default',
  ...props 
}) => {
  const variantClasses = {
    default: "bg-blue-50 border-blue-200 text-blue-900",
    destructive: "bg-red-50 border-red-200 text-red-900",
    warning: "bg-yellow-50 border-yellow-200 text-yellow-900",
    success: "bg-green-50 border-green-200 text-green-900"
  };

  return (
    <div 
      className={classNames(
        "relative w-full rounded-lg border px-4 py-3",
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

interface AlertDescriptionProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export const AlertDescription: React.FC<AlertDescriptionProps> = ({ 
  children, 
  className, 
  ...props 
}) => {
  return (
    <div 
      className={classNames(
        "text-sm [&_p]:leading-relaxed",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}; 