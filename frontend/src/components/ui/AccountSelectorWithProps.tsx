import React from 'react';

interface Account {
  id: number;
  nazwa_konta: string;
}

interface AccountSelectorProps {
  accounts: Account[];
  selectedAccountId: number | null;
  onAccountSelect: (accountId: number | null) => void;
  loading: boolean;
}

const AccountSelectorWithProps: React.FC<AccountSelectorProps> = ({
  accounts,
  selectedAccountId,
  onAccountSelect,
  loading
}) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Wybierz konto:
      </label>
      <select
        className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        disabled={loading}
        value={selectedAccountId || ''}
        onChange={(e) => {
          const value = e.target.value;
          onAccountSelect(value ? Number(value) : null);
        }}
      >
        <option value="">
          {loading ? 'Ładowanie kont...' : 'Wybierz konto'}
        </option>
        {accounts.map((account) => (
          <option key={account.id} value={account.id}>
            {account.nazwa_konta}
          </option>
        ))}
      </select>
      {!loading && accounts.length === 0 && (
        <p className="mt-2 text-sm text-gray-500">
          Brak dostępnych kont. Dodaj konto w sekcji "Konta".
        </p>
      )}
    </div>
  );
};

export default AccountSelectorWithProps; 