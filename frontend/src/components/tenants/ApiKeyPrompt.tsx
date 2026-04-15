import { useState } from 'react';
import Modal from '../shared/Modal';
import Button from '../shared/Button';

interface ApiKeyPromptProps {
  open: boolean;
  tenantName: string;
  onClose: () => void;
  onSubmit: (apiKey: string) => void;
}

export default function ApiKeyPrompt({ open, tenantName, onClose, onSubmit }: ApiKeyPromptProps) {
  const [apiKey, setApiKey] = useState('');

  const handleSubmit = () => {
    if (!apiKey.trim()) return;
    onSubmit(apiKey.trim());
    setApiKey('');
  };

  const handleClose = () => {
    setApiKey('');
    onClose();
  };

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title={`Connect to ${tenantName}`}
      footer={
        <>
          <Button variant="secondary" onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={!apiKey.trim()}>Connect</Button>
        </>
      }
    >
      <div>
        <label className="block text-sm font-medium text-text dark:text-dark-text mb-1.5">
          API Key
        </label>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="Enter the tenant API key"
          autoFocus
          className="w-full px-3 py-2 text-sm rounded-lg border border-border dark:border-dark-border
            bg-white dark:bg-dark-surface text-text dark:text-dark-text
            focus:outline-none focus:ring-2 focus:ring-primary/30"
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSubmit();
          }}
        />
        <p className="mt-2 text-xs text-text-muted dark:text-dark-text-muted">
          Enter the API key that was generated when this tenant was created.
        </p>
      </div>
    </Modal>
  );
}
