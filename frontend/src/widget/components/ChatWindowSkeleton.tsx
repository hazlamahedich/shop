import * as React from 'react';

export function ChatWindowSkeleton() {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: '#f9fafb',
        borderRadius: '12px',
        overflow: 'hidden',
      }}
    >
      {}
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <div
          style={{
            width: '100px',
            height: '16px',
            backgroundColor: '#e5e7eb',
            borderRadius: '4px',
          }}
        />
      </div>
      {}
      <div
        style={{
          flex: 1,
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        {}
        <div
          style={{
            alignSelf: 'flex-start',
            maxWidth: '70%',
            padding: '12px 16px',
            backgroundColor: '#e5e7eb',
            borderRadius: '16px 16px 16px 4px',
          }}
        >
          <div
            style={{
              width: '120px',
              height: '12px',
              backgroundColor: '#d1d5db',
              borderRadius: '4px',
            }}
          />
        </div>
        {}
        <div
          style={{
            alignSelf: 'flex-end',
            maxWidth: '70%',
            padding: '12px 16px',
            backgroundColor: '#6366f1',
            borderRadius: '16px 16px 4px 16px',
          }}
        >
          <div
            style={{
              width: '80px',
              height: '12px',
              backgroundColor: 'rgba(255,255,255,0.5)',
              borderRadius: '4px',
            }}
          />
        </div>
      </div>
      {}
      <div
        style={{
          padding: '12px 16px',
          borderTop: '1px solid #e5e7eb',
          display: 'flex',
          gap: '8px',
        }}
      >
        <div
          style={{
            flex: 1,
            height: '40px',
            backgroundColor: '#e5e7eb',
            borderRadius: '20px',
          }}
        />
        <div
          style={{
            width: '40px',
            height: '40px',
            backgroundColor: '#6366f1',
            borderRadius: '50%',
          }}
        />
      </div>
    </div>
  );
}
