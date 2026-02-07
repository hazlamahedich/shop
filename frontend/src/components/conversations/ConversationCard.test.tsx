/**
 * ConversationCard Component Tests
 *
 * Tests conversation card rendering and interactions
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ConversationCard from './ConversationCard';
import type { Conversation as ConversationType } from '../../types/conversation';

describe('ConversationCard', () => {
  const mockConversation: ConversationType = {
    id: 1,
    platformSenderId: 'customer_1234567890',
    platformSenderIdMasked: 'cust****',
    lastMessage: 'I am looking for running shoes',
    status: 'active',
    sentiment: 'neutral',
    messageCount: 5,
    updatedAt: new Date().toISOString(),
    createdAt: new Date().toISOString(),
  };

  it('renders conversation card with masked ID', () => {
    render(<ConversationCard conversation={mockConversation} />);

    expect(screen.getByText('cust****')).toBeInTheDocument();
  });

  it('renders last message preview', () => {
    render(<ConversationCard conversation={mockConversation} />);

    expect(screen.getByText('I am looking for running shoes')).toBeInTheDocument();
  });

  it('renders status badge with correct style', () => {
    const { rerender } = render(<ConversationCard conversation={mockConversation} />);
    expect(screen.getByText('Active')).toHaveClass('bg-green-100', 'text-green-700');

    const handoffConv = { ...mockConversation, status: 'handoff' as const };
    rerender(<ConversationCard conversation={handoffConv} />);
    expect(screen.getByText('Handoff')).toHaveClass('bg-yellow-100', 'text-yellow-700');

    const closedConv = { ...mockConversation, status: 'closed' as const };
    rerender(<ConversationCard conversation={closedConv} />);
    expect(screen.getByText('Closed')).toHaveClass('bg-gray-100', 'text-gray-700');
  });

  it('renders message count when > 0', () => {
    render(<ConversationCard conversation={mockConversation} />);
    expect(screen.getByText('5 messages')).toBeInTheDocument();
  });

  it('does not render message count when 0', () => {
    const noMessagesConv = { ...mockConversation, messageCount: 0 };
    render(<ConversationCard conversation={noMessagesConv} />);

    expect(screen.queryByText('0 messages')).not.toBeInTheDocument();
    expect(screen.queryByText('messages')).not.toBeInTheDocument();
  });

  it('renders "No messages yet" when lastMessage is null', () => {
    const noMessageConv = { ...mockConversation, lastMessage: null };
    render(<ConversationCard conversation={noMessageConv} />);

    expect(screen.getByText('No messages yet')).toBeInTheDocument();
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = vi.fn();
    render(<ConversationCard conversation={mockConversation} onClick={handleClick} />);

    const card = screen.getByText('cust****').closest('div');
    card?.click();

    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
