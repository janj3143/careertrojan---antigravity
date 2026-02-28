/**
 * Zendesk API Routes
 */

import { Router } from 'express';
import { 
    createTicket, 
    addTicketComment, 
    getTicket,
    searchTicketsByEmail,
    findOrCreateUser 
} from '../providers/zendesk.js';
import { validateRequest } from '../middleware/validate.js';
import Joi from 'joi';

export const zendeskRouter = Router();

// Validation schemas
const ticketSchema = Joi.object({
    requesterEmail: Joi.string().email().required(),
    requesterName: Joi.string(),
    subject: Joi.string().required(),
    body: Joi.string().required(),
    priority: Joi.string().valid('low', 'normal', 'high', 'urgent'),
    tags: Joi.array().items(Joi.string()),
    customFields: Joi.object()
});

const commentSchema = Joi.object({
    body: Joi.string().required(),
    public: Joi.boolean()
});

// Create support ticket
zendeskRouter.post('/tickets', validateRequest(ticketSchema), async (req, res) => {
    try {
        const result = await createTicket(req.body);
        res.status(201).json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get ticket by ID
zendeskRouter.get('/tickets/:ticketId', async (req, res) => {
    try {
        const ticket = await getTicket(req.params.ticketId);
        res.json({ ticket });
    } catch (error) {
        res.status(error.response?.status || 500).json({ error: error.message });
    }
});

// Add comment to ticket
zendeskRouter.post('/tickets/:ticketId/comment', validateRequest(commentSchema), async (req, res) => {
    try {
        const { body, public: isPublic } = req.body;
        const result = await addTicketComment(req.params.ticketId, body, isPublic !== false);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Search tickets by email
zendeskRouter.get('/search', async (req, res) => {
    try {
        const { email } = req.query;
        if (!email) {
            return res.status(400).json({ error: 'email query param required' });
        }
        const tickets = await searchTicketsByEmail(email);
        res.json({ tickets, count: tickets.length });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Find or create Zendesk user
zendeskRouter.post('/users', async (req, res) => {
    try {
        const { email, name } = req.body;
        if (!email) {
            return res.status(400).json({ error: 'email required' });
        }
        const user = await findOrCreateUser(email, name);
        res.json({ user });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});
