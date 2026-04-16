import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../../lib/api';
import { useAuthStore } from '../../../../store/authStore';

export interface AccountWithOwnership {
  id: number;
  nazwa_konta: string;
  access_token: string;
  refresh_token: string;
  token_expires_at: string;
  refresh_token_expires_at?: string;
  needs_reauth?: boolean;
  marketplace_type?: string;
  marketplace_specific_data?: any;
  created_at: string;
  updated_at: string;
  is_owner: boolean;
  shared_with_vsprint: boolean;
}

export function useSharedAccounts() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  // Check if user is vsprint employee or admin
  const isVsprintEmployee = user?.role === 'vsprint_employee' || user?.role === 'admin';

  // Determine which endpoint to use based on user role
  const getAccountsEndpoint = () => {
    if (isVsprintEmployee) {
      return '/allegro/shared-accounts';
    } else {
      return '/accounts/';
    }
  };

  // Use React Query for fetching accounts
  const {
    data,
    isLoading,
    error,
    refetch: fetchSharedAccounts
  } = useQuery<AccountWithOwnership[]>({
    queryKey: ['shared-accounts', user?.id, user?.role],
    queryFn: async () => {
      const endpoint = getAccountsEndpoint();
      const response = await api.get(endpoint);
      return response.data;
    },
    enabled: !!user,
    staleTime: 30000, // Cache for 30 seconds
    gcTime: 300000, // Keep in cache for 5 minutes (renamed from cacheTime in v5)
  });

  const accounts: AccountWithOwnership[] = data ?? [];

  // Refresh token mutation
  const refreshTokenMutation = useMutation({
    mutationFn: async (accountId: number) => {
      const response = await api.post(`/allegro/refresh-token/${accountId}`);
      return response.data;
    },
    onSuccess: (updatedAccount) => {
      // Update the account in the cache
      queryClient.setQueryData<AccountWithOwnership[]>(
        ['shared-accounts', user?.id, user?.role],
        (oldData) => {
          if (!oldData) return oldData;
          return oldData.map(acc => 
            acc.id === updatedAccount.id ? updatedAccount : acc
          );
        }
      );
    }
  });

  // Delete account mutation
  const deleteAccountMutation = useMutation({
    mutationFn: async (accountId: number) => {
      await api.delete(`/accounts/${accountId}`);
      return accountId;
    },
    onSuccess: (deletedAccountId) => {
      // Remove the account from the cache
      queryClient.setQueryData<AccountWithOwnership[]>(
        ['shared-accounts', user?.id, user?.role],
        (oldData) => {
          if (!oldData) return oldData;
          return oldData.filter(acc => acc.id !== deletedAccountId);
        }
      );
    }
  });

  // Refresh token for account
  const refreshAccountToken = async (accountId: number): Promise<boolean> => {
    try {
      await refreshTokenMutation.mutateAsync(accountId);
      return true;
    } catch (err: any) {
      console.error('Failed to refresh token:', err);
      return false;
    }
  };

  // Delete account (only for owners)
  const deleteAccount = async (accountId: number): Promise<boolean> => {
    try {
      await deleteAccountMutation.mutateAsync(accountId);
      return true;
    } catch (err: any) {
      console.error('Failed to delete account:', err);
      return false;
    }
  };

  // Get accounts that are about to expire
  const getExpiringAccounts = (daysThreshold = 7): AccountWithOwnership[] => {
    const threshold = new Date();
    threshold.setDate(threshold.getDate() + daysThreshold);
    
    return accounts.filter(account => {
      const expiresAt = new Date(account.token_expires_at);
      return expiresAt <= threshold;
    });
  };

  // Get owned accounts
  const getOwnedAccounts = (): AccountWithOwnership[] => {
    return accounts.filter(account => account.is_owner);
  };

  // Get shared accounts - only relevant for vsprint employees
  const getSharedAccounts = (): AccountWithOwnership[] => {
    if (!isVsprintEmployee) {
      return []; // Regular users don't have shared accounts concept
    }
    // For vsprint employees: accounts shared by other team members
    return accounts.filter(account => !account.is_owner && account.shared_with_vsprint);
  };

  // Get team shared accounts (for vsprint employees only)
  const getAccountsSharedWithTeam = (): AccountWithOwnership[] => {
    if (!isVsprintEmployee) {
      return []; // Regular users don't have team sharing concept
    }
    return accounts.filter(account => account.shared_with_vsprint);
  };

  // Check if user can perform admin actions on account
  const canManageAccount = (account: AccountWithOwnership): boolean => {
    return account.is_owner;
  };

  return {
    accounts,
    isLoading,
    error: error?.message || null,
    fetchSharedAccounts,
    refreshAccountToken,
    deleteAccount,
    getExpiringAccounts,
    getOwnedAccounts,
    getSharedAccounts,
    getAccountsSharedWithTeam,
    canManageAccount,
    // Utility properties
    totalAccounts: accounts.length,
    ownedCount: getOwnedAccounts().length,
    sharedCount: getSharedAccounts().length,
    sharedWithTeamCount: getAccountsSharedWithTeam().length,
    expiringCount: getExpiringAccounts().length,
    // Permission flags
    canAddAccounts: true, // Now all users can add accounts
    isVsprintEmployee, // Add this flag for components to use
  };
} 