import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { AccountWithOwnership } from '../hooks/marketplaces/allegro/accounts'

interface State {
  current?: AccountWithOwnership
  setCurrent: (acc: AccountWithOwnership | undefined) => void
  autoSelectFirst: (accounts: AccountWithOwnership[]) => void
}

export const useAccountStore = create<State>()(
  persist(
    (set, get) => ({
      current: undefined,
      setCurrent: (acc: AccountWithOwnership | undefined) => set({ current: acc }),
      autoSelectFirst: (accounts: AccountWithOwnership[]) => {
        const { current } = get()
        // If no account is selected and we have accounts, select the first one
        if (!current && accounts.length > 0) {
          set({ current: accounts[0] })
        }
        // If current account is no longer available, select first available or clear
        else if (current && !accounts.find(acc => acc.id === current.id)) {
          set({ current: accounts.length > 0 ? accounts[0] : undefined })
        }
      }
    }),
    {
      name: 'account-storage',
      partialize: (state) => ({ current: state.current })
    }
  )
) 