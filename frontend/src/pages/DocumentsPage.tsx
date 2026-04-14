import PageLayout from '../components/layout/PageLayout';
import FileUploader from '../components/documents/FileUploader';
import DocumentList from '../components/documents/DocumentList';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import Card from '../components/shared/Card';
import { useDocuments } from '../hooks/useDocuments';

export default function DocumentsPage() {
  const { documents, total, page, setPage, loading, error, refresh } = useDocuments();

  return (
    <PageLayout title="Documents">
      <div className="space-y-6">
        {/* Upload Section */}
        <Card title="Upload Documents">
          <FileUploader onUploadComplete={refresh} />
        </Card>

        {/* Document List */}
        <Card title="Document Library">
          {error && (
            <div className="p-3 rounded-lg bg-danger/5 border border-danger/20 mb-4">
              <p className="text-sm text-danger">{error}</p>
            </div>
          )}
          {loading && documents.length === 0 ? (
            <LoadingSpinner label="Loading documents..." />
          ) : (
            <DocumentList
              documents={documents}
              total={total}
              page={page}
              onPageChange={setPage}
              onRefresh={refresh}
              loading={loading}
            />
          )}
        </Card>
      </div>
    </PageLayout>
  );
}
