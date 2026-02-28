/**
 * Zendesk Integration Provider
 * 
 * Handles support ticket creation and email-to-ticket flows.
 */

import axios from 'axios';
import { logger } from '../utils/logger.js';

const ZENDESK_SUBDOMAIN = process.env.ZENDESK_SUBDOMAIN || '';
const ZENDESK_EMAIL = process.env.ZENDESK_EMAIL || '';
const ZENDESK_API_TOKEN = process.env.ZENDESK_API_TOKEN || '';

const zendeskApi = axios.create({
    baseURL: `https://${ZENDESK_SUBDOMAIN}.zendesk.com/api/v2`,
    auth: {
        username: `${ZENDESK_EMAIL}/token`,
        password: ZENDESK_API_TOKEN
    },
    headers: {
        'Content-Type': 'application/json'
    }
});

/**
 * Check Zendesk API connection
 */
export async function checkZendeskConnection() {
    if (!ZENDESK_SUBDOMAIN || !ZENDESK_API_TOKEN) {
        return { connected: false, error: 'No credentials configured' };
    }
    try {
        const response = await zendeskApi.get('/users/me.json');
        return { connected: true, user: response.data.user.email };
    } catch (error) {
        logger.error('Zendesk connection check failed', { error: error.message });
        return { connected: false, error: error.message };
    }
}

/**
 * Create a support ticket
 */
export async function createTicket({ 
    requesterEmail, 
    requesterName, 
    subject, 
    body, 
    priority = 'normal',
    tags = [],
    customFields = {}
}) {
    try {
        const response = await zendeskApi.post('/tickets.json', {
            ticket: {
                subject,
                comment: { body },
                priority,
                tags: ['careertrojan', ...tags],
                requester: {
                    name: requesterName || requesterEmail.split('@')[0],
                    email: requesterEmail
                },
                custom_fields: Object.entries(customFields).map(([id, value]) => ({
                    id: parseInt(id),
                    value
                }))
            }
        });

        logger.info('Zendesk ticket created', { 
            ticketId: response.data.ticket.id, 
            requesterEmail 
        });

        return {
            success: true,
            ticketId: response.data.ticket.id,
            ticketUrl: `https://${ZENDESK_SUBDOMAIN}.zendesk.com/agent/tickets/${response.data.ticket.id}`
        };
    } catch (error) {
        logger.error('Zendesk ticket creation failed', { error: error.message });
        throw error;
    }
}

/**
 * Add comment to existing ticket
 */
export async function addTicketComment(ticketId, body, isPublic = true) {
    try {
        const response = await zendeskApi.put(`/tickets/${ticketId}.json`, {
            ticket: {
                comment: {
                    body,
                    public: isPublic
                }
            }
        });

        logger.info('Zendesk comment added', { ticketId });
        return { success: true, ticketId };
    } catch (error) {
        logger.error('Zendesk add comment failed', { ticketId, error: error.message });
        throw error;
    }
}

/**
 * Get ticket by ID
 */
export async function getTicket(ticketId) {
    try {
        const response = await zendeskApi.get(`/tickets/${ticketId}.json`);
        return response.data.ticket;
    } catch (error) {
        logger.error('Zendesk get ticket failed', { ticketId, error: error.message });
        throw error;
    }
}

/**
 * Search tickets by user email
 */
export async function searchTicketsByEmail(email) {
    try {
        const response = await zendeskApi.get('/search.json', {
            params: {
                query: `type:ticket requester:${email}`
            }
        });
        return response.data.results;
    } catch (error) {
        logger.error('Zendesk search failed', { email, error: error.message });
        throw error;
    }
}

/**
 * Create or find user in Zendesk
 */
export async function findOrCreateUser(email, name) {
    try {
        // Search for existing user
        const searchResponse = await zendeskApi.get('/search.json', {
            params: { query: `type:user email:${email}` }
        });

        if (searchResponse.data.results.length > 0) {
            return searchResponse.data.results[0];
        }

        // Create new user
        const createResponse = await zendeskApi.post('/users.json', {
            user: {
                name: name || email.split('@')[0],
                email,
                verified: true
            }
        });

        logger.info('Zendesk user created', { email });
        return createResponse.data.user;
    } catch (error) {
        logger.error('Zendesk find/create user failed', { email, error: error.message });
        throw error;
    }
}

export default {
    checkZendeskConnection,
    createTicket,
    addTicketComment,
    getTicket,
    searchTicketsByEmail,
    findOrCreateUser
};
