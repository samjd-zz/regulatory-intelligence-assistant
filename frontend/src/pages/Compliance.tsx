import { useState } from 'react'
import { CheckCircle, AlertCircle, XCircle } from 'lucide-react'
import { useComplianceStore } from '@/store/complianceStore'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

export function Compliance() {
  const { formData, report, checking, error, updateField, checkCompliance } =
    useComplianceStore()
  const [programId] = useState('employment-insurance')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await checkCompliance(programId)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Compliance Checking
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Form Section */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Application Form
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={(formData.full_name as string) || ''}
                  onChange={(e) => updateField('full_name', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Social Insurance Number (SIN)
                </label>
                <input
                  type="text"
                  value={(formData.sin as string) || ''}
                  onChange={(e) => updateField('sin', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="123-456-789"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Residency Status
                </label>
                <select
                  value={(formData.residency_status as string) || ''}
                  onChange={(e) => updateField('residency_status', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select status</option>
                  <option value="citizen">Canadian Citizen</option>
                  <option value="permanent_resident">Permanent Resident</option>
                  <option value="temporary_resident">Temporary Resident</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Hours Worked (Last 52 weeks)
                </label>
                <input
                  type="number"
                  value={(formData.hours_worked as number) || ''}
                  onChange={(e) => updateField('hours_worked', parseInt(e.target.value) || 0)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="520"
                />
              </div>

              <button
                type="submit"
                disabled={checking}
                className="w-full bg-blue-500 text-white px-4 py-3 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed font-medium"
              >
                {checking ? 'Checking...' : 'Check Compliance'}
              </button>
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
                {error}
              </div>
            )}

            {!checking && !error && !report && (
              <p className="text-gray-600 text-center py-12">
                Fill out the form and click "Check Compliance" to see results
              </p>
            )}

            {!checking && report && (
              <div className="space-y-4">
                {/* Overall Status */}
                <div
                  className={`rounded-lg p-4 ${
                    report.compliant
                      ? 'bg-green-50 border border-green-200'
                      : 'bg-orange-50 border border-orange-200'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {report.compliant ? (
                      <CheckCircle className="w-6 h-6 text-green-600" />
                    ) : (
                      <AlertCircle className="w-6 h-6 text-orange-600" />
                    )}
                    <span
                      className={`font-semibold ${
                        report.compliant ? 'text-green-900' : 'text-orange-900'
                      }`}
                    >
                      {report.compliant
                        ? 'Application is Compliant'
                        : 'Issues Found'}
                    </span>
                  </div>
                </div>

                {/* Issues */}
                {report.issues.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">
                      Issues to Address
                    </h3>
                    <div className="space-y-2">
                      {report.issues.map((issue) => (
                        <div
                          key={issue.id}
                          className="bg-red-50 border border-red-200 rounded-lg p-3"
                        >
                          <div className="flex items-start gap-2">
                            <XCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                            <div className="flex-1">
                              <p className="font-medium text-red-900">
                                {issue.description}
                              </p>
                              <p className="text-sm text-red-700 mt-1">
                                {issue.suggestion}
                              </p>
                              <p className="text-xs text-red-600 mt-1">
                                Reference: {issue.regulation}
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
                    <h3 className="font-semibold text-gray-900 mb-2">
                      Passed Checks ({report.passed_checks.length})
                    </h3>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                      <ul className="text-sm text-green-800 space-y-1">
                        {report.passed_checks.slice(0, 5).map((check, idx) => (
                          <li key={idx} className="flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 flex-shrink-0" />
                            {check}
                          </li>
                        ))}
                        {report.passed_checks.length > 5 && (
                          <li className="text-gray-600">
                            ... and {report.passed_checks.length - 5} more
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
    </div>
  )
}
