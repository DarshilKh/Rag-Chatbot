import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, fireEvent, waitFor } from '@testing-library/react'
import UploadZone from '../UploadZone'
import { useDocuments } from '../../../hooks/useDocuments'
import { useToast } from '../../../hooks/useToast'

vi.mock('../../../hooks/useDocuments')
vi.mock('../../../hooks/useToast')

function makeFile(name, content = 'hello world', type = 'text/plain') {
  return new File([content], name, { type })
}

function uploadViaHiddenInput(container, file) {
  const input = container.querySelector('input[type="file"]')
  fireEvent.change(input, { target: { files: [file] } })
}

describe('UploadZone', () => {
  let notify
  let upload

  beforeEach(() => {
    notify = vi.fn()
    upload = vi.fn()
    useToast.mockReturnValue({ notify })
    useDocuments.mockReturnValue({ upload })
  })

  it('shows a success toast when the uploaded document is ready', async () => {
    upload.mockResolvedValue({ status: 'ready', filename: 'notes.md' })
    const { container } = render(<UploadZone />)

    uploadViaHiddenInput(container, makeFile('notes.md'))

    await waitFor(() => expect(notify).toHaveBeenCalled())
    expect(notify).toHaveBeenCalledWith(expect.stringContaining('uploaded and indexed'), 'success')
  })

  it(
    'regression test for audit finding H4: shows an ERROR toast (not success) ' +
      'when the backend returns a successful HTTP response but indexing failed',
    async () => {
      upload.mockResolvedValue({
        status: 'failed',
        filename: 'corrupt.pdf',
        error_message: 'PDF is password-protected.',
      })
      const { container } = render(<UploadZone />)

      uploadViaHiddenInput(container, makeFile('corrupt.pdf', 'x', 'application/pdf'))

      await waitFor(() => expect(notify).toHaveBeenCalled())
      // The bug: this previously called notify(..., 'success') unconditionally
      // any time the upload() promise resolved without throwing, regardless
      // of the returned document's status.
      expect(notify).toHaveBeenCalledWith('PDF is password-protected.', 'error')
      expect(notify).not.toHaveBeenCalledWith(expect.stringContaining('uploaded and indexed'), 'success')
    }
  )

  it('falls back to a generic error message if error_message is missing', async () => {
    upload.mockResolvedValue({ status: 'failed', filename: 'bad.txt' })
    const { container } = render(<UploadZone />)

    uploadViaHiddenInput(container, makeFile('bad.txt'))

    await waitFor(() => expect(notify).toHaveBeenCalled())
    expect(notify).toHaveBeenCalledWith(expect.stringContaining('indexing failed'), 'error')
  })

  it('shows an error toast when the upload call itself throws', async () => {
    upload.mockRejectedValue({ message: 'Network error' })
    const { container } = render(<UploadZone />)

    uploadViaHiddenInput(container, makeFile('notes.md'))

    await waitFor(() => expect(notify).toHaveBeenCalled())
    expect(notify).toHaveBeenCalledWith('Network error', 'error')
  })

  it('rejects an unsupported file type before ever calling upload()', async () => {
    const { container } = render(<UploadZone />)

    uploadViaHiddenInput(container, makeFile('virus.exe', 'x', 'application/octet-stream'))

    await waitFor(() => expect(notify).toHaveBeenCalled())
    expect(upload).not.toHaveBeenCalled()
    expect(notify).toHaveBeenCalledWith(expect.stringContaining("isn't a supported type"), 'error')
  })
})
