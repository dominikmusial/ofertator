import React from 'react';
import classNames from 'classnames';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export const Input: React.FC<InputProps> = ({ className, ...props }) => {
  return (
    <input 
      className={classNames(
        "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm",
        "placeholder-gray-400",
        "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
        "disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50",
        className
      )}
      {...props}
    />
  );
};

interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  children: React.ReactNode;
}

export const Label: React.FC<LabelProps> = ({ children, className, ...props }) => {
  return (
    <label 
      className={classNames(
        "block text-sm font-medium text-gray-700",
        className
      )}
      {...props}
    >
      {children}
    </label>
  );
}; 