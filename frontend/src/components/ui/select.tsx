import React, { useState, createContext, useContext } from 'react';
import classNames from 'classnames';
import { ChevronDown } from 'lucide-react';

interface SelectContextValue {
  value?: string;
  onValueChange?: (value: string) => void;
  disabled?: boolean;
}

const SelectContext = createContext<SelectContextValue>({});

interface SelectProps {
  children: React.ReactNode;
  value?: string;
  onValueChange?: (value: string) => void;
  disabled?: boolean;
}

export const Select: React.FC<SelectProps> = ({ children, value, onValueChange, disabled }) => {
  return (
    <SelectContext.Provider value={{ value, onValueChange, disabled }}>
      <div className="relative">
        {children}
      </div>
    </SelectContext.Provider>
  );
};

interface SelectTriggerProps extends React.HTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

export const SelectTrigger: React.FC<SelectTriggerProps> = ({ children, className, ...props }) => {
  const { disabled } = useContext(SelectContext);
  
  return (
    <button
      type="button"
      className={classNames(
        "flex w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm",
        "placeholder:text-gray-400",
        "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      disabled={disabled}
      {...props}
    >
      <span className="block truncate">{children}</span>
      <ChevronDown className="h-4 w-4 opacity-50" aria-hidden="true" />
    </button>
  );
};

interface SelectValueProps {
  placeholder?: string;
}

export const SelectValue: React.FC<SelectValueProps> = ({ placeholder }) => {
  const { value } = useContext(SelectContext);
  
  return (
    <span className={classNames(
      value ? "text-gray-900" : "text-gray-400"
    )}>
      {value || placeholder}
    </span>
  );
};

interface SelectContentProps {
  children: React.ReactNode;
}

export const SelectContent: React.FC<SelectContentProps> = ({ children }) => {
  // For simplicity, we'll render this as a native select overlay
  // In a real implementation, you'd want a proper dropdown
  return (
    <div className="hidden">
      {children}
    </div>
  );
};

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
  onSelect?: () => void;
}

export const SelectItem: React.FC<SelectItemProps> = ({ value, children, onSelect }) => {
  const { onValueChange } = useContext(SelectContext);
  
  const handleSelect = () => {
    onValueChange?.(value);
    onSelect?.();
  };
  
  return (
    <button
      type="button"
      className="block w-full px-3 py-2 text-left text-sm hover:bg-gray-100"
      onClick={handleSelect}
    >
      {children}
    </button>
  );
};

// Simple native select implementation for now
interface SimpleSelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  children: React.ReactNode;
  className?: string;
}

export const SimpleSelect: React.FC<SimpleSelectProps> = ({ 
  value, 
  onValueChange, 
  disabled, 
  placeholder,
  children,
  className 
}) => {
  return (
    <select
      value={value || ''}
      onChange={(e) => onValueChange?.(e.target.value)}
      disabled={disabled}
      className={classNames(
        "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm",
        "bg-white text-gray-900",
        "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
        "disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50",
        className
      )}
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {children}
    </select>
  );
}; 