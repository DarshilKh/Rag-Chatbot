import { createContext, useCallback, useEffect, useState } from 'react'
import { documentsApi } from '../api/documents'

export const DocumentContext = createContext(null)

export function DocumentProvider({ children }) {
  const [documents, setDocuments] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await documentsApi.list()
      setDocuments(data.documents)
    } catch (err) {
      setError(err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const upload = useCallback(async (file, onUploadProgress) => {
    const data = await documentsApi.upload(file, onUploadProgress)
    setDocuments((current) => [data.document, ...current])
    return data.document
  }, [])

  const rename = useCallback(async (id, newFilename) => {
    const updated = await documentsApi.rename(id, newFilename)
    setDocuments((current) => current.map((doc) => (doc.id === id ? updated : doc)))
    return updated
  }, [])

  const remove = useCallback(async (id) => {
    await documentsApi.remove(id)
    setDocuments((current) => current.filter((doc) => doc.id !== id))
  }, [])

  const readyDocuments = documents.filter((doc) => doc.status === 'ready')

  return (
    <DocumentContext.Provider
      value={{
        documents,
        readyDocuments,
        isLoading,
        error,
        refresh,
        upload,
        rename,
        remove,
      }}
    >
      {children}
    </DocumentContext.Provider>
  )
}
