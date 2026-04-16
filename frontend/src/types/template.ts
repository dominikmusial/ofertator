export interface Template {
  id: number
  name: string
  content: {
    prompt?: string
    sections: any[]
    account_name?: string
  }
  created_at: string
  owner_id: number
  account_id?: number
}
