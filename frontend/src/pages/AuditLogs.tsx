import React from 'react';
import { AuditLogViewer } from '../components/retention/AuditLogViewer';

const AuditLogs: React.FC = () => {
  return (
    <div className="space-y-6">
      <AuditLogViewer />
    </div>
  );
};

export default AuditLogs;
