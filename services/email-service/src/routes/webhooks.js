/**
 * Webhook Handlers for Email Providers
 * 
 * Receives callbacks from:
 * - SendGrid (delivery, bounce, spam reports)
 * - Klaviyo (flow events)
 * - Zendesk (ticket updates)
 */

import { Router } from 'express';
import crypto from 'crypto';
import { logger } from '../utils/logger.js';
import { trackEvent } from '../providers/klaviyo.js';

export const webhookRouter = Router();

// SendGrid webhook signature verification
const SENDGRID_WEBHOOK_KEY = process.env.SENDGRID_WEBHOOK_KEY || '';

function verifySendgridSignature(payload, signature, timestamp) {
    if (!SENDGRID_WEBHOOK_KEY) return true; // Skip if not configured
    
    const signedPayload = timestamp + payload;
    const expectedSignature = crypto
        .createHmac('sha256', SENDGRID_WEBHOOK_KEY)
        .update(signedPayload)
        .digest('base64');
    
    return signature === expectedSignature;
}

/**
 * SendGrid Event Webhook
 * POST /api/webhooks/sendgrid
 */
webhookRouter.post('/sendgrid', async (req, res) => {
    try {
        const events = req.body;
        
        if (!Array.isArray(events)) {
            return res.status(400).json({ error: 'Expected array of events' });
        }

        logger.info('SendGrid webhook received', { eventCount: events.length });

        for (const event of events) {
            const { email, event: eventType, timestamp, sg_message_id, reason } = event;

            switch (eventType) {
                case 'delivered':
                    logger.info('Email delivered', { email, messageId: sg_message_id });
                    break;
                case 'open':
                    logger.info('Email opened', { email });
                    try {
                        await trackEvent(email, 'Email_Opened', { messageId: sg_message_id });
                    } catch (e) {}
                    break;
                case 'click':
                    logger.info('Email link clicked', { email, url: event.url });
                    try {
                        await trackEvent(email, 'Email_Link_Clicked', { 
                            messageId: sg_message_id, 
                            url: event.url 
                        });
                    } catch (e) {}
                    break;
                case 'bounce':
                    logger.warn('Email bounced', { email, reason });
                    // TODO: Mark email as invalid in database
                    break;
                case 'dropped':
                    logger.warn('Email dropped', { email, reason });
                    break;
                case 'spamreport':
                    logger.warn('Spam report received', { email });
                    // TODO: Unsubscribe user automatically
                    break;
                case 'unsubscribe':
                    logger.info('User unsubscribed', { email });
                    // TODO: Update subscription status
                    break;
            }
        }

        res.json({ received: true, processed: events.length });
    } catch (error) {
        logger.error('SendGrid webhook error', { error: error.message });
        res.status(500).json({ error: error.message });
    }
});

/**
 * Klaviyo Webhook
 * POST /api/webhooks/klaviyo
 */
webhookRouter.post('/klaviyo', async (req, res) => {
    try {
        const { type, data } = req.body;

        logger.info('Klaviyo webhook received', { type });

        switch (type) {
            case 'flow_message_sent':
                logger.info('Klaviyo flow message sent', { 
                    email: data?.profile?.email,
                    flowId: data?.flow_id 
                });
                break;
            case 'unsubscribed':
                logger.info('Klaviyo unsubscribe', { email: data?.profile?.email });
                // TODO: Sync unsubscribe to database
                break;
            case 'profile_updated':
                logger.info('Klaviyo profile updated', { email: data?.profile?.email });
                break;
        }

        res.json({ received: true });
    } catch (error) {
        logger.error('Klaviyo webhook error', { error: error.message });
        res.status(500).json({ error: error.message });
    }
});

/**
 * Zendesk Webhook (ticket updates)
 * POST /api/webhooks/zendesk
 */
webhookRouter.post('/zendesk', async (req, res) => {
    try {
        const { ticket, current_user } = req.body;

        if (!ticket) {
            return res.status(400).json({ error: 'No ticket data' });
        }

        logger.info('Zendesk webhook received', { 
            ticketId: ticket.id, 
            status: ticket.status,
            requesterEmail: ticket.requester?.email
        });

        // Notify user of ticket updates via Klaviyo
        if (ticket.requester?.email && ticket.status) {
            try {
                await trackEvent(ticket.requester.email, 'Support_Ticket_Updated', {
                    ticketId: ticket.id,
                    status: ticket.status,
                    updatedBy: current_user?.email || 'system'
                });
            } catch (e) {
                logger.warn('Klaviyo tracking failed', { error: e.message });
            }
        }

        res.json({ received: true, ticketId: ticket.id });
    } catch (error) {
        logger.error('Zendesk webhook error', { error: error.message });
        res.status(500).json({ error: error.message });
    }
});

/**
 * Generic inbound email webhook (for reply handling)
 * POST /api/webhooks/inbound
 */
webhookRouter.post('/inbound', async (req, res) => {
    try {
        const { from, to, subject, text, html, attachments } = req.body;

        logger.info('Inbound email received', { from, to, subject });

        // Parse token from email address if present (e.g., reply+TOKEN@careertrojan.com)
        const tokenMatch = to?.match(/reply\+([a-zA-Z0-9_-]+)@/);
        if (tokenMatch) {
            const token = tokenMatch[1];
            logger.info('Token reply detected', { token, from });
            // TODO: Route to appropriate handler based on token
        }

        // Auto-create Zendesk ticket for support emails
        if (to?.includes('support@')) {
            // TODO: Create Zendesk ticket from inbound email
            logger.info('Support email detected, ticket creation pending');
        }

        res.json({ received: true, from, subject });
    } catch (error) {
        logger.error('Inbound webhook error', { error: error.message });
        res.status(500).json({ error: error.message });
    }
});
