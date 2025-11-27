import { create } from 'zustand'
import type {
  ComplianceCheckResponse,
  ValidationResult,
} from '@/types'
import { checkCompliance, validateField } from '@/services/api'

interface ComplianceState {
  formData: Record<string, unknown>
  validationResults: Record<string, ValidationResult>
  report: ComplianceCheckResponse | null
  checking: boolean
  error: string | null

  // Actions
  updateField: (field: string, value: unknown) => void
  validateField: (programId: string, field: string) => Promise<void>
  checkCompliance: (programId: string) => Promise<void>
  clearForm: () => void
  reset: () => void
  setFormData: (data: Record<string, unknown>) => void
  setChecking: (checking: boolean) => void
  setError: (error: string | null) => void
}

export const useComplianceStore = create<ComplianceState>((set, get) => ({
  formData: {},
  validationResults: {},
  report: null,
  checking: false,
  error: null,

  updateField: (field, value) =>
    set((state) => ({
      formData: { ...state.formData, [field]: value },
    })),

  validateField: async (programId: string, field: string) => {
    const { formData } = get()
    const value = formData[field]

    try {
      const result = await validateField(programId, field, value)

      set((state) => ({
        validationResults: {
          ...state.validationResults,
          [field]: result,
        },
      }))
    } catch (error) {
      console.error(`Validation failed for field ${field}:`, error)
    }
  },

  checkCompliance: async (programId: string) => {
    set({ checking: true, error: null })

    try {
      const response = await checkCompliance({
        form_data: get().formData,
        program_id: programId,
        workflow_type: 'ei_application', // Required by backend
      })

      set({
        report: response,
        checking: false,
      })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Compliance check failed',
        checking: false,
      })
    }
  },

  clearForm: () =>
    set({
      formData: {},
      validationResults: {},
      report: null,
      error: null,
    }),

  reset: () =>
    set({
      formData: {},
      validationResults: {},
      report: null,
      checking: false,
      error: null,
    }),

  setFormData: (data) => set({ formData: data }),

  setChecking: (checking) => set({ checking }),

  setError: (error) => set({ error }),
}))
