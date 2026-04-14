import { useState } from 'react';
import { Trash2, FileText, ChevronLeft, ChevronRight } from 'lucide-react';
import StatusBadge from './StatusBadge';
import Modal from '../shared/Modal';
import Button from '../shared/Button';
import EmptyState from '../shared/EmptyState';
import { deleteDocument } from '../../api/documents';
import { formatDate } from '../../utils/formatters';
import { DEFAULTS } from '../../utils/constants';
import type { Document } from '../../types/document';
import toast from 'react-hot-toast';

interface DocumentListProps {
  documents: Document[];
  total: number;
  page: number;
  onPageChange: (page: number) => void;
  onRefresh: () => void;
  loading: boolean;
}

export default function DocumentList({ documents, total, page, onPageChange, onRefresh, loading }: DocumentListProps) {
  const [deleteTarget, setDeleteTarget] = useState<Document | null>(null);
  const [deleting, setDeleting] = useState(false);
  const totalPages = Math.ceil(total / DEFAULTS.PAGE_SIZE);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteDocument(deleteTarget.id);
      toast.success(`Deleted "${deleteTarget.filename}"`);
      setDeleteTarget(null);
      onRefresh();
    } catch {
      toast.error('Failed to delete document');
    } finally {
      setDeleting(false);
    }
  };

  if (!loading && documents.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title="No documents yet"
        description="Upload your first document to get started with the RAG pipeline."
      />
    );
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border dark:border-dark-border">
              <th className="text-left py-3 px-4 text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">Name</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">Format</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">Category</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">Status</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">Uploaded</th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border dark:divide-dark-border">
            {documents.map((doc) => (
              <tr key={doc.id} className="hover:bg-surface dark:hover:bg-dark-surface-alt transition-colors">
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-primary flex-shrink-0" />
                    <span className="text-sm font-medium text-text dark:text-dark-text truncate max-w-[200px]">
                      {doc.filename}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-4">
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-surface dark:bg-dark-surface-alt text-text-muted dark:text-dark-text-muted uppercase">
                    {doc.format}
                  </span>
                </td>
                <td className="py-3 px-4 text-sm text-text-muted dark:text-dark-text-muted">
                  {doc.category || '—'}
                </td>
                <td className="py-3 px-4">
                  <StatusBadge status={doc.status} />
                </td>
                <td className="py-3 px-4 text-sm text-text-muted dark:text-dark-text-muted">
                  {formatDate(doc.upload_date)}
                </td>
                <td className="py-3 px-4 text-right">
                  <button
                    onClick={() => setDeleteTarget(doc)}
                    className="p-1.5 rounded-lg text-text-muted hover:text-danger hover:bg-danger/10 transition-colors cursor-pointer"
                    title="Delete document"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-4 border-t border-border dark:border-dark-border mt-4">
          <span className="text-sm text-text-muted dark:text-dark-text-muted">
            {total} document{total !== 1 ? 's' : ''} total
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="p-1.5 rounded-lg text-text-muted hover:bg-surface dark:hover:bg-dark-surface-alt
                disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="text-sm text-text-muted dark:text-dark-text-muted">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="p-1.5 rounded-lg text-text-muted hover:bg-surface dark:hover:bg-dark-surface-alt
                disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      <Modal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete Document"
        footer={
          <>
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>Cancel</Button>
            <Button variant="danger" onClick={handleDelete} loading={deleting}>Delete</Button>
          </>
        }
      >
        <p className="text-sm text-text-muted dark:text-dark-text-muted">
          Are you sure you want to delete <strong className="text-text dark:text-dark-text">{deleteTarget?.filename}</strong>?
          This will also remove all associated chunks from the vector store.
        </p>
      </Modal>
    </>
  );
}
