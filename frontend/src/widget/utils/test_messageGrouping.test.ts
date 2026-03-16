import { describe, it, expect } from 'vitest';
import { groupMessages, isFirstInGroup, isLastInGroup, isSingleMessage, getGroupPosition } from './messageGrouping';
import type { WidgetMessage } from '../types/widget';

function createMessage(id: string, sender: WidgetMessage['sender'], createdAt = new Date().toISOString()): WidgetMessage {
  return {
    messageId: id,
    content: `Message ${id}`,
    sender,
    createdAt,
  };
}

describe('groupMessages', () => {
  it('returns empty array for empty messages', () => {
    expect(groupMessages([])).toEqual([]);
  });

  it('groups single message correctly', () => {
    const messages = [createMessage('1', 'bot')];
    const groups = groupMessages(messages);

    expect(groups).toHaveLength(1);
    expect(groups[0].id).toBe('1');
    expect(groups[0].sender).toBe('bot');
    expect(groups[0].messages).toHaveLength(1);
  });

  it('groups consecutive same sender messages', () => {
    const messages = [
      createMessage('1', 'bot'),
      createMessage('2', 'bot'),
      createMessage('3', 'bot'),
    ];
    const groups = groupMessages(messages);

    expect(groups).toHaveLength(1);
    expect(groups[0].id).toBe('1');
    expect(groups[0].sender).toBe('bot');
    expect(groups[0].messages).toHaveLength(3);
  });

  it('breaks group on sender change', () => {
    const messages = [
      createMessage('1', 'bot'),
      createMessage('2', 'bot'),
      createMessage('3', 'user'),
      createMessage('4', 'user'),
    ];
    const groups = groupMessages(messages);

    expect(groups).toHaveLength(2);
    expect(groups[0].sender).toBe('bot');
    expect(groups[0].messages).toHaveLength(2);
    expect(groups[1].sender).toBe('user');
    expect(groups[1].messages).toHaveLength(2);
  });

  it('handles mixed senders correctly', () => {
    const messages = [
      createMessage('1', 'bot'),
      createMessage('2', 'user'),
      createMessage('3', 'bot'),
      createMessage('4', 'user'),
    ];
    const groups = groupMessages(messages);

    expect(groups).toHaveLength(4);
    expect(groups.every(g => g.messages.length === 1)).toBe(true);
  });

  it('NEVER groups system messages - each is standalone', () => {
    const messages = [
      createMessage('1', 'bot'),
      createMessage('2', 'system'),
      createMessage('3', 'bot'),
    ];
    const groups = groupMessages(messages);

    expect(groups).toHaveLength(3);
    expect(groups[0].sender).toBe('bot');
    expect(groups[1].sender).toBe('system');
    expect(groups[1].messages).toHaveLength(1);
    expect(groups[2].sender).toBe('bot');
  });

  it('handles consecutive system messages - each standalone', () => {
    const messages = [
      createMessage('1', 'system'),
      createMessage('2', 'system'),
      createMessage('3', 'system'),
    ];
    const groups = groupMessages(messages);

    expect(groups).toHaveLength(3);
    expect(groups.every(g => g.messages.length === 1)).toBe(true);
  });

  it('handles malformed message (missing sender) gracefully', () => {
    const messages = [
      { messageId: '1', content: 'Test', createdAt: new Date().toISOString() },
    ] as WidgetMessage[];
    
    const groups = groupMessages(messages);
    
    expect(groups).toHaveLength(1);
    expect(groups[0].messages).toHaveLength(1);
  });

  it('handles 100+ messages efficiently (<10ms)', () => {
    const messages: WidgetMessage[] = [];
    for (let i = 0; i < 150; i++) {
      messages.push(createMessage(`msg-${i}`, i % 2 === 0 ? 'bot' : 'user'));
    }

    const start = performance.now();
    const groups = groupMessages(messages);
    const duration = performance.now() - start;

    expect(duration).toBeLessThan(10);
    expect(groups.length).toBeGreaterThan(0);
  });

  it('groups merchant messages with bot messages', () => {
    const messages = [
      createMessage('1', 'bot'),
      createMessage('2', 'merchant'),
      createMessage('3', 'merchant'),
    ];
    const groups = groupMessages(messages);

    expect(groups).toHaveLength(2);
    expect(groups[0].sender).toBe('bot');
    expect(groups[0].messages).toHaveLength(1);
    expect(groups[1].sender).toBe('merchant');
    expect(groups[1].messages).toHaveLength(2);
  });

  it('preserves message order within groups', () => {
    const messages = [
      createMessage('1', 'bot'),
      createMessage('2', 'bot'),
      createMessage('3', 'bot'),
    ];
    const groups = groupMessages(messages);

    expect(groups[0].messages[0].messageId).toBe('1');
    expect(groups[0].messages[1].messageId).toBe('2');
    expect(groups[0].messages[2].messageId).toBe('3');
  });
});

describe('isFirstInGroup', () => {
  it('returns true for first message', () => {
    const group = { id: '1', sender: 'bot' as const, messages: [createMessage('1', 'bot'), createMessage('2', 'bot')] };
    expect(isFirstInGroup(group, 0)).toBe(true);
  });

  it('returns false for non-first message', () => {
    const group = { id: '1', sender: 'bot' as const, messages: [createMessage('1', 'bot'), createMessage('2', 'bot')] };
    expect(isFirstInGroup(group, 1)).toBe(false);
  });
});

describe('isLastInGroup', () => {
  it('returns true for last message', () => {
    const group = { id: '1', sender: 'bot' as const, messages: [createMessage('1', 'bot'), createMessage('2', 'bot')] };
    expect(isLastInGroup(group, 1)).toBe(true);
  });

  it('returns false for non-last message', () => {
    const group = { id: '1', sender: 'bot' as const, messages: [createMessage('1', 'bot'), createMessage('2', 'bot')] };
    expect(isLastInGroup(group, 0)).toBe(false);
  });
});

describe('isSingleMessage', () => {
  it('returns true for single message group', () => {
    const group = { id: '1', sender: 'bot' as const, messages: [createMessage('1', 'bot')] };
    expect(isSingleMessage(group)).toBe(true);
  });

  it('returns false for multi-message group', () => {
    const group = { id: '1', sender: 'bot' as const, messages: [createMessage('1', 'bot'), createMessage('2', 'bot')] };
    expect(isSingleMessage(group)).toBe(false);
  });
});

describe('getGroupPosition', () => {
  const createGroup = (count: number) => ({
    id: '1',
    sender: 'bot' as const,
    messages: Array.from({ length: count }, (_, i) => createMessage(`${i}`, 'bot')),
  });

  it('returns "single" for single message group', () => {
    const group = createGroup(1);
    expect(getGroupPosition(group, 0)).toBe('single');
  });

  it('returns "first" for first message in multi-message group', () => {
    const group = createGroup(3);
    expect(getGroupPosition(group, 0)).toBe('first');
  });

  it('returns "middle" for middle message in multi-message group', () => {
    const group = createGroup(3);
    expect(getGroupPosition(group, 1)).toBe('middle');
  });

  it('returns "last" for last message in multi-message group', () => {
    const group = createGroup(3);
    expect(getGroupPosition(group, 2)).toBe('last');
  });
});
