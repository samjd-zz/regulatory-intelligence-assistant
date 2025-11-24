import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { CheckCircle, AlertCircle, XCircle } from 'lucide-react'
import { useComplianceStore } from '@/store/complianceStore'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

// Validation schema
const complianceSchema = z.object({
  full_name: z
    .string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name must be less than 100 characters'),
  sin: z
    .string()
    .regex(/^\d{3}-\d{3}-\d{3}$/, 'SIN must be in format: 123-456-789')
    .length(11, 'SIN must be exactly 11 characters including dashes'),
  residency_status: z
    .enum(['citizen', 'permanent_resident', 'temporary_resident'], {
      message: 'Please select a valid residency status',
    }),
  hours_worked: z
    .number()
    .int('Hours must be a whole number')
    .min(420, 'Minimum 420 hours required for eligibility')
    .max(10000, 'Hours worked seems unreasonably high'),
})

type ComplianceFormData = z.infer<typeof complianceSchema>

export function Compliance() {
  const { report, checking, error, checkCompliance } = useComplianceStore()
  const [programId] = useState('employment-insurance')

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm<ComplianceFormData>({
    resolver: zodResolver(complianceSchema),
    mode: 'onBlur', // Validate on blur
    defaultValues: {
      full_name: '',
      sin: '',
      residency_status: undefined,
      hours_worked: undefined,
    },
  })

  const onSubmit = async () => {
    // Form is validated, now check compliance
    await checkCompliance(programId)
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Compliance Checking
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Form Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Employment Insurance Application
          </h2>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Full Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                {...register('full_name')}
                className={`w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 ${
                  errors.full_name
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-blue-500'
                }`}
                placeholder="John Doe"
              />
              {errors.full_name && (
                <p className="mt-1 text-sm text-red-600">{errors.full_name.message}</p>
              )}
            </div>

            {/* SIN */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Social Insurance Number (SIN) <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                {...register('sin')}
                className={`w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 ${
                  errors.sin
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-blue-500'
                }`}
                placeholder="123-456-789"
                maxLength={11}
              />
              {errors.sin && (
                <p className="mt-1 text-sm text-red-600">{errors.sin.message}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">Format: 123-456-789</p>
            </div>

            {/* Residency Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Residency Status <span className="text-red-500">*</span>
              </label>
              <select
                {...register('residency_status')}
                className={`w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 ${
                  errors.residency_status
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-blue-500'
                }`}
              >
                <option value="">Select status</option>
                <option value="citizen">Canadian Citizen</option>
                <option value="permanent_resident">Permanent Resident</option>
                <option value="temporary_resident">Temporary Resident</option>
              </select>
              {errors.residency_status && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.residency_status.message}
                </p>
              )}
            </div>

            {/* Hours Worked */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Hours Worked (Last 52 weeks) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                {...register('hours_worked', { valueAsNumber: true })}
                className={`w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 ${
                  errors.hours_worked
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-blue-500'
                }`}
                placeholder="520"
                min="0"
              />
              {errors.hours_worked && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.hours_worked.message}
                </p>
              )}
              <p className="mt-1 text-xs text-gray-500">Minimum 420 hours required</p>
            </div>

            <button
              type="submit"
              disabled={checking || !isValid}
              className="w-full bg-blue-500 text-white px-4 py-3 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed font-medium transition-colors"
            >
              {checking ? 'Checking...' : 'Check Compliance'}
            </button>

            {!isValid && Object.keys(errors).length > 0 && (
              <p className="text-sm text-amber-600 text-center">
                Please fix validation errors before submitting
              </p>
            )}
          </form>
        </div>

        {/* Results Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Compliance Report
          </h2>

          {checking && (
            <div className="flex justify-center py-12">
              <LoadingSpinner message="Checking compliance..." />
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
              <div className="flex items-start gap-2">
                <XCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium">Error</p>
                  <p className="text-sm">{error}</p>
                </div>
              </div>
            </div>
          )}

          {!checking && !error && !report && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-gray-600 font-medium mb-2">Ready to Check</p>
              <p className="text-sm text-gray-500">
                Fill out the form and click "Check Compliance" to see results
              </p>
            </div>
          )}

          {!checking && report && (
            <div className="space-y-4">
              {/* Overall Status */}
              <div
                className={`rounded-lg p-4 ${
                  report.compliant
                    ? 'bg-green-50 border-2 border-green-300'
                    : 'bg-red-50 border-2 border-red-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  {report.compliant ? (
                    <CheckCircle className="w-8 h-8 text-green-600 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-8 h-8 text-red-600 flex-shrink-0" />
                  )}
                  <div>
                    <p
                      className={`font-bold text-lg ${
                        report.compliant ? 'text-green-900' : 'text-red-900'
                      }`}
                    >
                      {report.compliant
                        ? 'Application is Compliant'
                        : 'Application Has Issues'}
                    </p>
                    <p
                      className={`text-sm ${
                        report.compliant ? 'text-green-700' : 'text-red-700'
                      }`}
                    >
                      Confidence: {Math.round(report.confidence * 100)}%
                    </p>
                  </div>
                </div>
              </div>

              {/* Issues */}
              {report.issues.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <XCircle className="w-5 h-5 text-red-600" />
                    Issues to Address ({report.issues.length})
                  </h3>
                  <div className="space-y-2">
                    {report.issues.map((issue) => (
                      <div
                        key={issue.id}
                        className={`rounded-lg p-4 border-l-4 ${
                          issue.severity === 'critical'
                            ? 'bg-red-50 border-red-500'
                            : issue.severity === 'high'
                              ? 'bg-orange-50 border-orange-500'
                              : issue.severity === 'medium'
                                ? 'bg-yellow-50 border-yellow-500'
                                : 'bg-blue-50 border-blue-500'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <AlertCircle
                            className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                              issue.severity === 'critical'
                                ? 'text-red-600'
                                : issue.severity === 'high'
                                  ? 'text-orange-600'
                                  : issue.severity === 'medium'
                                    ? 'text-yellow-600'
                                    : 'text-blue-600'
                            }`}
                          />
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs font-semibold uppercase tracking-wide text-gray-600">
                                {issue.severity}
                              </span>
                              <span className="text-xs text-gray-500">•</span>
                              <span className="text-xs text-gray-600">
                                {issue.field}
                              </span>
                            </div>
                            <p className="font-medium text-gray-900 mb-1">
                              {issue.description}
                            </p>
                            <p className="text-sm text-gray-700 mb-2">
                              💡 {issue.suggestion}
                            </p>
                            <p className="text-xs text-gray-500">
                              📋 Reference: {issue.regulation}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Passed Checks */}
              {report.passed_checks.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    Passed Checks ({report.passed_checks.length})
                  </h3>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <ul className="text-sm text-green-800 space-y-2">
                      {report.passed_checks.slice(0, 5).map((check, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                          <span>{check}</span>
                        </li>
                      ))}
                      {report.passed_checks.length > 5 && (
                        <li className="text-gray-600 pl-6">
                          ... and {report.passed_checks.length - 5} more checks passed
                        </li>
                      )}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
