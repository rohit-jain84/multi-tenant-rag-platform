import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import Modal from '../shared/Modal';
import Button from '../shared/Button';
import { createTenant } from '../../api/tenants';
import toast from 'react-hot-toast';

interface CreateTenantFormProps {
  open: boolean;
  onClose: () => void;
  onCreated: (tenantId: string, tenantName: string, apiKey: string) => void;
}

export default function CreateTenantForm({ open, onClose, onCreated }: CreateTenantFormProps) {
  const [name, setName] = useState('');
  const [creating, setCreating] = useState(false);
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setCreating(true);
    try {
      const result = await createTenant({ name: name.trim() });
      setGeneratedKey(result.api_key);
      toast.success(`Tenant "${name}" created`);
      onCreated(result.tenant.id, result.tenant.name, result.api_key);
    } catch {
      toast.error('Failed to create tenant');
    } finally {
      setCreating(false);
    }
  };

  const handleCopy = async () => {
    if (!generatedKey) return;
    await navigator.clipboard.writeText(generatedKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleClose = () => {
    setName('');
    setGeneratedKey(null);
    setCopied(false);
    onClose();
  };

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title={generatedKey ? 'Tenant Created' : 'Create New Tenant'}
      footer={
        generatedKey ? (
          <Button onClick={handleClose}>Done</Button>
        ) : (
          <>
            <Button variant="secondary" onClick={handleClose}>Cancel</Button>
            <Button onClick={handleCreate} loading={creating} disabled={!name.trim()}>Create</Button>
          </>
        )
      }
    >
      {generatedKey ? (
        <div className="space-y-3">
          <p className="text-sm text-text-muted dark:text-dark-text-muted">
            Save this API key now. It won't be shown again.
          </p>
          <div className="flex items-center gap-2 p-3 rounded-lg bg-surface dark:bg-dark-surface-alt border border-border dark:border-dark-border">
            <code className="flex-1 text-sm font-mono text-text dark:text-dark-text break-all">
              {generatedKey}
            </code>
            <button
              onClick={handleCopy}
              className="p-2 rounded-lg hover:bg-white dark:hover:bg-dark-surface transition-colors flex-shrink-0 cursor-pointer"
              title="Copy API key"
            >
              {copied ? <Check className="h-4 w-4 text-success" /> : <Copy className="h-4 w-4 text-text-muted" />}
            </button>
          </div>
        </div>
      ) : (
        <div>
          <label className="block text-sm font-medium text-text dark:text-dark-text mb-1.5">
            Tenant Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Acme Corp"
            autoFocus
            className="w-full px-3 py-2 text-sm rounded-lg border border-border dark:border-dark-border
              bg-white dark:bg-dark-surface text-text dark:text-dark-text
              focus:outline-none focus:ring-2 focus:ring-primary/30"
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleCreate();
            }}
          />
        </div>
      )}
    </Modal>
  );
}
