import type { WidgetMessage, MessageGroup } from '../types/widget';

export function groupMessages(messages: WidgetMessage[]): MessageGroup[] {
  if (messages.length === 0) return [];

  const groups: MessageGroup[] = [];

  for (const message of messages) {
    if (message.sender === 'system') {
      groups.push({ id: message.messageId, sender: 'system', messages: [message] });
      continue;
    }

    const lastGroup = groups[groups.length - 1];

    if (!lastGroup || lastGroup.sender === 'system' || lastGroup.sender !== message.sender) {
      groups.push({ id: message.messageId, sender: message.sender, messages: [message] });
    } else {
      lastGroup.messages.push(message);
    }
  }

  return groups;
}

export function isFirstInGroup(_group: MessageGroup, index: number): boolean {
  return index === 0;
}

export function isLastInGroup(group: MessageGroup, index: number): boolean {
  return index === group.messages.length - 1;
}

export function isSingleMessage(group: MessageGroup): boolean {
  return group.messages.length === 1;
}

export function getGroupPosition(
  group: MessageGroup,
  index: number
): 'first' | 'middle' | 'last' | 'single' {
  if (isSingleMessage(group)) return 'single';
  if (isFirstInGroup(group, index)) return 'first';
  if (isLastInGroup(group, index)) return 'last';
  return 'middle';
}
