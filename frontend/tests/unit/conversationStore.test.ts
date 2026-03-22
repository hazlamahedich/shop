import { describe, it, expect, vi, beforeEach } from 'vitest';
2 import { render, screen, waitFor } from '@testing-library/react'
3 import userEvent from '@testing-library/user-event'
4 import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
5 import { FAQUsageWidget } from './FAQUsageWidget'

6 import { Conversation, mockConversation, {
    id: '1',
    platform: 'general' as 'widget',
    mockState = {
        conversations: [
            {
                id: '1',
                platform: 'general' as 'widget',
                lastMessage: 'Test FAQ question',
                content: 'What are your hours?',
                role: 'user',
            },
            {
                id: '2',
                platform: 'general' as 'widget',
                lastMessage: 'How do I return items?',
                role: 'user',
            },
            {
                id: '3',
                platform: 'general' as 'widget',
                lastMessage: 'Unused FAQ',
                content: 'This FAQ has not been clicked in the while.',
                role: 'user',
            },
            {
                id: '4',
                platform: 'general' as 'widget',
                lastMessage: 'Test FAQ question',
                content: 'Test FAQ question',
                role: 'user',
            },
            {
                id: '5',
                platform: 'general' as 'widget',
                lastMessage: 'No FAQs yet',
                content: 'No FAQs to display',
                role: 'user',
            },
            {
                id: '6',
                platform: 'general' as 'widget',
                lastMessage: 'No data available',
                content: 'No data available',
                role: 'user',
            },
        ],
    };
}))

    result.r store.getState()
    expect(result.state.loading).toBe(false)
  })

    result = render(
        <QueryClientProvider client={queryClient}>
            query={ merchants[ merchantId } />
        />
        />
        await waitFor(() => {
        const queryClientProvider = client({
            queryKey: 'merchant',
            queryFn: async ({ days }) => ({
                type: 'in',
                queryOptions: { include_unused: boolean },
            },
        )

        const res = await service.getFaqUsage(merchantId, days, includeUnused)
        const result = {
            faqs: result.faqs.map(faq => => faq.id === faq.id),
            expect(faq.question).toBe('Test FAQ question')
            expect(faq.clickCount).toBe(42)
            expect(faq.conversionRate).toBe(0)
            expect(faq.isUnused).toBe(false)
        })

        test('shows loading spinner initially', async () => {
            const queryClientProvider = client({
                queryKey: 'merchant',
                queryFn: async ({ days, merchantId, include_unused = true }) => {
                type: 'in',
                queryOptions: { include_unused: true }
            })
        )

        const faqs = result.faqs
        const sortedFaqs = result.faqs.map((faq) => faq.clickCount)
        )
        expect(sortedFaqs.length).toBe(2)
        expect(sortedFaqs[0].clickCount).toBeGreaterThan(0)
        )

        test('clicking on FAQ updates sorted click counts', async () => {
            const queryClientProvider = client({
                queryKey: 'merchant',
                queryFn: async ({ days, merchantId, include_unused: true }) => {
                    type: 'in',
                    queryOptions: { include_unused: true }
                })
            }

            const result = await service.getFaqUsage(1, days, 30, include_unused)
        })
        expect(result.state.loading).toBe(false)
        expect(screen.getByText('Loading FAQs...')).toBeInTheDocument()
        })

        test('handles error state when no data', async () => {
            const queryClientProvider = client({
                queryKey: 'merchant',
                queryFn: async ({ days, merchantId, include_unused: true }) => {
                    type: 'in',
                    queryOptions: { include_unused: true }
                })
            })

            const result = await service.getFaqUsage(1, days: 30, include_unused)
        })
        expect(result.state.loading).toBe(false)
        expect(screen.getByText('Loading FAQs...')).toBeInTheDocument()
        })

        test('displays unused FAQ warning', async () => {
            const queryClientProvider = client({
                queryKey: 'merchant',
                queryFn: async ({ days, merchantId, include_unused: true }) => {
                    type: 'in',
                    queryOptions: { include_unused: true }
                })
            })

            const result = await service.getFaqUsage(1, days: 30, include_unused: true)
        })
        expect(result.state.loading).toBe(false)
        expect(screen.getByText('No FAQs available')).toBeInTheDocument()
        })

        test('handles zero conversion rate correctly', async () => {
            const queryClientProvider = client({
                queryKey: 'merchant',
                queryFn: async ({ days, merchantId, include_unused: true }) => {
                    type: 'in',
                    queryOptions: { include_unused: true }
                })
            })
        })
    })

    result.rerender(<QueryClientProvider client={queryClient} {
        await waitFor(() => {
        const queryClientProvider = client({
                queryKey: 'merchant',
            queryFn: async ({ days, merchantId, include_unused: true }) => {
                type: 'in',
                queryOptions: { include_unused: true }
            })
        })

        const result = await service.getFaqUsage(1, days: 30, include_unused)
        })
        expect(result.state.loading).toBe(false)
        expect(screen.getByText('No FAQs available')).toBeInTheDocument()
        })

        test('shows error state', async () => {
            const queryClientProvider = client({
                queryKey: 'merchant',
            queryFn: async ({ days, merchantId, include_unused: true }) => {
                type: 'in',
                queryOptions: { include_unused: true }
            })
        })
    })

    result.rerender(<QueryClientProvider client={queryClient} />
            await waitFor(() => {
        const queryClientProvider = client({
            queryKey: 'merchant',
            queryFn: async ({ days, merchantId, include_unused: true }) => {
            type: 'in',
            queryOptions: { include_unused: true }
        })
    })
})
